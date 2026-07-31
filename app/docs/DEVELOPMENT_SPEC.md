# Wi-Fi 7 AP 产品与竞品数据库——开发规格说明书

版本：1.0  
日期：2026-07-18  
项目阶段：内部 MVP  
目标读者：项目负责人、Codex、后续维护开发人员

---

## 1. 项目背景

本项目用于建立一个仅供子公司内部使用的无线产品与竞品知识库。第一阶段聚焦 Wi-Fi 7 无线接入点（AP），保存 TP-Link、Ubiquiti、Ruijie 和 Reyee 产品的核心规格及对标关系。

公司同事通过浏览器查询产品、查看对标关系和进行横向规格比较。如果发现数据错误，可以提交修改申请；正式数据只能由管理员审核后更新。

当前没有公司服务器、企业 SSO、云数据库或专职开发资源。全部设计、开发、测试和维护由项目负责人一人完成。服务器运行在一台几乎 24 小时在线的 Windows 办公电脑上，同事在工作时间通过同一局域网访问。

## 2. 已确认的项目约束

1. 服务器操作系统为 Windows。
2. 服务器与用户在工作时间处于同一局域网。
3. 不开放公网访问，不配置路由器端口转发。
4. 第一阶段仅供子公司内部使用。
5. 不接入企业 SSO。
6. 使用 Django 自带账号密码认证。
7. 项目负责人是唯一管理员和审核人。
8. 普通员工可以查询；编辑用户可以提交修改建议，但不能直接修改正式数据。
9. 第一阶段只支持 Wi-Fi 7 AP。
10. 第一批包含 20 个不同产品型号和 14 条已有对标关系。
11. 原始和后续批量数据主要通过 Excel 管理和导入。
12. 多国家或区域版本优先使用 US 版本；没有 US 页面时使用官方 Global 页面并明确标记。
13. 规格数据只采用厂商官方产品页或官方 datasheet。
14. 官网没有公开的参数不得猜测，应记录为缺失或 `Not Published`。
15. 数据库和附件必须自动备份。

## 3. MVP 目标

MVP 必须跑通以下闭环：

1. 管理员通过 Excel 导入产品、规格和对标关系。
2. 用户通过型号、品牌和核心参数查询产品。
3. 用户查看某个 TP-Link 产品对应的竞品。
4. 用户横向比较多个产品的核心规格。
5. 编辑用户提交参数纠错或新增建议。
6. 管理员查看修改前后差异及官方证据。
7. 管理员批准或拒绝申请。
8. 批准后正式数据更新，并保留操作记录。
9. 系统每天自动备份数据库和上传附件。

## 4. 第一阶段明确不做的内容

- 公网访问；
- 企业 SSO；
- 自助注册；
- 邮件找回密码；
- 多级审核；
- 自动网页爬虫；
- AI 自动提取规格；
- AI 自动推荐竞品；
- 价格和成本；
- 自动生成客户报价；
- React/Vue 前后端分离；
- REST API 对外开放；
- Docker、Kubernetes、Redis、Elasticsearch；
- 复杂统计报表；
- 其他产品品类；
- 多语言界面；
- 移动 App。

这些功能可以在 MVP 稳定后另行评估，不得在第一阶段提前引入复杂度。

---

## 5. 推荐技术栈

### 5.1 核心技术

| 模块 | 选型 | 说明 |
|---|---|---|
| 编程语言 | Python 3.12 或 3.13 | Windows 兼容、生态成熟 |
| Web 框架 | Django 5.2 LTS | 单体应用，自带 ORM、Admin、认证、表单和迁移 |
| 数据库 | SQLite | MVP 无需安装数据库服务，易于备份和迁移 |
| 页面渲染 | Django Templates | 不做前后端分离 |
| UI | Bootstrap 5.3 | 表格、表单、导航及响应式布局 |
| 动态交互 | HTMX，可选 | 用于局部搜索、筛选和审核操作；不强制使用 |
| Excel | openpyxl | 读取和生成 `.xlsx` 文件 |
| Web Server | Waitress | Windows 上运行 Django WSGI 应用 |
| 静态文件 | WhiteNoise | 简化内部部署时的静态文件服务 |
| 图片/附件 | Windows 本地目录 | 保存产品图片、datasheet 和证据附件 |
| 测试 | Django TestCase + pytest-django，可选 | 优先使用 Django 自带测试框架 |
| 浏览器测试 | Playwright，可选 | 只覆盖关键流程 |
| 代码版本 | Git | 所有源代码和迁移必须进入版本控制 |
| 自动任务 | Windows Task Scheduler | 开机启动、备份和健康检查 |

### 5.2 技术选型原则

