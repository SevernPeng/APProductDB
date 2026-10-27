# APProductDB 应用目录

这是 Django 应用目录，包含 `manage.py`、依赖清单、配置、业务模块与运行脚本。仓库根目录在本目录的上一级。

- 首次使用：按[仓库 README](../README.md)或[完整环境初始化指南](docs/ENVIRONMENT_SETUP.md)安装。
- 局域网访问、IP/网段配置、Windows 计划任务：[部署指南](docs/DEPLOYMENT.md)。
- 备份、恢复与换电脑迁移：[恢复手册](docs/RESTORE.md)。
- 代码结构：[架构](docs/ARCHITECTURE.md)、[数据库](docs/DATABASE_SCHEMA.md)。

已有环境时，在本目录运行以下命令启动本机服务：

```powershell
& .\.venv\Scripts\waitress-serve.exe --listen=127.0.0.1:8000 config.wsgi:application
```

访问 `http://127.0.0.1:8000/accounts/login/`。不要把这个地址发给其他电脑使用；局域网共享需要按部署指南配置实际服务器地址。
