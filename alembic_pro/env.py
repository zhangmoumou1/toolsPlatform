# env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 导入你的配置类
from config import Config  # 确保替换为正确的路径

# 设置日志配置
fileConfig(context.config.config_file_name)

# 动态设置数据库连接URL
db_url = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(
    Config.MYSQL_USER, Config.MYSQL_PWD, Config.MYSQL_HOST, Config.MYSQL_PORT, Config.DBNAME)
context.config.set_main_option('sqlalchemy.url', db_url)

# 引入你的模型
from app.crud import Base
target_metadata = Base.metadata
from app.models import audit_data_model
from app.models import dictionary_model
from app.models import tools_info_model

def include_object(object, name, type_, reflected, compare_to):
    """判断是否包含该对象，忽略指定表"""
    if type_ == 'table' and name == 'apscheduler_jobs':
        return False  # 忽略apscheduler_jobs表
    else:
        return True

def run_migrations_offline():
    url = context.config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        context.config.get_section(context.config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            # 使用include_object钩子
            include_object=include_object
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()