## 凡声测试平台（后端开发）指南

![png](https://img.shields.io/badge/Python-3.8+-green)
![png](https://img.shields.io/badge/React-17+-blue)
![png](https://img.shields.io/badge/FlaskApi-green)

> 平台功能正在完善迭代中.....

### 🎉 技术栈

- [x] 🎨 Python Flask
- [x] 🎶 SQLAlchemy(你可以看到很多sqlalchemy的用法) 
- [x] 🎉 Apscheduler(定时任务框架)
- [x] 🔒 Redis
- [x] 🏐 Gunicorn(内含uvicorn，部署服务)
- [x] 👟 asyncio(几乎全异步写法，值得参考)

### ⚽ 前端地址

  [🎁 快点我](https://gitlab-dby.91duobaoyu.com/qa/testplatformWeb)

## ☕ 说明
此代码statics下已包含前端编译后的代码，运行后将直接打开平台；如需二次开发请使用前端项目，完成开发后编译将dist下文件放入本项目的statics下即可
编译命令：`npm run build`

[在线体验 🍍](https://qa-platform.91duobaoyu.com/)

<details open="open">
<summary>🌙 已有功能</summary>

| 功能点            | 状态  |
|:----------|:----|
| http测试    | ✅   |
| 权限系统      | ✅   |


</details>

### 🚚 即将到来

| 功能点          | 敬请期待 |
|:-------------|:-----|
| 接口测试模块       | 🎉🎉🎉   |
| HttpRunner支持 | 🎉🎉🎉   |
| 数据工厂         | 🎉🎉🎉   |

## ✉ 使用文档

[使用文档(语雀)](https://duobaoyu.yuque.com/lq96tk/hn7lk6/ftq8tr#aByQx)

### 🎉 后端二次开发

1. 拉取代码

```bash
$ git clone http://gitlab-dby.91duobaoyu.com:7007/qa/testplatform.git
$ cd testplatform
```

2. 安装依赖

```bash
# 可换豆瓣源或者清华源安装依赖
$ pip install -r requirements.txt
```

3. 安装并启动redis

4. 安装并启动mysql

5. 修改conf/dev.env

修改其中mysql和redis连接信息（可在本地安装），redis虽然可以不开启，但是会导致`定时任务重复执行`（基于redis实现了分布式锁）。

6. 启动服务

```bash
# 开发环境运行项目
$ python pity.py  
# 正式环境运行项目
$ nohup /root/software_package/Python-3.8.6/bin/python3.8 pity.py &
```

7. 注册用户

打开浏览器输入: `http://localhost:7777`进入登录页。

点击注册按钮，第一个注册的用户会成为`超级管理员`，拥有一切权限。

![](https://newsystem-duobaodyu.oss-cn-hangzhou.aliyuncs.com/%E7%99%BB%E5%BD%95%E9%A1%B5%202022-11-18%2011_10_59.jpg)

登录后就可以开启开发之旅啦！

8. 接口文档
https://127.0.0.1:7777/docs


redis-server redis.windows.conf
./redis-cli
CONFIG SET requirepass 123456
