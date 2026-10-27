# 备份、恢复与换电脑迁移

本文适用于普通本地部署及 Windows 自动运行部署。默认在实际仓库的 `app` 目录执行，使用本机 `.env`。恢复会替换业务数据库与附件，应先验证备份并保留当前数据。

## 1. 创建一致性备份

```powershell
& .\.venv\Scripts\python.exe manage.py backup_database --no-prune
& .\.venv\Scripts\python.exe manage.py test_restore --backup latest
```

第一条备份数据库、附件、环境配置与版本信息，`--no-prune` 保留已有备份；日常自动备份使用自身保留策略。第二条在数据根目录的 `restore-tests` 下隔离校验，不覆盖当前数据库；成功后输出报告位置。每月至少演练一次。

备份位于配置的 `BACKUP_DIR` 下，以时间戳命名。保留完整目录中的数据库、`media.zip`、`environment.env`、`manifest.json` 及其余文件；不要只复制 SQLite 文件。备份含密钥与业务数据，应限制访问并复制到另一块磁盘或批准的安全存储。

## 2. 确认目标路径并验证指定备份

查看当前实际配置：

```powershell
& .\.venv\Scripts\python.exe manage.py shell -c "from django.conf import settings as s; print('ROOT:', s.RUNTIME_DATA_ROOT); print('DATABASE:', s.DATABASES['default']['NAME']); print('MEDIA:', s.MEDIA_ROOT); print('BACKUPS:', s.BACKUP_DIR)"
```

下面恢复命令适用于数据库为 `数据根目录\data\ap_products.sqlite3`、附件为 `数据根目录\media`、备份为 `数据根目录\backups` 的标准布局。如果上述输出使用自定义位置，先按实际位置调整命令，不能盲目执行。数据必须位于 `AP_PRODUCT_DATA_ROOT` 内。

在当前 PowerShell 中输入刚确认的实际数据根目录，并选择完整备份目录名：

```powershell
$DataRoot = (Resolve-Path -LiteralPath (Read-Host '请输入实际数据根目录绝对路径')).Path
$BackupName = Read-Host '请输入 backups 下实际备份目录名（YYYY-MM-DD_HHMMSS）'
if ($BackupName -notmatch '^\d{4}-\d{2}-\d{2}_\d{6}$') { throw '备份目录名格式错误' }
$BackupPath = Join-Path (Join-Path $DataRoot 'backups') $BackupName
Get-Item -LiteralPath $BackupPath
& .\.venv\Scripts\python.exe manage.py test_restore --backup $BackupName
if ($LASTEXITCODE -ne 0) { throw '备份验证失败，停止恢复' }
```

必须看到成功提示，并确认 `restore-tests\reports` 下报告状态为 `passed`。不要使用文档里的历史日期代替实际备份名称。

## 3. 停止所有写入与自动重启

前台运行时，在服务终端按 `Ctrl+C` 停止；同时停止手工导入、抓取、备份等操作。

如果安装了 Windows 自动任务，在管理员 PowerShell 中先禁用任务，防止健康检查、定时任务或重启触发新的写入，再停止它们：

```powershell
$TaskNames = @('APProductDB-HealthCheck','APProductDB-SyscomPrices','APProductDB-Backup','APProductDB-Server')
foreach ($TaskName in $TaskNames) {
    Disable-ScheduledTask -TaskName $TaskName
    Stop-ScheduledTask -TaskName $TaskName
}
Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
```

这些命令仅在上述任务确实已安装时执行。确认没有监听进程和其他写入数据库的进程后再继续。仅停止服务器任务不足以防止健康检查自动重启服务。

## 4. 保留现场并恢复

在仍可读取数据库时，可在停止业务写入后再运行一次 `backup_database --no-prune` 保留当前状态；数据库损坏无法备份时，下面隔离副本仅用于保留现场。

以下命令在设置了第 2 节变量的窗口执行。先验证所有目标都位于已确认的数据根目录内，输出路径并人工核对：

