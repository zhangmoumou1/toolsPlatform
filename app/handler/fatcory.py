import os
from datetime import datetime
from decimal import Decimal
from typing import Any
from fastapi import Query
from typing import Optional
from starlette.background import BackgroundTask
from starlette.responses import FileResponse
from app.handler.encoder import jsonable_encoder
from functools import wraps

class QmsResponse(object):
    """
    响应处理
    """
    @staticmethod
    def model_to_dict(obj, *ignore: str):
        if getattr(obj, '__table__', None) is None:
            return obj
        data = dict()
        for c in obj.__table__.columns:
            if c.name in ignore:
                # 如果字段忽略, 则不进行转换
                continue
            val = getattr(obj, c.name)
            if isinstance(val, datetime):
                data[c.name] = val.strftime("%Y-%m-%d %H:%M:%S")
            else:
                data[c.name] = val
        return data

    @staticmethod
    def dict_model_to_dict(obj):
        for k, v in obj.items():
            if isinstance(v, dict):
                QmsResponse.dict_model_to_dict(v)
            elif isinstance(v, list):
                obj[k] = QmsResponse.model_to_list(v)
            else:
                obj[k] = QmsResponse.model_to_dict(v)
        return obj

    @staticmethod
    def json_serialize(obj):
        ans = dict()
        for k, o in dict(obj).items():
            if isinstance(o, set):
                ans[k] = list(o)
            elif isinstance(o, datetime):
                ans[k] = o.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(o, Decimal):
                ans[k] = str(o)
            elif isinstance(o, bytes):
                ans[k] = o.decode(encoding='utf-8')
            else:
                ans[k] = o
        return ans

    @staticmethod
    def parse_sql_result(data: list):
        columns = []
        if len(data) > 0:
            columns = list(data[0].keys())
        return columns, [QmsResponse.json_serialize(obj) for obj in data]

    @staticmethod
    def model_to_list(data: list, *ignore: str):
        return [QmsResponse.model_to_dict(x, *ignore) for x in data]

    @staticmethod
    def encode_json(data: Any, *exclude: str):
        return jsonable_encoder(data, exclude=exclude, custom_encoder={
            datetime: lambda x: x.strftime("%Y-%m-%d %H:%M:%S")
        })

    @staticmethod
    def success(data=None, code=10000, msg="Success", exclude=()):
        return QmsResponse.encode_json(dict(code=code, msg=msg, data=data, suceess=True), *exclude)

    @staticmethod
    def records(data: list, code=10000, msg="Success"):
        return dict(code=code, msg=msg, data=QmsResponse.model_to_list(data))

    @staticmethod
    def success_with_size(data=None, code=10000, msg="Success", total=0):
        if data is None:
            return QmsResponse.encode_json(dict(code=code, msg=msg, data=list(), total=0))
        return QmsResponse.encode_json(dict(code=code, msg=msg, data={"list": data, "total": total}, suceess=True))

    @staticmethod
    def failed(msg, code=99999, data=None):
        return dict(code=code, msg=str(msg), data=data, suceess=False)

    @staticmethod
    def forbidden():
        return dict(code=403, msg="对不起, 你没有权限")

    @staticmethod
    def file(filepath, filename):
        return FileResponse(filepath, filename=filename, background=BackgroundTask(lambda: os.remove(filepath)))


# 自定义装饰器：处理空字符串，转换为 None
def parse_type(value: Optional[str] = Query(None)) -> Optional[int]:
    if value == "":
        return None  # 为空字符串时返回 None
    try:
        return int(value)  # 尝试将值转换为 int
    except (ValueError, TypeError):
        return None  # 无法转换时返回 None

