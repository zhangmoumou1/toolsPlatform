from app.models.basic import QmsBase
from sqlalchemy import Column, String, INT, TEXT, JSON

class ToolsInfoModel(QmsBase):
    title = Column(String(32), nullable=False, comment="标题")
    type = Column(INT, nullable=False, comment="类目，取自字典表dict_code=20250001")
    description = Column(String(50), nullable=True, comment="描述")
    manual = Column(TEXT, nullable=True, comment="操作说明")
    total = Column(INT, nullable=False, default=0, comment="使用数")

    __tablename__ = "tools_info"
    __tag__ = "工具基础信息"
    __table_args__ = {"comment": "工具基础信息"}

    def __init__(self, title, type, description, manual, total, user, id=None):
        self.title = title
        self.type = type
        self.description = description
        self.manual = manual
        self.total = total
        super().__init__(user, id)

class FeedBackModel(QmsBase):
    title = Column(String(32), nullable=False, comment="标题")
    description = Column(TEXT, nullable=True, comment="描述")
    url = Column(JSON, nullable=False, comment="文件地址")
    __tablename__ = "feedback"
    __tag__ = "意见反馈"
    __table_args__ = {"comment": "意见反馈"}

    def __init__(self, title, description, url, user, id=None):
        self.title = title
        self.description = description
        self.url = url
        super().__init__(user, id)