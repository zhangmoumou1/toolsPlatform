from pydantic import BaseModel, validator
from app.schema.base import QmsModel

class AuditDataImportForm(BaseModel):
    """
    钩稽数据导入
    """
    tool_id: int
    user: str
    env: int
    channel: str

    @validator("tool_id", "user", "env", "channel")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)

class AuditDataRoolbackForm(BaseModel):
    """
    钩稽数据回滚
    """
    tool_id: int
    user: str
    record_id: int

    @validator("tool_id", "user", "record_id")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)