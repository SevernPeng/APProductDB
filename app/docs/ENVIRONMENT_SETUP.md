# 本地环境与首次启动

本文面向新电脑安装，不依赖原作者的目录、IP、网段或已安装的软件。命令默认使用 Windows PowerShell，按顺序执行；某一步失败时先处理错误再继续。

## 1. 准备软件与源码

- 安装 64 位 Python 3.12 或 3.13，启用 Python Launcher（`py`）或将 Python 加入 PATH。
- 通过 Git 克隆本仓库，或将源码 ZIP 完整解压。使用 ZIP 不需要安装 Git。
- 安装时需要联网下载 Python 依赖；SQLite 随 Python 提供，无需单独安装数据库。无需安装 Microsoft Excel。
- 源码和运行数据应放在本地可写、非实时同步的目录；避免把运行中的 SQLite 放入 OneDrive 等同步目录。

先检查：

```powershell
py -3 --version
```

如果默认版本不是 3.12/3.13，可在下一步明确使用 `py -3.12` 或 `py -3.13`。如果没有 `py`，确认 `python --version` 后，用 `python` 替代创建虚拟环境命令中的 `py -3`。

在文件资源管理器中打开**仓库根目录**并打开 PowerShell。应能看到 `README.md`、`app`、`datasets`、`pyproject.toml`。后续命令在 `app` 目录执行：

```powershell
cd app
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m pip check
```

直接调用虚拟环境中的程序，无需执行 `Activate.ps1`，也无需修改 PowerShell 执行策略。开发者可改装 `requirements-dev.txt`，其中已包含运行依赖。

## 2. 生成本机配置

```powershell
& .\.venv\Scripts\python.exe scripts\create_env.py
```

脚本创建 `app/.env`，生成随机密钥，将数据目录设置为当前仓库根目录下的 `data`、`media`、`staticfiles`、`logs`、`backups`。已有 `.env` 时只提示并退出，不会更新旧地址或旧路径。

如果使用他人交付的目录，先检查是否带有旧 `.env`。有业务数据时先备份；不要直接覆盖配置或重新初始化数据库。全新安装不应使用他人的密钥。

| 配置项 | 本机部署含义 |
| --- | --- |
| `DJANGO_SECRET_KEY` | 自动生成，保密保存；不要使用 `.env.example` 中的占位值 |
| `DJANGO_DEBUG` | 默认 `False`，使用收集后的静态文件 |
| `DJANGO_ALLOWED_HOSTS` | 默认 `127.0.0.1,localhost`，不含协议、路径或端口 |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | 本机默认留空；局域网配置见部署指南 |
| `DJANGO_TIME_ZONE` | 默认 `America/Mexico_City`，按业务需要修改为时区名称 |
| `AP_PRODUCT_REQUIRE_D_DRIVE` | 默认 `False`，允许在其他盘符运行 |
| `AP_PRODUCT_DATA_ROOT` | 未设置时为仓库根目录；所有运行数据路径必须位于此目录内 |
| `DATABASE_PATH` | SQLite 文件的绝对路径 |
| `MEDIA_ROOT`、`STATIC_ROOT`、`LOG_DIR`、`BACKUP_DIR` | 对应目录的绝对路径 |

`.env.example` 仅用于查阅配置项。推荐通过脚本生成 `.env`，不要直接复制示例中的路径。系统或终端中已有的同名环境变量优先于 `.env`；修改配置后需停止并重新启动服务。

## 3. 建库、初始化并创建管理员

```powershell
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py initialize_catalog
& .\.venv\Scripts\python.exe manage.py createsuperuser
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
& .\.venv\Scripts\python.exe manage.py check
```

按提示填写管理员用户名、邮箱和密码；输入密码时终端不会显示字符，这是正常行为。登录时使用创建的**用户名**。没有预设管理员密码。

`initialize_catalog` 创建基础品牌、品类等目录数据，不会填充原电脑上的产品、附件和用户。需要现有业务数据时使用[恢复手册](RESTORE.md)迁移，不能只复制源码。网页自助注册目前仅接受 `@tp-link.com` 邮箱；本机管理员可通过上述命令创建。

## 4. 启动与验证

```powershell
& .\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 config.wsgi:application
```

保持终端打开，在这台电脑访问：

- 登录：`http://127.0.0.1:8000/accounts/login/`
- 健康检查：`http://127.0.0.1:8000/health/`，应返回 `{"status":"ok","database":"ok"}`。

确认能登录且页面样式正常。本机模式不需要查 IP、开放防火墙或设置路由器。其他电脑不能访问此监听地址；需要共享时继续阅读[局域网部署](DEPLOYMENT.md)。

按 `Ctrl+C` 停止。以后重新打开终端，进入实际的 `app` 目录后只执行启动命令，不要重复创建管理员。

开发调试可临时设置 `.env` 中的 `DJANGO_DEBUG=True` 并使用 `manage.py runserver 127.0.0.1:8000`；不要作为日常共享服务。新增或更新静态资源后重新执行 `collectstatic`。

## 5. 常见问题

| 现象 | 处理 |
| --- | --- |
| 找不到 `manage.py` / `requirements.txt` | 当前应位于仓库的 `app` 目录 |
| 找不到 `py` / Python | 确认 Python 安装与 PATH，重新打开终端 |
| 找不到 `.venv` 下的程序 | 确认虚拟环境创建成功且依赖安装无错误；换电脑要重建虚拟环境 |
| `No module named ...` | 使用本文虚拟环境中的 Python 重新安装依赖，不使用全局 `pip` |
| 页面无样式 / 静态资源报错 | 执行 `collectstatic --noinput` 后重启，检查 `STATIC_ROOT` 是否对应本机目录 |
| `SECRET_KEY` / 路径校验报错 | 检查 `.env`，所有运行数据路径须位于实际数据根目录内；任意盘部署保持 D 盘限制为 `False` |
| `unable to open database file` / 无写入权限 | 检查目录权限、磁盘空间、旧 `.env` 是否仍指向另一台电脑 |
| 8000 端口被占用 | 先关闭已有服务，或将手工启动参数改为 `127.0.0.1:8001` 并访问相同端口 |
| 登录失败 | 用创建时的用户名；必要时运行 `manage.py changepassword 用户名`（同样使用虚拟环境 Python） |

## 6. 其他系统

macOS/Linux 可使用同样的 Django 命令，但需将创建虚拟环境改为 `python3 -m venv .venv`，Python 路径改为 `./.venv/bin/python`，Waitress 路径改为 `./.venv/bin/waitress-serve`，脚本路径用 `/`。Windows 的 `.ps1`、防火墙与计划任务步骤不适用；长期运行需自行配置对应系统的服务管理。

## 7. 更新已有安装

先按恢复手册执行备份，停止服务，再更新源码。在 `app` 中重新安装依赖，运行 `migrate`、`collectstatic --noinput`、`check`，最后启动并验证健康检查与登录。保留本机 `.env` 和运行数据；不要用新示例文件覆盖它们。
