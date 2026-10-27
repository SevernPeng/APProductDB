# 局域网部署与 Windows 运行

先完成[本地环境初始化](ENVIRONMENT_SETUP.md)，确认本机可以登录。本文默认在服务器电脑的 `app` 目录操作，使用 TCP 8000 和受信任局域网 HTTP。无需配置公网端口映射。

## 1. 选择运行方式

| 方式 | 目录限制 | 启动方法 |
| --- | --- | --- |
| 仅自己使用 | 任意本地可写目录 | 环境指南中的 `127.0.0.1:8000` |
| 临时/手工局域网共享 | 任意本地可写目录 | 本文第 2–5 节，Waitress 前台运行 |
| Windows 开机运行、定时备份与健康检查 | 当前脚本要求仓库根目录为 `D:\APProductDB`，源码在 `D:\APProductDB\app` | 完成第 2–5 节，再按第 6 节安装 |

没有 D 盘也能使用前两种方式。当前 `start_server.ps1`、`install_windows.ps1`、备份与重启等脚本含固定路径检查，不能直接用于任意盘符；仅设置 `AP_PRODUCT_REQUIRE_D_DRIVE=False` 不会解除这些脚本的限制。

## 2. 获取服务器自己的地址与网段

**服务器**是运行 Django/Waitress 的电脑，**客户端**是访问网页的其他电脑。在服务器 PowerShell 中查看：

```powershell
Get-NetIPConfiguration
Get-NetIPAddress -AddressFamily IPv4 |
    Select-Object InterfaceIndex,InterfaceAlias,IPAddress,PrefixLength
```

选择实际连接公司/家庭局域网的以太网或 Wi-Fi 网卡，结合默认网关确认。不要选回环地址 `127.*`、自动分配地址 `169.254.*`、VPN、Docker、Hyper-V 等虚拟网卡。多网卡环境下按客户端实际可达的网络选择，不自动取第一条记录；不确定时请网络管理员确认。

在**当前 PowerShell 窗口**执行以下命令，交互输入刚查到的真实值。不要把说明文字当地址填写：

```powershell
$ServerIp = Read-Host '请输入服务器局域网 IPv4 地址'
$PrefixLength = [int](Read-Host '请输入同一地址记录中的 PrefixLength（0–32）')
$ParsedIp = [System.Net.IPAddress]::Parse($ServerIp)
if ($ParsedIp.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork) {
    throw '必须输入 IPv4 地址'
}
if ($PrefixLength -lt 0 -or $PrefixLength -gt 32) { throw '前缀长度必须在 0–32 之间' }
$AddressBytes = $ParsedIp.GetAddressBytes()
$NetworkBytes = for ($i = 0; $i -lt 4; $i++) {
    $Bits = [Math]::Min(8, [Math]::Max(0, $PrefixLength - 8 * $i))
    $MaskByte = if ($Bits -eq 0) { 0 } else { 256 - [int][Math]::Pow(2, 8 - $Bits) }
    [int]$AddressBytes[$i] -band $MaskByte
}
$LanSubnet = ($NetworkBytes -join '.') + '/' + $PrefixLength
$BaseUrl = "http://"+$ServerIp+":8000"
"服务器访问地址：$BaseUrl"
"此网卡对应网段：$LanSubnet"
```

这里用真实的前缀长度计算 CIDR 网段，不假定所有人的网络都是 `/24`。例如（**仅解释计算，不能照抄配置**），`192.168.10.37/24` 的网段为 `192.168.10.0/24`，`10.20.5.37/22` 的网段为 `10.20.4.0/22`。

`$LanSubnet` 表示这张网卡的直连网段。若公司使用跨网段路由、访客 Wi-Fi 或客户端隔离，需由 IT 确认可允许的来源网段与路由；不能通过随意扩大为 `Any` 来解决。推荐在路由器/DHCP 服务器上为服务电脑保留当前地址；不要随意手工占用一个 IP。

## 3. 更新 app/.env

普通手工部署：用文本编辑器打开 `app/.env`，保留原密钥和数据路径，只将下面两项修改为刚查到的**真实服务器地址**：

