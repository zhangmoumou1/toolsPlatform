import aiomysql
from io import BytesIO
import os
import uuid
from pathlib import Path
import zipfile
import shutil
import json
from fastapi import UploadFile
from typing import Generator
from sqlalchemy import text, select, update, desc
import pandas as pd
from app.crud import ModelWrapper, Mapper
from app.schema.audit_data_import import AuditDataRoolbackForm
from app.models import async_session, business_async_session
from app.models.audit_data_model import AuditDataImportModel
from app.models.tools_info_model import ToolsInfoModel
from app import init_logging
logger = init_logging()

# 配置媒体文件根目录（根据你的项目结构调整）
TMP_ROOT = "media/tmp"

@ModelWrapper(AuditDataImportModel)
class AuditDataImport(Mapper):

    @staticmethod
    async def insert_import_record(user: str, tool_id: int, env: int, channel: str, aliyun_url: str, execution_log: str = None):
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
                    record = AuditDataImportModel(user=user, tool_id=tool_id, env=env, channel=channel, url=aliyun_url,
                                                  execution_log=execution_log, is_rollback=0)
                    session.add(record)
                    await session.execute(
                        update(ToolsInfoModel)
                        .where((ToolsInfoModel.id == tool_id) & (ToolsInfoModel.deleted_at == 0))
                        .values(total=ToolsInfoModel.total + 1)
                    )
        except Exception as e:
            logger.error(f"用户{user}, 新增导入钩稽数据记录失败, {e}")
            raise Exception(f"用户{user}, 新增导入钩稽数据记录失败, {e}")

    @staticmethod
    async def audit_import_list(tool_id: int, user: str, env: int):
        """
        钩稽数据导入记录
        :param tool_id:
        :param user:
        :return:
        """
        try:
            search = [AuditDataImportModel.deleted_at == 0, AuditDataImportModel.tool_id == tool_id]
            async with async_session() as session:
                if user:
                    search.append(AuditDataImportModel.create_user == user)
                if env:
                    search.append(AuditDataImportModel.env == env)
                query = await session.execute(
                    select(AuditDataImportModel.env, AuditDataImportModel.channel, AuditDataImportModel.url,
                           AuditDataImportModel.is_rollback,AuditDataImportModel.create_user,
                           AuditDataImportModel.created_at).where(*search).order_by(desc(AuditDataImportModel.created_at))
                )
                total = query.raw.rowcount
                result = query.all()
                return result, total
        except Exception as e:
            logger.error(f"查询钩稽导入记录失败, {e}")
            raise Exception(f"查询钩稽导入记录失败, {e}")

    @staticmethod
    async def rollback_import_record(data: AuditDataRoolbackForm):
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
                        select(AuditDataImportModel.create_user, AuditDataImportModel.execution_log)
                        .where(*search).order_by(desc(AuditDataImportModel.created_at)))
                    db_user, db_log = query.first()
                    logger.error(db_log)
                    if data.user != db_user:
                        return f"非当前记录用户，无法回滚！"
            # 执行回滚数据
            async with business_async_session('v1', 'etl') as bs_session:
                execution_log = json.loads(db_log)
                first_inserted_id = execution_log['first_inserted_id']
                last_inserted_id = execution_log['last_inserted_id']
                logger.warning(last_inserted_id)
                await bs_session.execute(text(
                    f"delete from yunhuo_clea_data where id between {first_inserted_id} and {last_inserted_id}"))
                await bs_session.commit()
            # 修改记录回滚状态
            async with async_session() as session:
                async with session.begin():
                    search = [AuditDataImportModel.deleted_at == 0, AuditDataImportModel.tool_id == data.tool_id,
                              AuditDataImportModel.id == data.record_id]
                    await session.execute(
                        update(AuditDataImportModel)
                        .where(*search)
                        .values(is_rollback=True)
                    )
        except Exception as e:
            logger.error(f"用户{data.user}, 钩稽数据导入回滚失败, {e}")
            raise Exception(f"用户{data.user}, 钩稽数据导入回滚失败, {e}")


class ExcelToMysql():
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

    @staticmethod
    async def async_operations(excel_file):
        """
        pandas解析数据
        :param excel_file:
        :return:
        """
        try:
            # 读取Excel文件（同步部分）
            excel_io = BytesIO(excel_file)
            excel_io.seek(0)
            df = pd.read_excel(excel_io)
            df = df.where(pd.notnull(df), None)
            # 确保 df 是 DataFrame
            if not isinstance(df, pd.DataFrame):
                logger.error(f"read_excel() returned unexpected type: {type(df)}")
                raise ValueError("Excel file parsing failed, returned non-DataFrame object")

            # 检查 DataFrame 是否为空
            if df.empty:
                logger.warning("Excel file parsed but DataFrame is empty!")
            # 异步执行初始化连接池、插入数据和关闭连接池的操作
            import time
            now = time.time()
            count = await ExcelToMysql.insert_data_into_db(df)
            logger.error(f'22222---{time.time() - now}')
            return count
        except Exception as e:
            logger.error(f"An error occurred during async operations: {e}")
            raise

    @staticmethod
    async def insert_data_into_db(df):
        """
        数据导入云获表
        """
        try:
            async with business_async_session('v1', 'etl') as conn:
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
            print(f"Database error occurred: {e}")
            if 'conn' in locals() and conn is not None:
                await conn.rollback()
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
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

    @staticmethod
    def delete_zip_file(extract_to):
        """
        删除zip解压文件夹
        :return:
        """
        try:
            extract_path = Path(extract_to)
            if extract_path.exists() and extract_path.is_dir():
                shutil.rmtree(extract_path)
                logger.info(f"已删除文件夹: {extract_path}")
            else:
                logger.warning(f"文件夹不存在: {extract_path}")
        except Exception as e:
            logger.error(f"删除文件夹失败: {e}")
            raise

