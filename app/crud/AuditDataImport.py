import aiomysql
import os
import zipfile
import shutil
import json
import uuid
from pathlib import Path
from pandas import read_excel
from python_calamine.pandas import pandas_monkeypatch
from io import BytesIO
from fastapi import UploadFile
from typing import Generator
from sqlalchemy import text, select, update, desc
from sqlalchemy.orm import aliased
import pandas as pd
from app.crud import ModelWrapper, Mapper
from app.schema.audit_data_import import AuditDataRoolbackForm, AuditDataImportForm, AuditDataRecordListForm
from app.models import async_session, business_async_session
from app.models.audit_data_model import AuditDataImportModel
from app.models.tools_info_model import ToolsInfoModel
from app.models.dictionary_model import DictionaryModel
from app.crud import QueryDictionary, CheckDictionary, QueryDictionaryEnums
from app import init_logging
logger = init_logging()

# 配置媒体文件根目录（根据你的项目结构调整）
TMP_ROOT = "media/tmp"

@ModelWrapper(AuditDataImportModel)
class AuditDataImport(Mapper):

    @classmethod
    async def insert_import_record(cls, data: AuditDataImportForm, execution_log: str = None, execution_result:str = None):
        """
        钩稽数据导入
        :param user:
        :param tool_id:
        :param env:
        :param channel:
        :param aliyun_url:
        :return:
        """
        try:
            async with async_session() as session:
                async with session.begin():
                    await CheckDictionary(dict_code=2025002, enum_id=data.channel)
                    record = AuditDataImportModel(user=data.user, tool_id=data.tool_id, env=data.env, channel=data.channel, files=data.files,
                                                  execution_log=execution_log, is_rollback=0, execution_result=execution_result)
                    session.add(record)
                    await session.execute(
                        update(ToolsInfoModel)
                        .where((ToolsInfoModel.id == data.tool_id) & (ToolsInfoModel.deleted_at == 0))
                        .values(total=ToolsInfoModel.total + 1)
                    )
        except Exception as e:
            # 如果执行了业务，但是记录保存出错，需要回滚
            if execution_log:
                env_enum_name = (await QueryDictionaryEnums(dict_code=2025000, enum_id=data.env))[0]['enums'][0]['enum_name']
                async with business_async_session(env_enum_name, 'etl') as bs_session:
                    execution_log = json.loads(execution_log)
                    first_inserted_id = execution_log['first_inserted_id']
                    last_inserted_id = execution_log['last_inserted_id']
                    await bs_session.execute(text(
                        f"delete from yunhuo_clea_data where id between {first_inserted_id} and {last_inserted_id}"))
                    await bs_session.commit()
            cls.__log__.error(f"新增导入钩稽数据记录失败, {e}")
            raise Exception(f"新增导入钩稽数据记录失败, {e}")

    @classmethod
    async def audit_import_list(cls, data:AuditDataRecordListForm):
        """
        钩稽数据导入记录
        :param tool_id:
        :param user:
        :return:
        """
        try:
            search = [AuditDataImportModel.deleted_at == 0, AuditDataImportModel.tool_id == data.param.tool_id]
            async with async_session() as session:
                if data.param.user:
                    search.append(AuditDataImportModel.create_user == data.param.user)
                if data.param.env:
                    search.append(AuditDataImportModel.env == data.param.env)
                # 使用 aliased 创建字典表的两个别名
                dict_env = aliased(DictionaryModel)
                dict_channel = aliased(DictionaryModel)
                sql = select(AuditDataImportModel.id, AuditDataImportModel.env, dict_env.enum_name.label("env_desc"),
                            AuditDataImportModel.channel, dict_channel.enum_name.label("channel_desc"),
                             AuditDataImportModel.execution_result, AuditDataImportModel.files,
                             AuditDataImportModel.is_rollback, AuditDataImportModel.create_user,
                             AuditDataImportModel.created_at
                        ).outerjoin(
                            dict_env, ((dict_env.dict_code == 2025000) & (dict_env.enum_id == AuditDataImportModel.env))
                        ).outerjoin(
                            dict_channel, ((dict_channel.dict_code == 2025002) & (dict_channel.enum_id == AuditDataImportModel.channel))
                        ).where(
                            *search
                        ).order_by(
                            desc(AuditDataImportModel.created_at)
                        )
                query = await session.execute(sql)
                total = query.raw.rowcount
                if total == 0:
                    return [], 0
                sql = sql.offset((data.pageNum - 1) * data.pageSize).limit(data.pageSize)
                data = await session.execute(sql)
                return data.all(), total
        except Exception as e:
            cls.__log__.info(f"查询钩稽导入记录失败, {e}")
            raise Exception(f"查询钩稽导入记录失败, {e}")

    @classmethod
    async def rollback_import_record(cls, data: AuditDataRoolbackForm):
        """
        导入记录回滚
        :param user:
        :param tool_id:
        :param record_id:
        :return:
        """
        try:
            async with async_session() as session:
                async with session.begin():
                    search = [AuditDataImportModel.deleted_at == 0, AuditDataImportModel.tool_id == data.tool_id,
                              AuditDataImportModel.id == data.record_id]
                    query = await session.execute(
                        select(AuditDataImportModel.create_user, AuditDataImportModel.execution_log, AuditDataImportModel.env)
                        .where(*search).order_by(desc(AuditDataImportModel.created_at)))
                    db_user, db_log, env = query.first()
                    if data.user != db_user:
                        return f"非当前记录用户，无法回滚！"
            result = (await QueryDictionaryEnums(dict_code=2025000, enum_id=env))[0]['enums'][0]['enum_name']
            # 执行回滚数据
            async with business_async_session(result, 'etl') as bs_session:
                execution_log = json.loads(db_log)
                first_inserted_id = execution_log['first_inserted_id']
                last_inserted_id = execution_log['last_inserted_id']
                await bs_session.execute(text(
                    f"delete from yunhuo_clea_data where id between {first_inserted_id} and {last_inserted_id}"))
                await bs_session.commit()
            # 修改记录回滚状态
            async with async_session() as session:
                async with session.begin():
                    search = [AuditDataImportModel.deleted_at == 0, AuditDataImportModel.tool_id == data.tool_id,
                              AuditDataImportModel.id == data.record_id, AuditDataImportModel.create_user == data.user]
                    await session.execute(
                        update(AuditDataImportModel)
                        .where(*search)
                        .values(is_rollback=True)
                    )
        except Exception as e:
            cls.__log__.error(f"钩稽数据导入回滚失败, {e}")
            raise Exception(f"钩稽数据导入回滚失败, {e}")