- 保持单一 Django 工程，不拆分前端和后端。
- 优先使用 Django 内置能力，不重复实现用户、权限、表单和后台管理。
- 不为少量内部用户提前引入复杂基础设施。
- 数据模型必须允许未来迁移到 PostgreSQL，但 MVP 使用 SQLite。
- 业务逻辑不得只写在模板或 JavaScript 中，应放在 service、form 或 model 层。

---

## 6. 开发环境准备

### 6.1 Windows 软件

安装：

1. Git for Windows；
2. Python 3.12 或 3.13 64-bit；
3. VS Code；
4. VS Code Python 扩展；
5. 可选：DB Browser for SQLite；
6. 可选：Microsoft Edge 或 Chrome，用于测试。

安装 Python 时勾选 `Add Python to PATH`。

### 6.2 推荐工程路径

不要把运行中的项目和 SQLite 数据库放在 OneDrive 实时同步目录中。

建议路径：

```text
C:\APProductDB\
├── app\
├── data\
├── media\
├── logs\
└── backups\
```

其中：

- `app`：源代码；
- `data`：SQLite 数据库；
- `media`：上传附件和产品图片；
- `logs`：运行和错误日志；
- `backups`：备份副本。

### 6.3 Python 虚拟环境

```powershell
cd C:\APProductDB\app
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

建议初始依赖：

```text
Django>=5.2,<5.3
waitress>=3,<4
whitenoise>=6,<7
openpyxl>=3.1,<4
Pillow>=11,<12
python-dotenv>=1,<2
```

如果引入 pytest：

```text
pytest>=8,<9
pytest-django>=4,<5
```

所有依赖写入 `requirements.txt`，不得依赖开发电脑中的全局包。

### 6.4 环境变量

开发和生产配置使用 `.env`，不得把密钥提交到 Git。

```text
DJANGO_SECRET_KEY=<随机长字符串>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.100
DJANGO_CSRF_TRUSTED_ORIGINS=http://192.168.1.100:8000
DATABASE_PATH=C:\APProductDB\data\ap_products.sqlite3
MEDIA_ROOT=C:\APProductDB\media
LOG_DIR=C:\APProductDB\logs
BACKUP_DIR=C:\APProductDB\backups
```

`.env.example` 应提交到 Git，但不得包含真实密钥。

---

## 7. 建议项目结构

```text
ap-product-db/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── docs/
│   ├── DEVELOPMENT_SPEC.md
│   ├── DEPLOYMENT_WINDOWS.md
│   └── IMPORT_TEMPLATE.md
├── config/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── accounts/
│   ├── admin.py
│   ├── apps.py
│   ├── urls.py
│   └── views.py
├── catalog/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── services.py
│   ├── urls.py
│   ├── views.py
│   └── tests/
├── comparison/
│   ├── admin.py
│   ├── models.py
│   ├── services.py
│   ├── urls.py
│   ├── views.py
│   └── tests/
├── reviews/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── services.py
│   ├── urls.py
│   ├── views.py
│   └── tests/
├── imports/
│   ├── admin.py
│   ├── forms.py
│   ├── models.py
│   ├── services.py
│   ├── validators.py
│   ├── urls.py
│   ├── views.py
│   └── tests/
├── audit/
│   ├── admin.py
│   ├── models.py
│   └── services.py
├── templates/
│   ├── base.html
│   ├── registration/
│   ├── catalog/
│   ├── comparison/
│   ├── reviews/
│   └── imports/
├── static/
│   ├── css/
│   ├── js/
│   └── images/
└── scripts/
    ├── start_server.ps1
    ├── backup.ps1
    └── health_check.ps1
