import datetime
import calendar
import enum
import json
import logging
from typing import List
from sqlalchemy import select, desc, orm
from app.crud import ModelWrapper, Mapper
from app.models import async_session
from app.models.dictionary_model import DictionaryModel
from app.schema.dictionary import DictionaryForm
from app import init_logging
logger = init_logging()

class Dictionary(Mapper):

    @staticmethod
    async def insert_dictionary(data: DictionaryForm):
        try:
            async with async_session() as session:
                async with session.begin():
                    logger.info(data)
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
            logger.error(f"新增字典枚举失败, {e}")
            raise Exception(f"新增字典枚举失败, {e}")

    @staticmethod
    async def dictionary_list(dict_code: int):
        try:
            search = [DictionaryModel.deleted_at == 0]
            async with async_session() as session:
                if dict_code:
                    search.append(DictionaryModel.dict_code == dict_code)
                query = await session.execute(
                    select(DictionaryModel.enum_id, DictionaryModel.enum_name).where(*search)
                )
                total = query.raw.rowcount
                result = query.all()
                return result, total
        except Exception as e:
            logger.error(f"查询字典枚举失败, {e}")
            raise Exception(f"查询字典枚举失败, {e}")

    @staticmethod
    async def delete_dictionary(data: DictionaryForm):
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
                    [setattr(result, 'deleted_at', 1) or setattr(result, 'update_user', data.user) for result in results]
        except Exception as e:
            logger.error(f"查询字典枚举失败, {e}")
            raise Exception(f"查询字典枚举失败, {e}")