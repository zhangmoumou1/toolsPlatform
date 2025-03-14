from sqlalchemy import select
from app.crud import Mapper
from app.models import async_session
from app.models.tools_info_model import ToolsInfoModel, FeedBackModel
from app.models.dictionary_model import DictionaryModel
from app.schema.base import ToolListForm, ToolDetailForm

class ToolsInfo(Mapper):

    @classmethod
    async def tools_list(cls, data: ToolListForm):
        try:
            search = [ToolsInfoModel.deleted_at == 0]
            async with async_session() as session:
                if data.param.title:
                    search.append(ToolsInfoModel.title.like(f"%{data.param.title}%"))
                if data.param.type:
                    search.append(ToolsInfoModel.type == data.param.type)
                sql = select(ToolsInfoModel.id, ToolsInfoModel.title,ToolsInfoModel.type,
                        DictionaryModel.enum_name.label("type_desc"), ToolsInfoModel.description,
                        ToolsInfoModel.total, ToolsInfoModel.manual, ToolsInfoModel.create_user,
                        ToolsInfoModel.created_at
                     ).outerjoin(
                        DictionaryModel, (DictionaryModel.dict_code == 2025001) & (DictionaryModel.enum_id == ToolsInfoModel.type)
                ).where(*search)
                query = await session.execute(sql)
                total = query.raw.rowcount
                if total == 0:
                    return [], 0
                sql = sql.offset((data.pageNum - 1) * data.pageSize).limit(data.pageSize)
                result = await session.execute(sql)
                return result.all(), total
        except Exception as e:
            cls.__log__.error(f"查询工具失败, {e}")
            raise Exception(f"查询工具失败, {e}")

    @classmethod
    async def tools_detail(cls, data: ToolDetailForm):
        """
        工具详情
        :param tool_id:
        :return:
        """
        try:
            # if data.id == "1":
                # 钩稽数据导入功能
            try:
                search = [ToolsInfoModel.deleted_at == 0, ToolsInfoModel.id == data.id]
                async with async_session() as session:
                    query = await session.execute(
                        select(ToolsInfoModel.id, ToolsInfoModel.title, ToolsInfoModel.manual, ToolsInfoModel.description).where(*search))
                    return query.first()
            except Exception as e:
                cls.__log__.error(f"查询工具失败, {e}")
                raise Exception(f"查询工具失败, {e}")

            # else:
            #     raise Exception("id不存在")
        except Exception as e:
            cls.__log__.error(f"查询工具详情失败, {e}")
            raise Exception(f"查询工具详情失败, {e}")

    @classmethod
    async def feedback(cls, user: str, title: str, description: str, url: [] = None):
        """
        意见反馈
        :param data:
        :return:
        """
        try:
            async with async_session() as session:
                async with session.begin():
                    session.add(FeedBackModel(user=user, title=title, description=description, url=url))
        except Exception as e:
            cls.__log__.error(f"意见反馈失败, {e}")
            raise Exception(f"意见反馈失败, {e}")