```

如果 MVP 开发初期希望进一步减少 app 数量，可以先合并 `audit` 到 `reviews`，但不得把所有模型和逻辑堆在一个文件中。

---

## 8. 用户与权限

### 8.1 用户角色

使用 Django `Group` 和权限系统，不创建自定义认证框架。

| 角色 | Django Group | 权限 |
|---|---|---|
| 查询用户 | Viewer | 查看已发布产品、规格、来源和对标关系 |
| 编辑用户 | Contributor | Viewer 权限 + 提交修改申请、查看本人申请 |
| 管理员 | Django superuser | 管理数据、导入 Excel、审核申请、管理用户 |

### 8.2 认证规则

- 不开放注册页面；
- 用户账号由管理员创建；
- 登录使用用户名和密码；
- 查询页面可以选择要求登录；MVP 推荐所有页面登录后访问；
- 用户无法进入 Django Admin，除非明确授予 staff 权限；
- 用户无法直接调用更新正式数据的视图；
- 管理员不得通过前端参数伪造申请人或审核人。

---

## 9. 数据模型

所有主键建议使用 Django 默认 `BigAutoField`。所有正式业务模型包含 `created_at` 和 `updated_at`。

### 9.1 Brand

```text
name                 CharField(unique=True)
slug                 SlugField(unique=True)
is_own_brand         BooleanField(default=False)
official_website     URLField(blank=True)
active               BooleanField(default=True)
created_at           DateTimeField(auto_now_add=True)
updated_at           DateTimeField(auto_now=True)
```

初始品牌：

- TP-Link；
- Ubiquiti；
- Ruijie；
- Reyee。

Ruijie 和 Reyee 必须作为不同品牌记录。

### 9.2 Category

```text
name                 CharField(unique=True)
slug                 SlugField(unique=True)
parent               ForeignKey(self, null=True, blank=True)
active               BooleanField(default=True)
```

MVP 至少包含：

```text
Wireless
└── Access Point
```

### 9.3 Product

```text
brand                ForeignKey(Brand, PROTECT)
category             ForeignKey(Category, PROTECT)
model                CharField
model_key            CharField(db_index=True)
region               CharField(default="US")
hardware_version     CharField(blank=True)
ap_type              CharField(choices=AP_TYPE_CHOICES)
wifi_standard        CharField(default="Wi-Fi 7")
lifecycle_status     CharField(choices=LIFECYCLE_CHOICES, default="unknown")
official_url         URLField(blank=True)
image                ImageField(blank=True)
notes                TextField(blank=True)
is_published         BooleanField(default=True)
created_by           ForeignKey(User, null=True, SET_NULL, related_name="products_created")
updated_by           ForeignKey(User, null=True, SET_NULL, related_name="products_updated")
created_at           DateTimeField(auto_now_add=True)
updated_at           DateTimeField(auto_now=True)
```

约束：

```text
UniqueConstraint(brand, model_key, region, hardware_version)
```

`model_key` 用于规范搜索，例如移除空格和连字符并转换为大写：

```text
U7-Pro-Outdoor -> U7PROOUTDOOR
```

不得使用 `model` 作为数据库主键。

AP 类型：

```text
ceiling
wall
wall_plate
outdoor
other
```

### 9.4 SpecDefinition

定义系统支持的标准规格字段。

```text
code                 SlugField(unique=True)
display_name         CharField
group                CharField
data_type            CharField(choices=text/integer/decimal/boolean/choice)
unit                 CharField(blank=True)
is_filterable        BooleanField(default=False)
is_core              BooleanField(default=True)
display_order        PositiveIntegerField(default=0)
description          TextField(blank=True)
active               BooleanField(default=True)
```

第一阶段参数定义：

```text
supported_bands
total_spatial_streams
mimo_2g
mimo_5g
mimo_6g
rate_2g_mbps
rate_5g_mbps
rate_6g_mbps
max_channel_width_mhz
ethernet_interfaces
poe_input
poe_output
max_clients
ip_rating
```

`wifi_standard` 和 `ap_type` 保存在 Product 中，因为它们是所有产品的基础属性；其余可变规格保存在 ProductSpec 中。

### 9.5 ProductSpec

```text
product              ForeignKey(Product, CASCADE, related_name="specs")
definition           ForeignKey(SpecDefinition, PROTECT)
value_text           TextField(blank=True)
value_number         DecimalField(null=True, blank=True, max_digits=14, decimal_places=3)
raw_value            TextField(blank=True)
source_url           URLField(blank=True)
source_note          TextField(blank=True)
verified_date        DateField(null=True, blank=True)
updated_by           ForeignKey(User, null=True, SET_NULL)
created_at           DateTimeField(auto_now_add=True)
updated_at           DateTimeField(auto_now=True)
```

约束：

```text
UniqueConstraint(product, definition)
```

写入规则：

- 数字规格写入 `value_number`；
- 文本、枚举和组合端口写入 `value_text`；
- `raw_value` 保存官方原始表达；
- 没有 6 GHz Radio 时，对应数值为空，不写 0；
- 官网未公开时可以在文本字段记录 `Not Published`，数字字段保持为空；
- 每个核心参数尽量保存自己的来源 URL；若同一产品全部参数来自同一页面，可使用 Product 的 official_url 作为默认来源。

### 9.6 ProductMatch

```text
our_product          ForeignKey(Product, PROTECT, related_name="competitor_matches")
competitor_product   ForeignKey(Product, PROTECT, related_name="matched_as_competitor")
match_type           CharField(choices=direct/performance/price/function/candidate)
status               CharField(choices=candidate/confirmed/rejected, default="candidate")
region               CharField(default="US")
match_score          PositiveSmallIntegerField(null=True, blank=True)
reason               TextField(blank=True)
advantages           TextField(blank=True)
disadvantages        TextField(blank=True)
source_url           URLField(blank=True)
created_by           ForeignKey(User, null=True, SET_NULL, related_name="matches_created")
updated_by           ForeignKey(User, null=True, SET_NULL, related_name="matches_updated")
created_at           DateTimeField(auto_now_add=True)
updated_at           DateTimeField(auto_now=True)
```

约束：

```text
UniqueConstraint(our_product, competitor_product, region)
CheckConstraint(our_product != competitor_product)
```

MVP 中 `our_product` 必须是 TP-Link 产品。一个竞品可以同时对应多个 TP-Link 型号。

### 9.7 ChangeRequest

```text
request_type         CharField(choices=product/spec/match)
target_product       ForeignKey(Product, null=True, blank=True, PROTECT)
target_spec          ForeignKey(ProductSpec, null=True, blank=True, PROTECT)
target_match         ForeignKey(ProductMatch, null=True, blank=True, PROTECT)
field_name           CharField
old_value            JSONField(default=dict)
proposed_value       JSONField(default=dict)
reason               TextField
source_url           URLField(blank=True)
attachment           FileField(blank=True)
status               CharField(choices=pending/approved/rejected, default="pending")
submitted_by         ForeignKey(User, PROTECT, related_name="change_requests")
submitted_at         DateTimeField(auto_now_add=True)
reviewed_by          ForeignKey(User, null=True, blank=True, SET_NULL, related_name="reviewed_changes")
reviewed_at          DateTimeField(null=True, blank=True)
review_comment       TextField(blank=True)
```

MVP 一条 ChangeRequest 只修改一个逻辑字段，降低审核和回滚难度。

### 9.8 AuditLog

```text
actor                ForeignKey(User, null=True, SET_NULL)
action               CharField
object_type          CharField
object_id            CharField
object_repr          CharField
before_data          JSONField(default=dict)
after_data           JSONField(default=dict)
created_at           DateTimeField(auto_now_add=True)
ip_address           GenericIPAddressField(null=True, blank=True)
```

至少记录：

- Excel 导入；
- 新增、更新、停用产品；
- 新增或更新规格；
- 新增或更新对标关系；
- 批准或拒绝修改申请；
- 用户和权限管理可以使用 Django Admin log。

### 9.9 ImportJob

```text
uploaded_file        FileField
status               CharField(choices=uploaded/validating/invalid/ready/imported/failed)
total_rows           PositiveIntegerField(default=0)
valid_rows           PositiveIntegerField(default=0)
error_rows           PositiveIntegerField(default=0)
error_report         FileField(blank=True)
summary              JSONField(default=dict)
uploaded_by          ForeignKey(User, PROTECT)
uploaded_at          DateTimeField(auto_now_add=True)
imported_at          DateTimeField(null=True, blank=True)
```

---

## 10. Excel 数据格式

当前标准数据文件：

```text
Wi-Fi_7_AP_Spec_Database_US.xlsx
```

包含：

1. `Spec Data`；
2. `Match Map`；
3. `Field Definitions`。

### 10.1 Spec Data 导入字段

```text
Brand
Model
Region / HW Version
AP Type
Wi-Fi Standard
Supported Wireless Bands
Total Spatial Streams
2.4 GHz MIMO
5 GHz MIMO
6 GHz MIMO
2.4 GHz Max Rate (Mbps)
5 GHz Max Rate (Mbps)
6 GHz Max Rate (Mbps)
Aggregate Rate (Mbps)
Max Channel Width (MHz)
Ethernet Interfaces
PoE Input
PoE Output
Max Clients
IP Rating
Official Source
Last Verified
Data Notes
```

`Aggregate Rate` 为派生值。导入时不要信任 Excel 的静态值，应在系统内用三个频段速率重新计算。

### 10.2 Match Map 导入字段

```text
TP-Link Model
Competitor Brand 1
Competitor Model 1
Competitor Brand 2
Competitor Model 2
```

导入时将一行转换成最多两条 ProductMatch。

### 10.3 导入流程

必须采用两阶段导入：

```text
上传文件 -> 校验 -> 显示预览和错误 -> 管理员确认 -> 数据库事务导入
```

上传文件后不得立即覆盖正式数据库。

### 10.4 校验规则

至少检查：

- 工作表是否存在；
- 必需列是否存在；
- 品牌和型号是否为空；
- 品牌是否在 Brand 中；
- AP Type 是否为允许值；
- Wi-Fi Standard 是否为允许值；
- 空间流和速率是否为非负数字；
- 支持频段与各频段速率是否矛盾；
- `2.4 / 5 GHz` 产品不得填写 6 GHz Rate；
- `2.4 / 5 / 6 GHz` 产品原则上应有三个 MIMO 字段；
- URL 格式是否正确；
- 日期是否可解析；
- 品牌 + 型号 + 区域 + 硬件版本是否重复；
- Match Map 中引用的型号是否存在；
- TP-Link 型号不得被识别成 competitor_product；
- ProductMatch 不得指向自身；
- 同一关系不得重复。

错误报告必须包含：

```text
Sheet Name
Row Number
Column Name
Original Value
Error Code
Human-readable Message
```

### 10.5 更新策略

导入页面必须让管理员选择：

- `Create only`：已有产品报错；
- `Create and update`：新产品创建，已有产品更新；
- `Preview only`：只校验，不写数据库。

默认使用 `Preview only`。

所有正式写入必须在 `transaction.atomic()` 中完成。任何严重错误都应回滚整个批次。

---

## 11. 页面和功能

### 11.1 登录页

- 用户名和密码；
- 登录失败提示；
- 不显示注册入口；
- 登录成功后跳转到首页；
- 支持退出登录。

### 11.2 首页

包含：

- 全局型号搜索框；
- 快捷入口：产品查询、竞品对标、产品比较、提交修改；
- 产品总数；
- TP-Link/竞品数量；
- 最近更新产品；
- 当前用户自己的待处理修改数量；
- 管理员额外显示全站待审核数量。

### 11.3 产品列表

支持：

- 分页，每页默认 25 条；
- 按品牌筛选；
- 按 AP Type 筛选；
- 按支持频段筛选；
- 按空间流筛选；
- 按 LAN 速率筛选；
- 按型号关键字搜索；
- 默认按品牌、型号排序；
- 可选择多个产品加入比较。

搜索应忽略型号中的大小写、空格和连字符。

### 11.4 产品详情

展示：

- 品牌、型号、区域和硬件版本；
- AP Type；
- 官方页面；
- 所有核心规格；
- 各字段来源和验证日期；
- Aggregate Rate；
- 当前对标关系；
- 最后更新时间；
- “提交修改建议”按钮。

数字为 0 与缺失必须有不同显示：

- 不支持的频段显示 `Not Applicable`；
- 官方未公开显示 `Not Published`；
- 未收集显示 `Unknown`；
- 不得统一显示为 `-`。

### 11.5 TP-Link 对标页面

用户选择一个 TP-Link 型号后显示所有竞品：

- 竞品品牌和型号；
- Match Type；
- Status；
- Match Score；
- 对标理由；
- 优势和劣势；
- 查看规格比较按钮。

### 11.6 横向比较页面

要求：

- 同时比较 2–4 个产品；
- 以规格字段为行，以产品为列；
- 默认显示核心字段；
- 支持“只显示差异”；
- 支持“显示来源”；
- 区分数值缺失和不支持；
- 提供清除产品和更换产品功能；
- 支持导出当前比较结果为 Excel。

默认比较字段：

```text
AP Type
Wi-Fi Standard
Supported Wireless Bands
Total Spatial Streams
MIMO by Band
2.4 GHz Max Rate
5 GHz Max Rate
6 GHz Max Rate
Aggregate Rate
Max Channel Width
Ethernet Interfaces
PoE Input
PoE Output
Max Clients
IP Rating
```

不得自动把某一列标记成“绝对更优”，因为端口、PoE、客户端和防护等级的价值取决于场景。MVP 只做差异高亮。

### 11.7 修改申请页面

Contributor 可以：

- 从产品详情页选择要修改的字段；
- 查看当前值；
- 输入建议值；
- 填写修改原因；
- 填写官方来源 URL；
- 上传 PDF、PNG、JPG 或 XLSX 证据；
- 提交申请；
- 查看本人申请状态。

校验：

- 原因必填；
- 新值不得和旧值完全相同；
- 核心规格原则上要求来源 URL 或附件；
- 附件必须限制扩展名和大小；建议最大 10 MB；
- 普通文件名必须被安全处理，不能作为服务器路径直接使用。

### 11.8 审核页面

仅管理员访问。

列表支持：

- Pending/Approved/Rejected 筛选；
- 按提交人筛选；
- 按产品筛选；
- 按提交时间排序。

详情必须显示：

- 产品；
- 字段名称；
- 当前正式值；
- 提交时旧值；
- 建议值；
- 修改原因；
- 来源和附件；
- 提交人和时间。

批准时：

1. 重新检查当前正式值是否仍等于申请中的 old_value；
2. 如果正式值已变化，提示冲突，禁止静默覆盖；
3. 在数据库事务内更新正式数据；
4. 写入 AuditLog；
5. 更新 ChangeRequest 状态；
6. 记录审核人和审核时间。

拒绝时必须填写审核意见。

### 11.9 Excel 导入页面

仅管理员访问。

步骤：

1. 上传 `.xlsx`；
2. 选择 Preview/Create only/Create and update；
3. 后台校验；
4. 展示统计和前若干条预览；
5. 提供错误报告下载；
6. 管理员确认导入；
7. 展示导入结果。

上传的原文件应保留在 ImportJob 中，以便审计。

### 11.10 Django Admin

使用 Admin 管理：

- 用户和 Group；
- Brand；
- Category；
- Product；
- SpecDefinition；
- ProductSpec；
- ProductMatch；
- ChangeRequest；
- ImportJob；
- AuditLog 只读。

Admin 列表应提供搜索、筛选和合理的 `list_display`，不得直接暴露难以阅读的 JSON。

---

## 12. URL 规划

```text
/
/accounts/login/
/accounts/logout/
/products/
/products/<int:pk>/
/products/<int:pk>/suggest-change/
/matches/
/matches/<int:our_product_id>/
/compare/
/compare/export/
/changes/
/changes/mine/
/changes/<int:pk>/
/reviews/
/reviews/<int:pk>/approve/
/reviews/<int:pk>/reject/
/imports/
/imports/new/
/imports/<int:pk>/
/imports/<int:pk>/confirm/
/imports/<int:pk>/errors/
/admin/
/health/
```

`/health/` 返回简单 JSON，用于本机健康检查：

```json
{"status":"ok","database":"ok"}
```

不得包含密钥、路径或服务器详细信息。

---

## 13. 搜索、筛选与性能

MVP 使用 SQLite 和 Django ORM。

建议索引：

- Product.model；
- Product.model_key；
- Product.brand；
- Product.ap_type；
- Product.region；
- ProductMatch.our_product；
- ProductMatch.competitor_product；
- ChangeRequest.status；
- ChangeRequest.submitted_by；
- AuditLog.created_at。

避免 N+1 查询：

- 产品列表使用 `select_related("brand", "category")`；
- 产品详情按需 `prefetch_related("specs__definition")`；
- 对标页面预取 competitor_product 和其 specs。

所有列表必须分页，不允许一次返回无限数据。

---

## 14. 安全要求

虽然只在局域网使用，仍需满足：

- `DEBUG=False`；
- 设置强随机 `SECRET_KEY`；
- 设置明确 `ALLOWED_HOSTS`；
- 所有 POST 操作启用 CSRF；
- 使用 Django ORM，禁止字符串拼接 SQL；
- 修改和审核视图必须检查登录及权限；
- 文件上传限制类型和大小；
- 上传文件名随机化；
- 不允许执行上传文件；
- 日志中不得记录密码和 session cookie；
- Admin 使用强密码；
- 默认不创建共享管理员账号；
- Windows 防火墙仅允许局域网访问服务端口；
- 不做公网端口映射；
- 如果未来跨地点访问，必须使用公司批准的 VPN，不直接暴露 Waitress。

MVP 可以先使用 HTTP，因为限定在可信局域网。如果公司政策要求加密，应增加 Caddy 或 IIS 反向代理提供 HTTPS，而不是由 Waitress 直接处理证书。

---

## 15. 日志

建议日志文件：

```text
application.log
error.log
waitress.log
backup.log
```

使用 RotatingFileHandler：

- 单文件最大 10 MB；
- 保留 10 个历史文件；
- 应用日志 INFO；
- Django request 错误日志 ERROR；
- 不记录登录密码、完整 cookie 和附件内容。

关键业务操作额外写入 AuditLog，不能只依赖文本日志。

---

## 16. Windows 部署

### 16.1 网络

- 为办公电脑设置 DHCP Reservation 或固定局域网 IP；
- 示例地址：`192.168.1.100`；
- 同事通过 `http://192.168.1.100:8000` 访问；
- Windows 防火墙只允许公司局域网网段访问 TCP 8000；
- 不开放到公网。

