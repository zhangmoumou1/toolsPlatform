from app.models.basic import QmsBase
from sqlalchemy import Column, String, INT, event

class DictionaryModel(QmsBase):
    dict_code = Column(INT, nullable=False)
    dict_name = Column(String(32), nullable=True, comment="字典名称")
    enum_id = Column(INT, nullable=False, comment="字典枚举id")
    enum_name = Column(String(32), nullable=True, comment="字典枚举名称")

    __tablename__ = "dictionary"
    __tag__ = "枚举字典"
    __table_args__ = {"comment": "枚举字典"}

    def __init__(self, dict_code, dict_name, enum_id, enum_name, user, id=None):
        self.dict_code = dict_code
        self.dict_name = dict_name
        self.enum_id = enum_id
        self.enum_name = enum_name
        super().__init__(user, id)

# # 定义 before_insert 事件监听器
# @event.listens_for(DictionaryModel, 'before_insert')
# def receive_before_insert(mapper, connection, target):
#     # 在插入之前增加 dict_code 值
#     target.dict_code += 1
#
# # 定义 before_update 事件监听器
# @event.listens_for(DictionaryModel, 'before_update')
# def receive_before_update(mapper, connection, target):
#     # 在更新之前增加 dict_code 值
#     target.dict_code += 1