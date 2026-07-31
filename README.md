# APProductDB

APProductDB 是用于维护网络产品、竞品规格、对标关系和来源证据的内部 Django 应用。

## 项目结构

```text
APProductDB/
├── app/                 # Django 应用、模板、静态资源、迁移和测试
├── datasets/            # 可复现的规格识别基准数据
├── app/.env.example     # 环境变量示例
├── pyproject.toml       # 测试与静态检查配置
└── README.md
```

运行时数据库、上传文件、日志、备份和静态文件不会进入 Git。生产部署时建议统一放在 `D:\APProductDB` 下。

## 本地启动

```powershell
cd app
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts\create_env.py
python manage.py migrate
python manage.py initialize_catalog
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

访问 `http://127.0.0.1:8000/accounts/login/`。

## 质量检查

```powershell
cd app
python manage.py check
python manage.py test
pytest
ruff check .
```

架构说明见 [app/docs/ARCHITECTURE.md](app/docs/ARCHITECTURE.md)，生产部署见 [app/docs/DEPLOYMENT.md](app/docs/DEPLOYMENT.md)，恢复流程见 [app/docs/RESTORE.md](app/docs/RESTORE.md)。
