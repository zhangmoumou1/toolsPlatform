from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.enums.DatabaseEnum import DatabaseEnum
from config import Config, get_async_ur
from app import init_logging
logger = init_logging()


def create_database():
    engine = create_engine('mysql+mysqlconnector://{}:{}@{}:{}'.format(
        Config.MYSQL_USER, Config.MYSQL_PWD, Config.MYSQL_HOST, Config.MYSQL_PORT), echo=True)
    with engine.connect() as conn:
        conn.execute("CREATE DATABASE IF NOT EXISTS qms default character set utf8mb4 collate utf8mb4_unicode_ci")
    # close engine
    engine.dispose()


# 优先建库
create_database()

# 同步engine
# engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_recycle=1500)
# 异步engine
async_engine = create_async_engine(Config.ASYNC_SQLALCHEMY_URI, pool_recycle=1500)
# Session = sessionmaker(engine)
async_session = sessionmaker(async_engine, class_=AsyncSession)


# 业务MySQL异步连接
async_engines = {}
async_sessions = {}
def business_async_session(env, db_name):
    uri = get_async_ur(env, db_name)
    if uri not in async_engines:
        async_engines[uri] = create_async_engine(uri, pool_recycle=1500)
        async_sessions[uri] = sessionmaker(async_engines[uri], class_=AsyncSession, expire_on_commit=False)
    # 创建一个新的会话实例
    Session = async_sessions[uri]
    session = Session()
    return session

# 创建对象的基类:
Base = declarative_base()


# Base.metadata.create_all(engine)


class DatabaseHelper(object):

    def __init__(self):
        # cache
        self.connections = dict()

    async def get_connection(self, sql_type: int, host: str, port: int, username: str, password: str, database: str):
        # 拼接key
        key = f"{host}:{port}:{database}:{username}:{password}:{database}"
        connection = self.connections.get(key)
        # 先判断是否已经有connection了，如果有则直接返回
        if connection is not None:
            return connection
        # 获取sqlalchemy需要的jdbc url
        jdbc_url = DatabaseHelper.get_jdbc_url(sql_type, host, port, username, password, database)
        # 创建异步引擎
        eg = create_async_engine(jdbc_url, pool_recycle=1500)
        ss = sessionmaker(bind=eg, class_=AsyncSession)
        # 将数据缓存起来
        data = dict(engine=eg, session=ss)
        self.connections[key] = data
        return data

    @staticmethod
    async def test_connection(ss):
        if ss is None:
            raise Exception("暂不支持的数据库类型")
        async with ss() as session:
            await session.execute("select 1")

    @staticmethod
    def get_jdbc_url(sql_type: int, host: str, port: int, username: str, password: str, database: str):
        if sql_type == DatabaseEnum.MYSQL:
            # mysql模式
            return f'mysql+aiomysql://{username}:{password}@{host}:{port}/{database}'
        if sql_type == DatabaseEnum.POSTGRESQL:
            return f'postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}'
        raise Exception("未知的数据库类型")

    def remove_connection(self, host: str, port: int, username: str, password: str, database: str):
        key = f"{host}:{port}:{database}:{username}:{password}:{database}"
        if self.connections.get(key):
            self.connections.pop(key)


db_helper = DatabaseHelper()
