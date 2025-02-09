from sqlalchemy import select
from app.crud import Mapper
from app.models import async_session
from app.models.tools_info_model import ToolsInfoModel
from app import init_logging
logger = init_logging()

class ToolsInfo(Mapper):

    @staticmethod
    async def tools_list(title: str, type: int):
        try:
            search = [ToolsInfoModel.deleted_at == 0]
            async with async_session() as session:
                if title:
                    search.append(ToolsInfoModel.title.like(f"%{title}%"))
                if type:
                    search.append(ToolsInfoModel.type == type)
                query = await session.execute(
                    select(ToolsInfoModel.id, ToolsInfoModel.title, ToolsInfoModel.description, ToolsInfoModel.total,
                           ToolsInfoModel.manual, ToolsInfoModel.create_user, ToolsInfoModel.created_at).where(*search)
                )
                total = query.raw.rowcount
                result = query.all()
                return result, total
        except Exception as e:
            logger.error(f"查询工具失败, {e}")
            raise Exception(f"查询工具失败, {e}")
