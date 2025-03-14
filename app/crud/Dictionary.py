import logging
from typing import List
from sqlalchemy import select, desc, orm
from app.crud import Mapper
from app.models import async_session
from app.models.dictionary_model import DictionaryModel
from app.schema.dictionary import DictionaryForm
from app import init_logging
logger = init_logging()

class Dictionary(Mapper):

    @classmethod
    async def insert_dictionary(cls, data: DictionaryForm):
        try:
            async with async_session() as session:
                async with session.begin():
                    for enums in data.enum:
                        result = await session.execute(
                            select(DictionaryModel).where(DictionaryModel.dict_code == data.dict_code,
                                                          DictionaryModel.enum_id == enums.enum_id,
                                                          DictionaryModel.deleted_at == 0))
                        query = result.scalars().first()
                        if query is not None:
                            raise Exception(f"enum_id={enums.enum_id}已存在")
                        session.add(DictionaryModel(user=data.user, dict_code=data.dict_code, dict_name=data.dict_name,
                                                    enum_id=enums.enum_id, enum_name=enums.enum_name))
        except Exception as e:
            cls.__log__.error(f"新增字典枚举失败, {e}")
            raise Exception(f"新增字典枚举失败, {e}")

    # @classmethod
    # async def dictionary_list(cls, dict_code: int, enum_id:None):
    #     try:
    #         search = [DictionaryModel.deleted_at == 0]
    #         async with async_session() as session:
    #             if dict_code:
    #                 search.append(DictionaryModel.dict_code == dict_code)
    #             if enum_id is not None:
    #                 search.append(DictionaryModel.enum_id == enum_id)
    #             query = await session.execute(
    #                 select(DictionaryModel.enum_id, DictionaryModel.enum_name).where(*search)
    #             )
    #             total = query.raw.rowcount
    #             if total == 1:
    #                 result = query.all()[0][ DictionaryModel.enum_name ]
    #             else:
    #                 result = query.all()
    #             cls.__log__.info(f"查询字典枚举成功, {str(result)}")
    #             return result, total
    #     except Exception as e:
    #         cls.__log__.error(f"查询字典枚举失败, {str(e)}")
    #         raise Exception(f"查询字典枚举失败, {e}")

    @classmethod
    async def delete_dictionary(cls, data: DictionaryForm):
        try:
            search = [DictionaryModel.deleted_at == 0]
            async with async_session() as session:
                async with session.begin():
                    if data.dict_code:
                        search.append(DictionaryModel.dict_code == data.dict_code)
                    query = await session.execute(
                        select(DictionaryModel).where(*search)
                    )
                    results = query.scalars().all()
                    logging.error(results)
                    if results == []:
                        raise Exception("字典不存在")
                    [setattr(result, 'deleted_at', 1) or setattr(result, 'update_user', data.user) for result in
                     results]
        except Exception as e:
            cls.__log__.error(f"删除字典枚举失败, {str(e)}")
            raise Exception(f"删除字典枚举失败, {e}")

