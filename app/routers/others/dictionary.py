from app.schema.dictionary import DictionaryForm
from app.crud.Dictionary import Dictionary
from app.crud.ToolsInfo import ToolsInfo
from app.handler.fatcory import QmsResponse
from fastapi import APIRouter
from app import init_logging
logger = init_logging()

router = APIRouter(prefix="/qms/others")

@router.post("/dictionaryAdd", tags=["其他"], summary="新增字典")
async def insert_dictionary(data: DictionaryForm):
    await Dictionary.insert_dictionary(data)
    return QmsResponse.success()

@router.get("/dictionaryList", tags=["其他"], summary="查询字典")
async def list_dictionary(dict_code: int = None):
    data, total = await Dictionary.dictionary_list(dict_code)
    return QmsResponse.success_with_size(data=data, total=total)

@router.post("/dictionaryDelete", tags=["其他"], summary="删除字典")
async def delete_dictionary(data: DictionaryForm):
    await Dictionary.delete_dictionary(data)
    return QmsResponse.success()

@router.get("/toolList", tags=["其他"], summary="查询工具信息")
async def list_tool(title: str = None, type: int = None):
    data, total = await ToolsInfo.tools_list(title, type)
    return QmsResponse.success_with_size(data=data, total=total)