```powershell
$DatabaseDir = Join-Path $DataRoot 'data'
$DatabasePath = Join-Path $DatabaseDir 'ap_products.sqlite3'
$MediaPath = Join-Path $DataRoot 'media'
$Quarantine = Join-Path (Join-Path $DataRoot 'recovery-quarantine') (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
$RootPrefix = $DataRoot.TrimEnd('\') + '\'
foreach ($Candidate in @($BackupPath,$DatabaseDir,$DatabasePath,$MediaPath,$Quarantine)) {
    $FullPath = [System.IO.Path]::GetFullPath($Candidate)
    if (-not $FullPath.StartsWith($RootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "目标路径不在数据根目录内：$FullPath"
    }
    $FullPath
}
```

路径确认无误、服务和写入全部停止后执行：

```powershell
New-Item -ItemType Directory -Path $Quarantine -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $DatabaseDir -Force | Out-Null
foreach ($Suffix in @('', '-wal', '-shm', '-journal')) {
    $CurrentFile = $DatabasePath + $Suffix
    if (Test-Path -LiteralPath $CurrentFile) {
        Move-Item -LiteralPath $CurrentFile -Destination (Join-Path $Quarantine ('ap_products.sqlite3' + $Suffix)) -ErrorAction Stop
    }
}
if (Test-Path -LiteralPath $MediaPath) {
    Move-Item -LiteralPath $MediaPath -Destination (Join-Path $Quarantine 'media') -ErrorAction Stop
}
Copy-Item -LiteralPath (Join-Path $BackupPath 'ap_products.sqlite3') -Destination $DatabasePath -ErrorAction Stop
New-Item -ItemType Directory -Path $MediaPath -ErrorAction Stop | Out-Null
Expand-Archive -LiteralPath (Join-Path $BackupPath 'media.zip') -DestinationPath $MediaPath -ErrorAction Stop
```

同时隔离 SQLite 的 WAL/SHM/journal（如存在），避免旧辅助文件与恢复后的数据库混用。任一命令失败立即停止，不要启动半恢复的服务。不要删除 `recovery-quarantine` 中的故障现场。

将备份中的 `environment.env` 与目标电脑 `.env` 人工比较：路径、IP、网段必须使用目标电脑的值；密钥应按恢复需求保留，不能无检查直接覆盖整个配置。自动任务安装曾收紧文件权限时，恢复后还要确认任务账户可以读写恢复文件。

## 5. 检查并恢复服务

使用与备份版本匹配的源码/依赖恢复，升级迁移前保留原备份。在 `app` 目录执行：

```powershell
& .\.venv\Scripts\python.exe manage.py migrate
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py shell -c "from django.db import connection; c=connection.cursor(); c.execute('PRAGMA integrity_check'); print(c.fetchone()[0])"
```

最后一条必须输出 `ok`，其他命令均应成功。手工部署按[环境指南](ENVIRONMENT_SETUP.md)或[局域网指南](DEPLOYMENT.md)启动。

已安装自动任务时，在管理员窗口重新启用第 3 节禁用的任务，然后启动服务器：

```powershell
foreach ($TaskName in $TaskNames) { Enable-ScheduledTask -TaskName $TaskName }
Start-ScheduledTask -TaskName APProductDB-Server
```

服务就绪后访问 `http://127.0.0.1:8000/health/`，并按实际服务器局域网地址从另一台电脑验证。登录后抽查产品、对标比较、修改申请与审计记录、图片及附件下载；全新空数据库的备份则检查对应页面能正常打开。保留恢复报告与隔离现场，确认成功后再决定清理。

## 6. 换电脑迁移

1. 在旧电脑创建并验证完整备份，记录源码版本；需要无遗漏切换时，在最终备份前停止业务写入。
2. 在新电脑按环境指南安装对应版本源码与依赖、生成本机 `.env`；不要复制旧 `.venv`。
3. 将完整备份目录放到新电脑配置的 `BACKUP_DIR` 下，按本文验证并恢复。
4. 用新电脑实际路径检查配置；按局域网指南重新获取 IP 和前缀长度、设置主机/CSRF 来源与防火墙。不要复制旧 IP 或网段。
5. 按需在新电脑安装自动任务，验证登录与附件后通知使用者新地址。确认切换成功前保留旧备份。