### 16.2 Django 生产配置

```powershell
cd C:\APProductDB\app
.\.venv\Scripts\Activate.ps1
python manage.py check --deploy
python manage.py migrate
python manage.py collectstatic --noinput
waitress-serve --listen=0.0.0.0:8000 config.wsgi:application
```

不要使用 `python manage.py runserver` 作为正式服务。

### 16.3 启动脚本

`scripts/start_server.ps1` 应：

1. 切换到项目目录；
2. 激活虚拟环境或直接调用虚拟环境 Python；
3. 创建日志目录；
4. 启动 Waitress；
5. 把 stdout/stderr 写入日志；
6. 返回非零退出码时留下错误记录。

### 16.4 Windows Task Scheduler

创建任务：

1. `APProductDB-Server`
   - 触发：电脑启动时；
   - 操作：执行 start_server.ps1；
   - 用户未登录时也运行；
   - 失败后每 5 分钟重试，最多 3 次。
2. `APProductDB-Backup`
   - 触发：每天固定时间；
   - 操作：执行 backup.ps1。
3. `APProductDB-HealthCheck`
   - 触发：每 15 分钟；
   - 请求 `/health/`；
   - 失败时写日志；MVP 不强制自动重启。

### 16.5 电源设置

- 接通电源时不自动睡眠；
- 笔记本合盖不睡眠；
- 优先使用有线网络；
- Windows 更新重启后服务应自动启动；
- 如公司允许，配置 BIOS 断电恢复后自动开机。

