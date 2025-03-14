# 基础配置类
import os
from typing import List
from pydantic import BaseSettings
import logging
ROOT = os.path.dirname(os.path.abspath(__file__))

class BaseConfig(BaseSettings):
    LOG_DIR = os.path.join(ROOT, 'logs')
    LOG_NAME = os.path.join(LOG_DIR, 'qms.log')

    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int

    HEARTBEAT: int = 48

    # mock server
    MOCK_ON: bool
    PROXY_ON: bool
    PROXY_PORT: int
    MYSQL_HOST: str
    MYSQL_PORT: int
    MYSQL_USER: str
    MYSQL_PWD: str
    DBNAME: str

    # 业务MySQL连接信息
    MYSQL_HOST_V5: str
    MYSQL_PORT_V5: int
    MYSQL_USER_V5: str
    MYSQL_PWD_V5: str
    MYSQL_HOST_V1: str
    MYSQL_PORT_V1: int
    MYSQL_USER_V1: str
    MYSQL_PWD_V1: str
    MYSQL_HOST_TEST: str
    MYSQL_PORT_TEST: int
    MYSQL_USER_TEST: str
    MYSQL_PWD_TEST: str


    # WARNING: close redis can make job run multiple times at the same time
    REDIS_ON: bool
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int
    REDIS_PASSWORD: str
    # Redis连接信息
    REDIS_NODES: List[dict] = []

    # sqlalchemy
    SQLALCHEMY_DATABASE_URI: str = ''
    # 异步URI
    ASYNC_SQLALCHEMY_URI: str = ''
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 权限 0 普通用户 1 组长 2 管理员
    MEMBER = 0
    MANAGER = 1
    ADMIN = 2

    # github access_token地址
    GITHUB_ACCESS = "https://github.com/login/oauth/access_token"

    # github获取用户信息
    GITHUB_USER = "https://api.github.com/user"

    # client_id
    CLIENT_ID: str

    # SECRET
    SECRET_KEY: str

    # 测试报告路径
    REPORT_PATH = os.path.join(ROOT, "templates", "report.html")

    # 重置密码路径
    PASSWORD_HTML_PATH = os.path.join(ROOT, "templates", "reset_password.html")

    # APP 路径
    APP_PATH = os.path.join(ROOT, "app")

    # dao路径
    DAO_PATH = os.path.join(APP_PATH, 'crud')

    # markdown地址
    MARKDOWN_PATH = os.path.join(ROOT, 'templates', "markdown")

    SERVER_REPORT = "http://localhost:8000/#/record/report/"

    OSS_URL = "https://desp-chn.oss-cn-hangzhou.aliyuncs.com/test"

    # 七牛云链接地址，如果采用七牛oss，需要自行替换
    QINIU_URL = "cdn.zhangyanc.club"

    RELATION = "qms_relation"
    ALIAS = "__alias__"
    TABLE_TAG = "__tag__"
    # 数据库表展示的变更字段
    FIELD = "__fields__"
    SHOW_FIELD = "__show__"
    IGNORE_FIELDS = ('created_at', "updated_at", "deleted_at", "create_user", "update_user")

    # 测试计划中，case默认重试次数
    RETRY_TIMES = 1

    # 日志名
    QMS_ERROR = "qms_error"
    QMS_INFO = "qms_info"

class DevConfig(BaseConfig):
    class Config:
        env_file = os.path.join(ROOT, "conf", "dev.env")


class ProConfig(BaseConfig):
    class Config:
        env_file = os.path.join(ROOT, "conf", "pro.env")

    SERVER_REPORT = "https://qms.fun/#/record/report/"
    SERVER_HOST = "127.0.0.1"


# 获取qms环境变量
QMS_ENV = os.environ.get("qms_env", "pro")
# 如果qms_env存在且为prod
Config = ProConfig() if QMS_ENV and QMS_ENV.lower() == "pro" else DevConfig()

# init redis
if Config.REDIS_PASSWORD:
    Config.REDIS_NODES = [
        {
            "host": Config.REDIS_HOST, "port": Config.REDIS_PORT, "db": Config.REDIS_DB, "password": Config.REDIS_PASSWORD
        }
    ]
else:
    Config.REDIS_NODES = [
        {
            "host": Config.REDIS_HOST, "port": Config.REDIS_PORT, "db": Config.REDIS_DB
        }
    ]

# init sqlalchemy (used by apscheduler)
Config.SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://{}:{}@{}:{}/{}'.format(
    Config.MYSQL_USER, Config.MYSQL_PWD, Config.MYSQL_HOST, Config.MYSQL_PORT, Config.DBNAME)

# init async sqlalchemy
Config.ASYNC_SQLALCHEMY_URI = f'mysql+aiomysql://{Config.MYSQL_USER}:{Config.MYSQL_PWD}' \
                              f'@{Config.MYSQL_HOST}:{Config.MYSQL_PORT}/{Config.DBNAME}'

# # 业务MySQL异步连接信息
def get_async_ur(env, db_name):
    if env == 'v5环境':
        ASYNC_SQLALCHEMY_URI = f'mysql+aiomysql://{Config.MYSQL_USER_V5}:{Config.MYSQL_PWD_V5}' \
                               f'@{Config.MYSQL_HOST_V5}:{Config.MYSQL_PORT_V5}/{db_name}'
    elif env == 'v1环境':
        ASYNC_SQLALCHEMY_URI = f'mysql+aiomysql://{Config.MYSQL_USER_V1}:{Config.MYSQL_PWD_V1}' \
                               f'@{Config.MYSQL_HOST_V1}:{Config.MYSQL_PORT_V1}/{db_name}'
    elif env == 'test环境':
        ASYNC_SQLALCHEMY_URI = f'mysql+aiomysql://{Config.MYSQL_USER_TEST}:{Config.MYSQL_PWD_TEST}' \
                               f'@{Config.MYSQL_HOST_TEST}:{Config.MYSQL_PORT_TEST}/{db_name}'
    return ASYNC_SQLALCHEMY_URI

BANNER = f"""

 _____                   _         _                _ 
|  ___|                 | |      / _ \             (_)
| |_    __ _    ___    _| |_    / /_\ \    ___      _ 
|  _|  / _` |  / __|  |_| |_|  | | _ | |  | '_ \   | |
| |   | (_| |  \__ \    | |_   | |   | |  | |_) |  | |
\_|    \__,_|  |___/     \__|  \_|   |_/  | .__/   |_|
                                          | |       
                                          |_|                                                 
"""
