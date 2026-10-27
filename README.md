# APProductDB

APProductDB 是维护网络产品、竞品规格、对标关系和来源证据的 Django 应用，使用 SQLite 保存数据，Waitress 提供本地 Web 服务。

## 从哪里开始

| 目标 | 文档 |
| --- | --- |
| 在自己的电脑上从零安装、登录和使用 | [本地环境与首次启动](app/docs/ENVIRONMENT_SETUP.md) |
| 让同一局域网的其他电脑访问，或配置 Windows 开机运行 | [局域网部署与运行](app/docs/DEPLOYMENT.md) |
| 备份、换电脑迁移、恢复数据 | [备份与恢复](app/docs/RESTORE.md) |
| 了解模块和数据结构 | [架构](app/docs/ARCHITECTURE.md)、[数据库](app/docs/DATABASE_SCHEMA.md) |

## 本机快速启动（Windows PowerShell）

前提：已安装 64 位 Python 3.12 或 3.13，并将仓库克隆或解压到本地。以下从**仓库根目录**执行；无需 D 盘，无需知道本机局域网 IP，也无需管理员权限。完整安装和故障处理见[环境说明](app/docs/ENVIRONMENT_SETUP.md)。

```powershell
cd app
py -3 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe scripts\create_env.py
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py initialize_catalog
& .\.venv\Scripts\python.exe manage.py createsuperuser
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
& .\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 config.wsgi:application
```

保持终端打开，访问 [登录页面](http://127.0.0.1:8000/accounts/login/)，使用刚创建的管理员用户名和密码登录。健康检查：[health](http://127.0.0.1:8000/health/)。按 `Ctrl+C` 停止服务。再次启动只需进入 `app` 并执行最后一条命令。

`create_env.py` 自动生成密钥和当前目录对应的数据路径；已有 `.env` 时不会覆盖。首次安装不要复制他人的 `.env` 或数据库。初始化只建立基础目录数据，不会自动导入实际产品。

## 地址与目录原则

- `127.0.0.1` / `localhost` 始终指向浏览器所在电脑，只用于本机访问。
- 同事需要使用**运行服务那台电脑的实际局域网 IPv4 地址**。每个人的地址和网段都可能不同，按[部署说明](app/docs/DEPLOYMENT.md)获取并配置，不照抄示例地址。
- `0.0.0.0` 是服务器监听所有网卡的参数，不是浏览器访问地址。
- 普通本地部署可放在任意可写目录；现有 Windows 计划任务脚本要求 `D:\APProductDB` 布局，不能仅修改文档路径就用于其他盘符。

## 项目结构

```text
APProductDB/             # 克隆或解压后的仓库根目录
├── app/                # Django 源码、manage.py、scripts/、docs/
│   ├── .env.example    # 配置说明；实际配置由 create_env.py 生成
│   └── .venv/          # 本机创建的虚拟环境，不提交 Git
├── datasets/           # 规格识别基准数据
├── data/               # 默认 SQLite 数据库，首次运行时创建
├── media/              # 上传文件
├── staticfiles/        # collectstatic 输出
├── logs/               # 日志
├── backups/            # 备份
└── pyproject.toml      # 测试、静态检查配置
```

数据库、上传文件、日志、备份、密钥均不进入 Git。迁移源码不会自动迁移业务数据。

## 开发检查

在 `app` 目录执行：

```powershell
& .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py test
& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m ruff check .
```

[开发规格](app/docs/DEVELOPMENT_SPEC.md)保留设计背景；当前安装和运行步骤以本 README 及上述部署、恢复文档为准。