---

## 17. SQLite 与备份

### 17.1 SQLite 配置

- 数据库文件放在 `C:\APProductDB\data`；
- 不放在 Git；
- 不让 OneDrive 直接同步运行中的数据库；
- 可启用合理的 SQLite timeout；
- 不把长时间任务放在事务中；
- Excel 导入事务应尽可能短。

### 17.2 备份内容

每天备份：

- SQLite 数据库；
- `media` 附件目录；
- `.env` 的安全副本；
- 当前应用版本信息；
- 可选：导入原文件。

### 17.3 备份方法

不得直接复制正在写入的 SQLite 文件作为唯一备份方式。优先使用 SQLite backup API 或 Django 管理命令生成一致性副本。

建议实现：

```text
python manage.py backup_database --output <path>
```

备份目录：

```text
C:\APProductDB\backups\2026-07-18_230000\
├── ap_products.sqlite3
├── media.zip
├── environment.txt
└── manifest.json
```

保留策略：

- 最近 30 个日备份；
- 最近 12 个周备份；
- 删除旧备份前先确认至少存在一个有效最新备份；
- 每月进行一次恢复测试。

最好再把生成后的备份副本复制到另一块磁盘或公司允许的安全存储位置。

### 17.4 恢复文档

必须编写 `docs/RESTORE.md`，包含：

