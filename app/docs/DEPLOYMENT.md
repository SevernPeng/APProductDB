# Windows 部署与运行

## 数据位置

本项目的应用和所有业务数据均固定在 `D:\APProductDB`：

```text
D:\APProductDB\
├── app\             应用、虚拟环境和 Git 仓库
├── data\            SQLite 正式数据库
├── media\           产品图片、导入原文件和证据附件
├── staticfiles\     WhiteNoise 收集后的静态文件
├── logs\            应用、Waitress、备份和健康检查日志
├── backups\         一致性备份
└── restore-tests\   隔离恢复测试报告
```

生产设置会拒绝数据库、媒体、静态文件、日志或备份目录指向 `D:\APProductDB` 以外的位置。不要把运行中的数据库放入 OneDrive 或其他实时同步目录。

## 当前局域网配置

- 当前地址：`192.168.68.56`
- 当前网段：`192.168.68.0/22`
- 同事访问：`http://192.168.68.56:8000/`
- 防火墙只允许 Domain/Private 网络配置文件中的 `192.168.68.0/22` 访问 TCP 8000。

必须在路由器或 DHCP 服务器上为本机设置 `192.168.68.56` 的地址保留；如果地址变化，重新运行 `configure_runtime.py`，并使用新网段重新安装防火墙规则。不得配置公网端口映射。

## 初始化生产运行环境

在普通 PowerShell 中执行：

```powershell
cd D:\APProductDB\app
& .\.venv\Scripts\python.exe .\scripts\configure_runtime.py --host 192.168.68.56 --data-root D:\APProductDB
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
& .\.venv\Scripts\python.exe manage.py check --deploy
```

本项目按需求仅在受信任局域网使用 HTTP，因此 `check --deploy` 关于 HTTPS、HSTS 和 Secure Cookie 的提示属于已知部署选择；不得把该配置暴露到公网。

## 安装防火墙和计划任务

以管理员身份打开 Windows PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
cd D:\APProductDB\app
.\scripts\install_windows.ps1 -LanSubnet 192.168.68.0/22 -DailyBackupTime 23:00
```

脚本安装：

- `APProductDB-Server`：开机启动 Waitress；失败后每5分钟重试，最多3次；
- `APProductDB-Backup`：每天23:00运行一致性备份；
- `APProductDB-HealthCheck`：每15分钟检查 `/health/`；
- `APProductDB-LAN-8000`：仅允许当前局域网访问8000端口；
- 交流电源下不自动睡眠，合盖不睡眠。
- 数据库、附件、备份、日志、恢复报告和 `.env` ACL 仅允许当前管理员、SYSTEM 与本机 Administrators。

如果电源设置由公司策略管理，可添加 `-SkipPowerSettings`，然后由 IT 单独配置。BIOS 的断电恢复自动开机需要人工按公司政策设置。

## 服务操作

手工前台启动生产服务器：

```powershell
D:\APProductDB\app\scripts\start_server.ps1
```

计划任务操作：

```powershell
Start-ScheduledTask -TaskName APProductDB-Server
Stop-ScheduledTask -TaskName APProductDB-Server
Get-ScheduledTask -TaskName APProductDB-*
Get-ScheduledTaskInfo -TaskName APProductDB-Server
```

正式运行只使用 Waitress，不使用 `manage.py runserver`。启动计划任务前应关闭仍占用8000端口的开发服务器。

## 备份和恢复演练

手工备份：

```powershell
D:\APProductDB\app\scripts\backup.ps1
```

或者：

```powershell
& D:\APProductDB\app\.venv\Scripts\python.exe D:\APProductDB\app\manage.py backup_database
```

隔离恢复测试：

```powershell
& D:\APProductDB\app\.venv\Scripts\python.exe D:\APProductDB\app\manage.py test_restore --backup latest
```

恢复测试不会覆盖正式数据库；报告保存在 `D:\APProductDB\restore-tests\reports`。每月至少执行一次。正式恢复步骤见 `docs\RESTORE.md`。

## 日常检查

- `http://127.0.0.1:8000/health/` 返回 `{"status":"ok","database":"ok"}`；
- `D:\APProductDB\logs\health-check.log` 持续出现 `OK`；
- `D:\APProductDB\backups` 每天出现一个时间戳目录；
- `Get-ScheduledTaskInfo` 中最近结果为0；
- 每月执行隔离恢复测试并保存通过报告。

如公司允许，应把完成后的备份目录再复制到另一块磁盘或公司批准的安全存储；不要同步正在运行的 SQLite 文件。
