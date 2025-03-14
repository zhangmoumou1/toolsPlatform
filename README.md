
## 研策测试工具后端

![png](https://img.shields.io/badge/Python-3.8+-green)
![png](https://img.shields.io/badge/Python-FastApi-green)

### 🎉 技术栈

- [x] 🎨 Python FastApi
- [x] 🎶 SQLAlchemy
- [x] 🔒 Redis
- [x] 💎 Asyncio
- [x] 🎃 Apscheduler

### 🎉 部署步骤
#### 本地部署
1、拉取代码

```bash
$ git clone http://git.wxb.com.cn/AutomationTestGroup/toolsPlatform.git
```

2、安装依赖

```bash
# 可换豆瓣源或者清华源安装依赖
$ pip install -r requirements.txt
```

3、conf/dev.env，修改mysql和redis连接信息；config.py修改QMS_ENV为dev


4、启动服务

```bash
$ python qms.py  
```
看到如下表示启动成功
```bash
2025-03-14 10:25:58.518 | SUCCESS  | main:<module>:21 - qms is running at dev
2025-03-14 10:25:58.519 | SUCCESS  | main:<module>:22 - 

 _____                   _         _                _ 
|  ___|                 | |      / _ \             (_)
| |_    __ _    ___    _| |_    / /_\ \    ___      _ 
|  _|  / _` |  / __|  |_| |_|  | | _ | |  | '_ \   | |
| |   | (_| |  \__ \    | |_   | |   | |  | |_) |  | |
\_|    \__,_|  |___/     \__|  \_|   |_/  | .__/   |_|
                                          | |       
                                          |_|

2025-03-14 10:25:58.523 | INFO     | uvicorn.server:serve:75 - Started server process [17816]
2025-03-14 10:25:58.525 | INFO     | uvicorn.lifespan.on:startup:45 - Waiting for application startup.
2025-03-14 10:25:58.787 | SUCCESS  | main:init_redis:92 - redis connected success.        ✔
2025-03-14 10:26:01.073 | SUCCESS  | main:init_scheduler:117 - ApScheduler started success.        ✔
2025-03-14 10:26:01.078 | SUCCESS  | main:init_database:128 - database and tables created success.        ✔
2025-03-14 10:26:01.408 | INFO     | uvicorn.lifespan.on:startup:59 - Application startup complete.
2025-03-14 10:26:01.413 | INFO     | uvicorn.server:_log_started_message:206 - Uvicorn running on http://127.0.0.1:7777 (Press CTRL+C to quit)
```

5、API地址

http://127.0.0.1:7777

6、接口文档

https://127.0.0.1:7777/docs#/

#### 生产部署
MySQL和Redis统一用test环境，mysql库名qms，redis为db5

1、首次部署

首次部署需要构建镜像
```bash
$ docker-compose up --build
```

2、jenkins部署
后续可直接使用Jenkins部署

http://192.168.1.61:8080/job/toolsPlatform/

```bash
# 若部署失败，可查看日志
$ docker logs 容器ID
$ docker-compose logs
```
3、API地址

https://test.wxb.com.cn/qms

4、接口文档

http://192.168.1.61:7777/docs#/


#### 数据迁移
当涉及到数据库/表信息变更，使用Alembic进行数据库迁移

1、初始化Alembic：如果你还没有配置Alembic，首先需要初始化它。这一步会在你的项目中创建一个alembic目录，并生成一些必要的文件（如env.py和alembic.ini）
```bash
$ alembic init alembic
```
2、env.py引入所有模型
```bash
...
...
# 引入你的模型
from app.crud import Base
target_metadata = Base.metadata
from app.models import audit_data_model
from app.models import dictionary_model
from app.models import tools_info_model
...
...
```

3、生成迁移脚本
```bash
$ alembic revision --autogenerate -m "变更描述"
```

4、应用迁移
```bash
$ alembic upgrade head
```