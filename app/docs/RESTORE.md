# APProductDB 恢复手册

正式恢复会替换数据库和附件，只能由管理员在确认备份有效后执行。

## 1. 停止服务

以管理员 PowerShell 执行：

```powershell
Stop-ScheduledTask -TaskName APProductDB-Server
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

确认8000端口不再监听。如果仍有手工启动的 Waitress 或开发服务器，应在对应终端正常按 `Ctrl+C` 停止。

## 2. 选择并验证备份

列出备份：

```powershell
Get-ChildItem D:\APProductDB\backups -Directory | Sort-Object Name -Descending
```

对准备恢复的备份先执行隔离测试：

```powershell
cd D:\APProductDB\app
& .\.venv\Scripts\python.exe manage.py test_restore --backup 2026-07-18_230000
```

只有命令返回成功且 `D:\APProductDB\restore-tests\reports` 中报告状态为 `passed` 时才继续。

## 3. 保留当前故障现场

在 `D:\APProductDB\recovery-quarantine\<时间>` 创建目录。若数据库仍可读取，优先再运行一次 `backup_database --no-prune`；如果数据库已损坏无法备份，可在服务停止后把当前数据库和 media 复制到该隔离目录，仅用于取证，不把直接复制视为有效备份。

## 4. 恢复 SQLite 数据库

假设备份为 `D:\APProductDB\backups\2026-07-18_230000`：

```powershell
Copy-Item D:\APProductDB\backups\2026-07-18_230000\ap_products.sqlite3 D:\APProductDB\data\ap_products.sqlite3.restore -Force
Move-Item D:\APProductDB\data\ap_products.sqlite3 D:\APProductDB\recovery-quarantine\<时间>\ap_products.sqlite3 -Force
Move-Item D:\APProductDB\data\ap_products.sqlite3.restore D:\APProductDB\data\ap_products.sqlite3 -Force
```

所有目标路径必须逐项确认在 `D:\APProductDB` 下，不使用通配符。

## 5. 恢复 media

先把当前 `D:\APProductDB\media` 移到同一隔离目录，再创建新的空 media 目录并解压备份中的 `media.zip`：

```powershell
Move-Item D:\APProductDB\media D:\APProductDB\recovery-quarantine\<时间>\media
New-Item -ItemType Directory D:\APProductDB\media
Expand-Archive D:\APProductDB\backups\2026-07-18_230000\media.zip D:\APProductDB\media
```

如需恢复环境配置，将备份中的 `environment.env` 与当前 `.env` 人工比较；不要在未确认主机地址和密钥的情况下直接覆盖。

## 6. 数据库和应用检查

```powershell
cd D:\APProductDB\app
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('PRAGMA integrity_check'); print(c.fetchone()[0])"
```

最后一条必须输出 `ok`。

## 7. 启动并抽查

```powershell
Start-ScheduledTask -TaskName APProductDB-Server
Start-Sleep -Seconds 5
Invoke-RestMethod http://127.0.0.1:8000/health/
```

登录后至少抽查：

- 一个 TP-Link 产品和一个竞品详情；
- 一条对标关系和一次横向比较；
- 一条修改申请及其 AuditLog；
- 一个导入原文件或证据附件下载。

确认恢复成功后保留故障现场目录，直到管理员确认可以清理。不要自动删除 `recovery-quarantine`。
