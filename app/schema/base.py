from app.excpetions.ParamsException import ParamsError
from pydantic import BaseModel, validator, root_validator
from typing import Optional, Any, Dict

class QmsModel(object):

    @staticmethod
    def not_empty(v):
        if isinstance(v, str) and len(v.strip()) == 0:
            raise ParamsError("不能为空")
        if not isinstance(v, int):
            if not v:
                raise ParamsError("不能为空")
        return v

    @property
    def parameters(self):
        raise NotImplementedError

class ToolDetailForm(BaseModel):
    """
    工具详情
    """
    id: str

    @validator("id")
    def name_not_empty(cls, v):
        return QmsModel.not_empty(v)

class ToolListParams(BaseModel):
    title: str
    type: str

class ToolListForm(BaseModel):
    """
    钩稽数据执行记录列表
    """
    param: ToolListParams
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
            values['param'] = ToolListParams(**param_dict)

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