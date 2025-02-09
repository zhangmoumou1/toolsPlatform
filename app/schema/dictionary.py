from typing import List
from pydantic import BaseModel, validator
from app.schema.base import QmsModel

class EnumForm(BaseModel):
    enum_id: int
    enum_name: str

    @validator("enum_id", "enum_name")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)

class DictionaryForm(BaseModel):
    """
    枚举字典
    """
    user: str
    dict_code: int
    dict_name: str = None
    enum: List[EnumForm] = None

    @validator("user", "dict_code")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)