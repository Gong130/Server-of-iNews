# Server-of-iNews

## 项目简介
本项目旨在演示一个最小可用的“登录 + 受保护资源 + 数据展示”的完整链路：
- 用户在根路径完成注册/登录，登录成功后浏览器保存 JWT。
- 登录页将跳转到 `news.html`，页面通过 `Authorization: Bearer <token>` 访问受保护的 `/api/news` 接口。
- 后端从数据库中查询新闻并返回给前端展示。

## 功能特性
- 用户注册与登录（密码哈希存储）
- 基于 JWT 的接口鉴权与会话保持
- 新闻数据持久化至 SQL Server，并提供受保护的新闻列表接口
- 首次启动自动建表并插入示例新闻数据（空表时）

## 技术栈
- 后端：Flask, Flask-JWT-Extended, Flask-SQLAlchemy, pyodbc
- 数据库：Microsoft SQL Server（ODBC Driver 17/18）
- 前端：原生 HTML/JS（`static/new.html`）

## 目录结构
```
Server of iNews/
  instance/
  main.ipynb
  SQL.ipynb
sql.py                # 后端主程序（Flask）
SQLQuery1.sql
static/
  new.html            # 新闻展示页面（受保护）
test.py
```

## 快速开始（Windows）
1. 安装依赖（建议使用虚拟环境）
   ```powershell
   # 可选：创建并激活虚拟环境
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # 安装依赖
   pip install flask flask_sqlalchemy flask-jwt-extended pyodbc
   ```
2. 安装/确认 ODBC 驱动（其一）
   - 微软官方：`ODBC Driver 17 for SQL Server` 或 `ODBC Driver 18 for SQL Server`
   - 安装后重启终端使驱动可用
3. 配置数据库连接
   打开 `sql.py` 中的连接串：
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = (
       'mssql+pyodbc://sa:123456@localhost/inews_db?driver=ODBC+Driver+17+for+SQL+Server'
   )
   ```
   - 修改用户名、密码、服务器、数据库名或驱动为你本地环境
4. 运行服务
   ```powershell
   python .\sql.py
   ```

## 数据库配置（SQL Server）
- 确保 SQL Server 已启动并允许本机连接
- 若数据库 `inews_db` 不存在，SQLAlchemy 会在连接成功后自动建表（前提是数据库存在）
- 首次运行时若 `news` 表为空，会自动插入 3 条示例新闻

## 运行与体验
1. 打开浏览器访问根路径：`http://127.0.0.1:5000/`
2. 在页面完成注册或直接登录
3. 登录成功后页面会跳转到 `/news.html` 并展示新闻列表
4. 退出登录：点击页面“退出登录”按钮

## API 文档
- POST `/api/auth/register`
  - 请求体：`{ "username": "string", "password": "string" }`
  - 响应：`201` 注册成功 或错误信息
- POST `/api/auth/login`
  - 请求体：`{ "username": "string", "password": "string" }`
  - 响应：`{ "access_token": "<JWT>" }`
- GET `/api/news`（受保护）
  - Header：`Authorization: Bearer <JWT>`
  - 响应：新闻数组，如：
    ```json
    [
      { "id": 1, "title": "...", "author": "...", "created_at": "...", "content": "..." }
    ]
    ```

- 登录/注册页：

  <img width="806" height="487" alt="image" src="https://github.com/user-attachments/assets/bf265230-87cd-44d4-ae1d-ae435be6f3be" />


- 登录成功后的新闻列表页：

  <img width="672" height="394" alt="image" src="https://github.com/user-attachments/assets/1becf958-5b53-4012-9ad5-c0d9bdda5046" />


## 常见问题与排错
- 加载新闻失败（页面提示）：
  - 打开浏览器开发者工具 Network，查看 `/api/news` 的状态码与响应
  - 若 `401/422`，多半为 Token 问题：清空 `localStorage.removeItem('access_token')` 并重新登录
  - 检查服务端日志是否有 “Subject must be a string” 等 JWT 错误
- 连接数据库失败：
  - 确认 ODBC 驱动名称与版本与连接串匹配
  - 检查 SQL Server 实例、用户名/密码与目标数据库是否存在
- 中文路径/Windows 路径：
  - 项目路径包含中文通常没问题，但某些工具可能不兼容，建议使用英文路径作为替代方案

---

