import json
from app.schema.audit_data_import import AuditDataRoolbackForm, AuditDataImportForm, AuditDataRecordListForm
from app.crud.AuditDataImport import AuditDataImport, ExcelToMysql
from app.middleware.AliyunOss import OssClient
from app.handler.fatcory import QmsResponse
from app.middleware.FileFormat import checkFileFormat
from urllib.parse import urlparse, unquote
from fastapi import APIRouter
from app.crud import Mapper
from app import init_logging
logger = init_logging()

router = APIRouter(prefix="/others")

@router.post("/audit/import", tags=["其他"], summary="云获钩稽数据导入")
async def audit_import(data: AuditDataImportForm):
    try:
        if len(data.files) == 0:
            return QmsResponse.failed(f'请上传文件！')
        results = {
            'first_inserted_id': 0,
            'last_inserted_id': 0,
            'count': 0
        }
        for file in data.files:
            url = file['url']
            if checkFileFormat(url, 'xlsx') is True:
                client = OssClient.get_oss_client()
                parsed_url = urlparse(url)
                file_path = parsed_url.path.lstrip('/')  # 获取路径并去掉前导的 '/'
                decoded_file_path =unquote(file_path)
                # 使用 get_file_object 获取文件内容
                file_content = await client.get_file_object(decoded_file_path)
                result = await ExcelToMysql.async_operations(file_content, data.env)
                results['first_inserted_id'] = result.get('first_inserted_id', 0)
                results['last_inserted_id'] = result.get('last_inserted_id', 0)
                results['count'] += result.get('count', 0)
                # aliyun_url = 'http://www.baidu.com'
        execution_result = f'共执行{str(results["count"])}条'
        await AuditDataImport.insert_import_record(data, json.dumps(results), execution_result)
        return QmsResponse.success(msg=execution_result)
    except Exception as e:
        return QmsResponse.failed(msg=f'执行失败，文件内容不正确，请查看工具说明，{e}')

@router.post("/audit/recordList", tags=["其他"], summary="云获钩稽数据导入记录")
async def list_audit_import(data: AuditDataRecordListForm):
    data, total = await AuditDataImport.audit_import_list(data)
    return QmsResponse.success_with_size(data=data, total=total)

@router.post("/audit/rollback", tags=["其他"], summary="云获钩稽数据导入回滚")
async def rollback_audit_import(data: AuditDataRoolbackForm):
    data = await AuditDataImport.rollback_import_record(data)
    if data:
        return QmsResponse.failed(msg=data)
    return QmsResponse.success()