1. 停止 Waitress；
2. 备份当前损坏数据；
3. 恢复 SQLite 文件；
4. 恢复 media；
5. 运行数据库检查；
6. 启动应用；
7. 登录并抽查产品和附件。

---

## 18. 测试要求

### 18.1 模型测试

- Product 唯一约束；
- model_key 规范化；
- ProductMatch 不能指向自身；
- ProductSpec 同一产品同一参数不能重复；
- 数字值和文本值的保存规则；
- ChangeRequest 状态转换；
- 审批后 AuditLog 生成。

### 18.2 权限测试

- 未登录用户无法访问业务页面；
- Viewer 无法提交修改；
- Contributor 可以提交但不能审核；
- Contributor 不能直接修改 ProductSpec；
- 普通用户不能访问导入页面；
- 只有管理员可以批准或拒绝；
- 用户不能修改他人的申请内容。

### 18.3 Excel 导入测试

- 正常文件预览成功；
- 缺工作表；
- 缺必需列；
- 重复产品；
- 非数字速率；
- 无效 URL；
- 不存在的竞品型号；
- 自对标；
- 重复对标；
- Create only 遇到已有产品；
- Create and update 正确更新；
- 任何严重错误时事务回滚；
- 错误报告行号正确。

### 18.4 页面测试