```dotenv
# 以下 <服务器IPv4> 是占位符，必须替换后才能使用。
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,<服务器IPv4>
DJANGO_CSRF_TRUSTED_ORIGINS=http://<服务器IPv4>:8000
```

`ALLOWED_HOSTS` 写主机名/IP，不写协议和端口；`CSRF_TRUSTED_ORIGINS` 写完整来源（协议、主机、端口），不加路径。多值用英文逗号分隔。不要设置 `ALLOWED_HOSTS=*`。使用 DNS 名称时也要加入对应主机和来源，并确保客户端能够解析该名称。

**仅在使用 D 盘自动运行布局时**，可用项目脚本代替手工修改：

```powershell
& .\.venv\Scripts\python.exe scripts\configure_runtime.py --host $ServerIp --data-root 'D:\APProductDB'
```

此脚本要求先有 `.env`，会将所有运行数据路径重写到指定数据根目录，并启用 D 盘限制；它不会移动已有数据。已有安装更改根目录前先备份并迁移数据。新安装保持 `D:\APProductDB\app` 与数据根目录一致，不为自动任务指定另一个数据根目录。

检查并收集静态资源：

```powershell
& .\.venv\Scripts\python.exe manage.py check
& .\.venv\Scripts\python.exe manage.py collectstatic --noinput
& .\.venv\Scripts\python.exe manage.py check --deploy
```

本文使用局域网 HTTP，`check --deploy` 可能提示 HTTPS、HSTS 和 Secure Cookie 未启用；应确认这些提示仅来自选择的 HTTP 方案，并修复其他配置问题。需要公网或 HTTPS 时须另行设计反向代理、证书及安全配置，不能直接把本文服务映射到公网。

## 4. 启动服务与开放访问

先停止已有的本机服务，再在普通 PowerShell 的 `app` 目录启动：

```powershell
& .\.venv\Scripts\waitress-serve.exe --listen=0.0.0.0:8000 --threads=4 --channel-timeout=120 config.wsgi:application
```

`0.0.0.0` 表示监听所有 IPv4 网卡，浏览器仍使用实际服务器 IP。保持该窗口打开。

在服务器上另开**管理员 PowerShell**，重新执行第 2 节以设置 `$ServerIp`、`$LanSubnet` 等变量，然后创建限定来源网段的规则：

```powershell
$RuleName = 'APProductDB-LAN-8000'
Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue |
    Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $RuleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8000 -RemoteAddress $LanSubnet -Profile Domain,Private,Public
```

此规则覆盖所有网络配置文件，但只允许指定网段。应确认所选网络受信任；已有其他宽泛放行规则仍可能允许额外访问，需一并检查。本机单独使用不需要此规则。

## 5. 从两端验证

在服务器浏览器访问 `http://127.0.0.1:8000/health/` 和第 2 节打印的实际地址。在**另一台电脑**浏览器打开服务器实际地址后的 `/accounts/login/`，确认页面样式和登录正常。不要在客户端使用 `localhost`、`127.0.0.1` 或 `0.0.0.0`。

客户端 PowerShell 还可执行：

```powershell
$ServerIp = Read-Host '请输入服务器的局域网 IPv4 地址（不是客户端自己的地址）'
Test-NetConnection -ComputerName $ServerIp -Port 8000
Invoke-RestMethod ("http://"+$ServerIp+":8000/health/")
```

健康检查应返回 `status=ok`、`database=ok`。服务器休眠、关机或前台终端关闭后服务会停止。

## 6. 可选：安装 Windows 自动运行

仅适用于 `D:\APProductDB\app` 源码布局、`D:\APProductDB` 数据根目录，且已完成首次初始化与验证的安装。没有此布局时使用前台运行，或先按恢复手册迁移。