class ExcelToMysql(Mapper):
    # @staticmethod
    # async def async_operations_from_df(df):
    #     """
    #     pandas解析数据并执行数据库操作
    #     :param df: 合并后的 DataFrame
    #     :return:
    #     """
    #     try:
    #         if df.empty:
    #             logger.warning("DataFrame is empty!")
    #             return 0
    #
    #         # 异步执行初始化连接池、插入数据和关闭连接池的操作
    #         count = await ExcelToMysql.insert_data_into_db(df)
    #         return count
    #     except Exception as e:
    #         logger.error(f"An error occurred during async operations: {e}")
    #         raise

    @classmethod
    async def async_operations(cls, excel_file, env):
        """
        pandas解析数据
        :param excel_file:
        :return:
        """
        try:
            pandas_monkeypatch()
            # 读取Excel文件（同步部分）
            excel_io = BytesIO(excel_file)
            excel_io.seek(0)
            df = pd.read_excel(excel_io, engine="calamine")
            df = df.where(pd.notnull(df), None)
            # 确保 df 是 DataFrame
            if not isinstance(df, pd.DataFrame):
                cls.__log__.error(f"read_excel() returned unexpected type: {type(df)}")
                raise ValueError("Excel file parsing failed, returned non-DataFrame object")

            # 检查 DataFrame 是否为空
            if df.empty:
                cls.__log__.warning("Excel file parsed but DataFrame is empty!")
            # 异步执行初始化连接池、插入数据和关闭连接池的操作
            count = await ExcelToMysql.insert_data_into_db(df, env)
            return count
        except Exception as e:
            cls.__log__.error(f"An error occurred during async operations: {e}")
            raise

    @classmethod
    async def insert_data_into_db(cls, df, env):
        """
        数据导入云获表
        """
        try:
            data = (await QueryDictionaryEnums(dict_code=2025000, enum_id=env))[0]['enums'][0]['enum_name']
            async with business_async_session(data, 'etl') as conn:
                # 查询当前表的最大ID
                result = await conn.execute(text("SELECT MAX(id) FROM yunhuo_clea_data"))
                max_id_result = result.scalar()  # 获取最大ID
                first_inserted_id = max_id_result if max_id_result is not None else 1
                sql = text("""
                    INSERT INTO yunhuo_clea_data (user_name, cash, order_time, bank_deal_time, order_no, lx_order_no, batch_no,
                    receive_id_card, receive_card_no, receive_bank, receive_service_fee, receive_service_main, service_main,
                    payment_remark, bank_flow, trade_channel, order_update_time, order_status, status_desc)
                    VALUES (:user_name, :cash, :order_time, :bank_deal_time, :order_no, :lx_order_no, :batch_no,
                    :receive_id_card, :receive_card_no, :receive_bank, :receive_service_fee, :receive_service_main, :service_main,
                    :payment_remark, :bank_flow, :trade_channel, :order_update_time, :order_status, :status_desc)
                """)

                header = ['收款户名', '商家打款金额（元）', '订单创建时间', '银行受理时间', '订单号', '商家订单号',
                          '批次号', '收款证件号', '收款卡号', '收款银行', '实收服务费（元）', '抵扣服务费（元）',
                          '服务主体', '打款备注', '银行流水号', '交易渠道', '订单更新时间', '订单状态', '状态说明']

                # **2. 确保金额和批次号是字符串**
                df['商家打款金额（元）'] = df['商家打款金额（元）'].astype(str)
                df['实收服务费（元）'] = df['实收服务费（元）'].astype(str)
                df['抵扣服务费（元）'] = df['抵扣服务费（元）'].astype(str)
                df['批次号'] = df['批次号'].astype(str)
                # **5. 生成字典格式的数据**
                data_dicts = df.rename(columns=dict(zip(header, [
                    "user_name", "cash", "order_time", "bank_deal_time", "order_no", "lx_order_no", "batch_no",
                    "receive_id_card", "receive_card_no", "receive_bank", "receive_service_fee", "receive_service_main",
                    "service_main",
                    "payment_remark", "bank_flow", "trade_channel", "order_update_time", "order_status", "status_desc"
                ]))).to_dict(orient='records')

                # **6. 执行批量插入**
                result = await conn.execute(sql, data_dicts)
                await conn.commit()
                # 查询当前表的最大ID
                result = await conn.execute(text("SELECT MAX(id) FROM yunhuo_clea_data"))
                max_id_result = result.scalar()  # 获取最大ID
                last_inserted_id = max_id_result if max_id_result is not None else 1

        except aiomysql.Error as e:
            cls.__log__.error(f"Database error occurred: {e}")
            if 'conn' in locals() and conn is not None:
                await conn.rollback()
        except Exception as e:
            cls.__log__.error(f"An unexpected error occurred: {e}")
            if 'conn' in locals() and conn is not None:
                await conn.rollback()
        finally:
            return {'first_inserted_id': first_inserted_id + 1, 'last_inserted_id': last_inserted_id, 'count': len(data_dicts)}
            # return len(data_dicts) if 'data_dicts' in locals() else 0

    @staticmethod
    def handle_uploaded_zip(unique_id, extract_to, zip_file: UploadFile) -> Generator[str, None, None]:
        """
        解压zip
        :param unique_id:
        :param extract_to:
        :param zip_file:
        :return:
        """
        temp_zip_dir = Path(TMP_ROOT) / unique_id
        temp_zip_path = temp_zip_dir / zip_file.filename
        temp_zip_dir.mkdir(parents=True, exist_ok=True)
        try:
            with temp_zip_path.open("wb") as buffer:
                zip_file.file.seek(0)
                shutil.copyfileobj(zip_file.file, buffer)

            extract_to.mkdir(parents=True, exist_ok=True)

            # 解压 ZIP
            with zipfile.ZipFile(temp_zip_path, "r") as zip_ref:
                zip_ref.extractall(extract_to)

            # 移动所有文件到根目录
            for file_path in extract_to.rglob("*"):  # 递归查找所有文件
                if file_path.is_file():
                    new_path = extract_to / file_path.name

                    # 处理文件名冲突
                    if new_path.exists():
                        new_path = extract_to / f"{file_path.stem}_{uuid.uuid4()}{file_path.suffix}"

                    shutil.move(str(file_path), str(new_path))
                    yield str(new_path)

            # 删除空文件夹
            for dir_path in sorted(extract_to.glob("**/*"), key=lambda p: -len(p.parts)):
                if dir_path.is_dir() and not any(dir_path.iterdir()):
                    dir_path.rmdir()

        finally:
            # 清理临时 ZIP 文件
            if temp_zip_path.exists():
                temp_zip_path.unlink()
            if temp_zip_dir.exists():
                try:
                    temp_zip_dir.rmdir()
                except OSError:
                    pass

    @classmethod
    def delete_zip_file(cls, extract_to):
        """
        删除zip解压文件夹
        :return:
        """
        try:
            extract_path = Path(extract_to)
            if extract_path.exists() and extract_path.is_dir():
                shutil.rmtree(extract_path)
                cls.__log__.info(f"已删除文件夹: {extract_path}")
            else:
                cls.__log__.warning(f"文件夹不存在: {extract_path}")
        except Exception as e:
            cls.__log__.error(f"删除文件夹失败: {e}")
            raise