- 型号模糊搜索；
- 忽略空格、大小写和连字符；
- 品牌和 AP Type 筛选；
- 产品详情显示缺失状态；
- 2–4 产品比较；
- 只显示差异；
- 导出比较结果；
- 提交修改；
- 审核冲突检测；
- 批准和拒绝流程。

### 18.5 备份测试

- 在线数据库可生成一致备份；
- 附件包含在备份内；
- 备份 manifest 正确；
- 可在临时目录恢复并启动测试实例。

---

## 19. MVP 验收标准

满足以下全部条件才算完成：

1. Windows 重启后网站可自动启动；
2. 同一局域网的同事可以通过浏览器登录；
3. 标准 Excel 可先预览再导入；
4. 20 个首批产品全部导入；
5. 14 条对标关系全部导入；
6. 产品列表可搜索和筛选；
7. 产品详情显示核心规格、支持频段和来源；
8. 可同时比较 2–4 个产品；
9. Viewer、Contributor 和管理员权限符合设计；
10. Contributor 可提交修改；
11. 管理员可批准或拒绝；
12. 批准后正式数据更新；
13. 修改和导入操作有审计记录；
14. 每天自动备份数据库和附件；
15. 已实际完成一次备份恢复测试；
16. `python manage.py check --deploy` 无严重问题；
17. 自动测试通过；
18. 没有已知的数据破坏或越权漏洞。

---

## 20. 推荐开发阶段

### 阶段 1：工程骨架

- 创建 Git 仓库；
- 创建 Django 工程；
- 环境变量配置；
- 日志配置；
- 基础模板和 Bootstrap；
- 登录、退出及 Group；
- `/health/`；
- 基础测试框架。

完成标准：可以登录并访问空首页。

### 阶段 2：产品数据库和 Admin

- Brand、Category、Product；
- SpecDefinition、ProductSpec；
- ProductMatch；
- migrations；
- Admin 搜索、筛选和编辑；
- 初始化品牌、品类和字段定义的数据迁移或 management command。

完成标准：管理员可以在 Admin 手工创建一个完整产品和对标关系。

### 阶段 3：Excel 导入

