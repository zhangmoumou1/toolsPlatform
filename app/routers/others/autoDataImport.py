import uuid
import json
from io import BytesIO
import pandas as pd
from fastapi import File, UploadFile
from pathlib import Path
from app.schema.audit_data_import import AuditDataRoolbackForm
from app.crud.AuditDataImport import AuditDataImport, ExcelToMysql
from app.middleware.AliyunOss import OssClient
from app.handler.fatcory import QmsResponse
from app.routers.others.dictionary import router
from app import init_logging
logger = init_logging()

@router.post("/audit/import", tags=["其他"], summary="云获钩稽数据导入")
async def audit_import(user: str, tool_id: int, env: int, channel: str, file: UploadFile = File(...)):
    file_name = file.filename
    file_content = await file.read()
    if '.xls' in file_name or '.xlsx' in file_name or '.csv' in file_name:
        result = await ExcelToMysql.async_operations(file_content)
        counts = result['count']
        # counts = await ExcelToMysql.insert_data_into_db(file_content)
    elif '.zip' in file_name:
        # counts = 0
        unique_id = user + str(uuid.uuid4())
        MEDIA_ROOT = "media/upload"
        extract_to = Path(MEDIA_ROOT) / unique_id  # 解压目标目录
        all_dfs = []  # 用来存放每个文件的 DataFrame

        for file_single in ExcelToMysql.handle_uploaded_zip(unique_id, extract_to, file):
            # 以二进制方式读取文件
            if isinstance(file_single, str):
                with open(file_single, "rb") as f:
                    excel_bytes = f.read()
            elif isinstance(file_single, bytes):
                excel_bytes = file_single
            else:
                raise ValueError("Invalid input: Expected file path (str) or binary content (bytes)")

            # 将文件读取为 DataFrame
            excel_io = BytesIO(excel_bytes)
            df = pd.read_excel(excel_io)
            df = df.where(pd.notnull(df), None)  # 处理空值
            all_dfs.append(df)  # 将每个 DataFrame 存入列表

        # 合并所有 DataFrame
        combined_df = pd.concat(all_dfs, ignore_index=True)

        # 将合并后的 DataFrame 传递给 async_operations
        # counts = await ExcelToMysql.async_operations_from_df(combined_df)
        result = await ExcelToMysql.insert_data_into_db(combined_df)
        counts = result['count']

        # 删除解压文件
        ExcelToMysql.delete_zip_file(extract_to)
    else:
        return QmsResponse.failed('Not a zip, csv, xls, or xlsx file！')

    # client = OssClient.get_oss_client()
    # oss上传 WARNING: 可能存在数据不同步的问题，oss成功本地失败
    # aliyun_url = await client.create_file(user, file_name, file_content)
    aliyun_url = 'http://www.baidu.com'
    await AuditDataImport.insert_import_record(user, tool_id, env, channel, aliyun_url, json.dumps(result))
    return QmsResponse.success({'url': aliyun_url}, msg=f'共执行{str(counts)}条')


# @router.post("/audit/import", tags=["其他"], summary="云获钩稽数据导入")
# async def audit_import(user: str, tool_id: int, env: int, channel: str, file: UploadFile = File(...)):
#     file_name = file.filename
#     file_content = await file.read()
#     if '.xls' in file_name or '.xlsx' in file_name or '.csv' in file_name:
#        counts = await ExcelToMysql.async_operations(file_content)
#     elif '.zip' in file_name:
#         counts = 0
#         unique_id = user + str(uuid.uuid4())
#         MEDIA_ROOT = "media/upload"
#         extract_to = Path(MEDIA_ROOT) / unique_id  # 解压目标目录
#         for file_single in ExcelToMysql.handle_uploaded_zip(unique_id, extract_to, file):
#             # 以二进制方式读取文件
#             if isinstance(file_single, str):
#                 with open(file_single, "rb") as f:
#                     excel_bytes = f.read()
#             elif isinstance(file_single, bytes):
#                 excel_bytes = file_single
#             else:
#                 raise ValueError("Invalid input: Expected file path (str) or binary content (bytes)")
#             count = await ExcelToMysql.async_operations(excel_bytes)
#             counts += count
#         # 删除解压文件
#         ExcelToMysql.delete_zip_file(extract_to)
#     else:
#         return QmsResponse.failed('Not a zip, csv, xls, or xlsx file！')
#     client = OssClient.get_oss_client()
#     # oss上传 WARNING: 可能存在数据不同步的问题，oss成功本地失败
#     aliyun_url = await client.create_file(user, file_name, file_content)
#     await AuditDataImport.insert_import_record(user, tool_id, env, channel, aliyun_url)
#     return QmsResponse.success({'url': aliyun_url}, msg=f'共执行{str(counts)}条')

@router.get("/audit/recordList", tags=["其他"], summary="云获钩稽数据导入记录")
async def list_audit_import(tool_id: int, user: str, env: int):
    data, total = await AuditDataImport.audit_import_list(tool_id, user, env)
    return QmsResponse.success_with_size(data=data, total=total)

@router.post("/audit/rollback", tags=["其他"], summary="云获钩稽数据导入回滚")
async def rollback_audit_import(data: AuditDataRoolbackForm):
    data = await AuditDataImport.rollback_import_record(data)
    if data:
        return QmsResponse.failed(msg=data)
    return QmsResponse.success()