安装脚本会覆盖同名任务/规则、调整数据及 `.env` 权限，并默认修改交流电源睡眠/合盖设置；同时安装价格抓取任务。了解这些影响后，在**管理员 PowerShell**进入 `D:\APProductDB\app`，先重新执行第 2 节获取真实网络参数，再执行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install_windows.ps1 -LanSubnet $LanSubnet -DailyBackupTime '23:00' -SkipPowerSettings
```

必须显式传入 `-LanSubnet`，不要依赖脚本内的旧默认网段。这里使用 `-SkipPowerSettings` 保留电源设置；如希望脚本禁用交流电源睡眠及合盖睡眠，可移除此参数。公司策略、BIOS 断电恢复开机需另行处理。

| 安装项 | 行为 |
| --- | --- |
| `APProductDB-Server` | 开机启动 Waitress，失败每 5 分钟重试，最多 3 次 |
| `APProductDB-Backup` | 每天指定时间运行备份，并检查价格抓取兜底 |
| `APProductDB-SyscomPrices` | 默认周日 02:00 抓取 SYSCOM 价格，依赖该功能所需账户配置及外网 |
| `APProductDB-HealthCheck` | 每 5 分钟检查健康状态，失败自动重启并验证 |
| `APProductDB-LAN-8000` | 仅放行指定来源网段的 TCP 8000 |

任务以执行安装的 Windows 账户运行，使用 S4U、最高权限；数据权限收紧为该账户、SYSTEM 与本机 Administrators。服务账户应能访问本地源码与数据。备份和抓价日志在 `runtime\logs` 下；价格任务使用 `syscom-prices.log`。仅浏览本地数据无需先配置外部价格同步或 Ollama；对应可选功能需要另外准备服务/账户。

关闭前台服务后启动任务：

```powershell
Start-ScheduledTask -TaskName APProductDB-Server
Get-ScheduledTaskInfo -TaskName APProductDB-Server
Invoke-RestMethod http://127.0.0.1:8000/health/
```

启动是异步的，如暂未就绪，稍后再验证并查看 `D:\APProductDB\runtime\logs\waitress-runtime.log`。长期运行任务的结果可能为“正在运行”，不能仅用结果是否为 0 判断 Web 服务是否正常。

日常操作：

```powershell
Get-ScheduledTask -TaskName APProductDB-*
.\scripts\restart_server.ps1
```

正式停机或恢复时，同时停止健康检查任务，防止自动拉起；具体见[恢复手册](RESTORE.md)。价格抓取任务可单独通过 `scripts\install_syscom_price_task.ps1 -DayOfWeek Sunday -At 02:00` 重新安装。

## 7. IP、网段或端口变化

- IP 变化：重新查地址，更新 `ALLOWED_HOSTS` 和 `CSRF_TRUSTED_ORIGINS`，重启服务，通知使用者更换访问地址。
- 网段变化：重新计算并核对 `$LanSubnet`，重建防火墙规则；自动运行布局可重跑安装命令，但会同时覆盖计划任务及权限。
- 换网络/换电脑：同时检查地址、路由、防火墙和数据路径；不要直接复用旧电脑 `.env`。
- 手工部署改端口：同步修改 Waitress 参数、CSRF 来源端口、防火墙端口与浏览器 URL。现有自动运行脚本、健康检查与规则围绕 8000 配套，不支持只改一处参数。

## 8. 排查与日常维护

| 现象 | 按顺序检查 |
| --- | --- |
| 本机也打不开 | 服务是否运行、8000 是否占用、启动窗口报错/日志、`.env` 与数据库权限 |
| 本机可用、其他电脑连接失败 | 是否监听 `0.0.0.0`、实际服务器 IP 是否变化、TCP 8000 规则与来源网段、Wi-Fi 客户端隔离/VPN/路由 |
| HTTP 400 / `DisallowedHost` | 访问使用的 IP/主机名是否在 `DJANGO_ALLOWED_HOSTS`，保存后是否重启 |
| HTTP 403 / CSRF 错误 | 协议、主机、端口是否匹配 CSRF 来源；HTTP 下是否误启用 Secure Cookie；检查服务日志 |
| 自动任务启动失败 | 实际目录、虚拟环境、安装账户权限、端口占用，查看 `waitress-runtime.log` |
| 更新后样式异常 | 重跑 `collectstatic --noinput` 并重启 |
| 备份未生成 | 计划任务历史、`logs` 下备份日志、可用空间和目录权限 |

每天检查健康接口、自动部署的 `logs\health-check.log` 与备份目录。每月至少执行一次隔离恢复测试；备份应另存到批准的存储，不能只保留在服务器同一块磁盘。具体命令见[备份与恢复](RESTORE.md)。