- ImportJob；
- 上传和校验；
- 错误报告；
- Preview/Create only/Create and update；
- transaction.atomic；
- 导入审计日志；
- 导入测试。

完成标准：标准 Excel 中的20个产品和14条关系可无错误导入。

### 阶段 4：查询和详情

- 首页；
- 产品列表；
- 搜索和筛选；
- 产品详情；
- 来源显示；
- 权限控制。

完成标准：用户可在30秒内找到指定型号并查看完整核心规格。

### 阶段 5：对标和比较

- TP-Link 产品对标页面；
- 2–4产品比较；
- 只显示差异；
- 导出比较 Excel。

完成标准：用户可从 EAP772 一键进入 U7-Pro 和 RG-AP7136-R 比较。

### 阶段 6：修改和审核

- ChangeRequest；
- Contributor 提交；
- 我的申请；
- 管理员审核；
- 冲突检查；
- AuditLog。

完成标准：纠错可以完整闭环且普通用户不能绕过审核。

### 阶段 7：部署和备份

- Waitress；
- WhiteNoise；
- Windows 防火墙；
- Task Scheduler；
- 自动备份；
- 恢复测试；
- 部署文档。

完成标准：电脑重启后服务恢复，同事可访问，备份可恢复。

---

## 21. Codex 实施规则

Codex 开发时应遵循：

1. 每次只实现一个明确阶段或一个可验证功能。
2. 修改前先读取现有代码、迁移和测试。
3. 不删除或重建用户已有数据。
4. 模型变化必须生成 Django migration。
5. 每次功能修改同步增加或更新测试。
6. 完成后运行相关测试，不只检查页面是否能打开。
7. 不引入 React、Docker、PostgreSQL 等未批准技术。
8. 不把业务规则硬编码在模板中。
9. 不在代码中写真实路径、密码和 Secret Key。
10. 导入、审批和批量更新必须使用数据库事务。
11. 所有正式数据更新必须能够追踪操作者。
12. 不从非官方来源自动补充规格。
13. 遇到官网缺失数据时保存为空或 Not Published，不进行推测。
14. Region/HW Version 不得在导入时丢失。
15. 完成一个阶段后更新 README 和对应文档。

建议给 Codex 的首个任务：

```text
请阅读 DEVELOPMENT_SPEC.md，并只实施“阶段1：工程骨架”。
使用 Python 3.12、Django 5.2 LTS、Django Templates 和 Bootstrap 5.3。
创建可运行的工程、环境变量配置、登录/退出、Viewer 和 Contributor Group 初始化、基础首页、/health/、日志配置和自动测试。
不要提前实现产品模型、Excel导入或其他阶段。
完成后运行测试和 Django system check，并汇报创建的文件、启动方式和测试结果。
```

后续每个阶段单独下达任务，先验收再继续。

---

## 22. 未来扩展方向

MVP 稳定后可按优先级考虑：

1. 增加 Wi-Fi 6 AP；
2. 增加 Switch、Gateway 和其他品类；
3. 自动提醒长期未验证的数据；
4. 从官方页面辅助抓取变更，但必须人工审核；
5. 对标关系评分；
6. 更完善的版本历史；
7. PostgreSQL；
8. 企业 SSO；
9. 内部 HTTPS 域名；
10. 价格监控与现有产品数据库联动。

迁移到 PostgreSQL 的建议触发条件：

- 经常出现 SQLite locked 错误；
- 写入用户数量明显增加；
- 需要在不同服务器上运行；
- 需要复杂全文搜索；
- 需要更高可用性和集中备份。

---

## 23. 当前首批数据

### TP-Link

- EAP787
- EAP773
- EAP772
- EAP723
- EAP725-Wall
- EAP725-Outdoor
- EAP772-Outdoor
- EAP775-Wall

### Ubiquiti

- U7-Pro-XGS
- U7-Pro
- U7-Lite
- U7-IW
- U7-Outdoor
- U7-Pro-Outdoor
- U7-Pro-Wall

### Ruijie/Reyee

- RG-RAP73Pro
- RG-AP7136-R
- RG-RAP72Pro
- RG-RAP72-Wall
- RG-RAP72Pro-OD

完整数据、官方来源和字段说明位于 `Wi-Fi_7_AP_Spec_Database_US.xlsx`。

---

## 24. 最终交付清单

MVP 最终至少应包含：

```text
源代码 Git 仓库
requirements.txt
.env.example
数据库 migrations
初始化基础数据命令
标准 Excel 导入功能
标准 Excel 示例文件
自动测试
Windows 启动脚本
Windows 备份脚本
部署文档
恢复文档
用户使用说明
管理员操作说明
```

本规格说明书是 MVP 的需求基线。任何会明显扩大范围、引入新基础设施或改变数据结构的需求，应先更新本文档再实施。
