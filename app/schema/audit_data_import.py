from pydantic import BaseModel, validator, root_validator
from app.schema.base import QmsModel
from typing import Optional, Any, Dict

class AuditDataImportForm(BaseModel):
    """
    钩稽数据导入
    """
    tool_id: int
    user: str
    env: int
    channel: int
    files: list

    @validator("tool_id", "user", "env", "channel", "files")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)

class AuditDataRoolbackForm(BaseModel):
    """
    钩稽数据回滚
    """
    tool_id: int
    record_id: int
    user: str

    @validator("tool_id", "user", "record_id")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)

class AuditRecordListParams(BaseModel):
    tool_id: Optional[str] = None
    user: Optional[str] = None
    env: Optional[str] = None

class AuditDataRecordListForm(BaseModel):
    """
    钩稽数据执行记录列表
    """
    param: AuditRecordListParams
    pageNum: int
    pageSize: int

    @root_validator(pre=True)
    def convert_and_default_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        values['pageNum'] = cls.convert_to_int_or_default(values.get('pageNum', None), default=1)
        values['pageSize'] = cls.convert_to_int_or_default(values.get('pageSize', None), default=1000)

        # 处理 param 字段的嵌套数据转换
        if 'param' in values:
            param_dict = values['param']
            if param_dict.get('user') and isinstance(param_dict['user'], str) and param_dict['user'].strip() == '':
                param_dict['user'] = None
            values['param'] = AuditRecordListParams(**param_dict)

        return values

    @staticmethod
    def convert_to_int_or_default(value: Any, default: int) -> int:
        """ 将值转换为整数，若为空则返回默认值 """
        if value is None:
            return default
        try:
            return int(value)
        except (ValueError, TypeError):
            return default