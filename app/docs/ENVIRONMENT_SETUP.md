# 开发环境初始化记录

初始化日期：2026-07-18

## 安装结果

- 项目目录：`D:\APProductDB`
- 源码与虚拟环境：`D:\APProductDB\app`
- Python：3.13.9（64 位）
- Django：5.2.16（5.2 LTS）
- Git for Windows：2.53.0.windows.3
- 数据库：SQLite（Python/Django 内置支持）
- Excel：openpyxl 3.1.5
- Web Server：Waitress 3.0.2
- 静态文件：WhiteNoise 6.12.0
- 测试：pytest 8.4.2、pytest-django 4.12.0

## 目录

```text
D:\APProductDB\
├── app\              # Git 仓库、源码、.venv、规范和样例数据
├── data\             # SQLite 数据库（不放入 Git）
├── media\            # 上传附件
├── logs\             # 运行日志
├── backups\          # 数据库与附件备份
└── tools\Git\        # Git for Windows
```

## 使用方式

重新打开 PowerShell 或 VS Code 终端后执行：

```powershell
cd D:\APProductDB\app
.\.venv\Scripts\Activate.ps1
python --version
python -m pip check
git status
```

PowerShell 当前用户执行策略为 `RemoteSigned`，允许激活本地虚拟环境脚本。

## 输入材料

- `docs\DEVELOPMENT_SPEC.md`
- `import_samples\Wi-Fi_7_AP_Spec_Database_US.xlsx`

样例工作簿验证结果：3 张工作表、20 个产品、8 行对标映射（共 14 条竞品关系）、12 条字段定义。

## 下一步

按开发规格的“阶段 1：工程骨架”创建 Django 工程。当前初始化没有提前创建产品模型、Excel 导入业务或其他后续阶段功能。
