from app.models.basic import QmsBase
from sqlalchemy import Column, String, TEXT, BIGINT, BOOLEAN, INT, TIMESTAMP, JSON

from app.models import Base

class AuditDataImportModel(QmsBase):
    tool_id = Column(INT, nullable=False, comment="工具ID，关联tools_info.id")
    env = Column(INT, nullable=False, comment="执行环境，取自字典表dict_code=20250000")
    channel = Column(INT, nullable=False, comment="渠道，取自字典表dict_code=20250002")
    files = Column(JSON, nullable=False, comment="文件信息")
    execution_log = Column(TEXT, nullable=True, comment="执行明细，用于回滚")
    execution_result = Column(TEXT, nullable=True, comment="执行结果")
    is_rollback = Column(BOOLEAN, nullable=False, comment="是否回滚")

    __tablename__ = "qms_audit_data"
    __tag__ = "钩稽数据导入记录"
    __table_args__ = {"comment": "钩稽数据导入记录"}

    def __init__(self, tool_id,  env, channel, files, execution_log, execution_result, is_rollback, user, id=None):
        self.tool_id = tool_id
        self.env = env
        self.channel = channel
        self.files = files
        self.is_rollback = is_rollback
        self.execution_log = execution_log
        self.execution_result = execution_result
        super().__init__(user, id)