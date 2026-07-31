from dataclasses import dataclass
from pathlib import Path

from django.conf import settings

from catalog.product_types import PRODUCT_TYPE_DEFINITIONS
from catalog.spec_templates import SPEC_DEFINITIONS, TEMPLATES

SCHEMA_VERSION = "2"

BASE_FIELDS = (
    {
        "code": "brand",
        "display_name": "品牌",
        "group": "Identity",
        "data_type": "text",
        "unit": "",
        "required": True,
        "description": "已在系统中配置的品牌名称。",
    },
    {
        "code": "model",
        "display_name": "型号",
        "group": "Identity",
        "data_type": "text",
        "unit": "",
        "required": True,
        "description": "厂商正式型号。",
    },
    {
        "code": "region",
        "display_name": "区域",
        "group": "Identity",
        "data_type": "text",
        "unit": "",
        "required": True,
        "description": "销售区域，例如 Global、US、EU、CN。",
    },
    {
        "code": "hardware_version",
        "display_name": "硬件版本",
        "group": "Identity",
        "data_type": "text",
        "unit": "",
        "required": False,
        "description": "硬件版本；没有时留空。",
    },
    {
        "code": "lifecycle_status",
        "display_name": "生命周期",
        "group": "Classification",
        "data_type": "choice",
        "unit": "",
        "required": False,
        "description": "unknown、active、announced 或 discontinued。",
    },
    {
        "code": "official_url",
        "display_name": "产品页",
        "group": "Source",
        "data_type": "url",
        "unit": "",
        "required": False,
        "description": "厂商官方产品页面 URL。",
    },
    {
        "code": "datasheet_url",
        "display_name": "数据表",
        "group": "Source",
        "data_type": "url",
        "unit": "",
        "required": False,
        "description": "官方 Datasheet URL。",
    },
    {
        "code": "launch_date",
        "display_name": "上市日期",
        "group": "Source",
        "data_type": "date",
        "unit": "",
        "required": False,
        "description": "YYYY-MM-DD。",
    },
    {
        "code": "last_verified",
        "display_name": "最后核实日期",
        "group": "Source",
        "data_type": "date",
        "unit": "",
        "required": False,
        "description": "本行规格最后核实日期，YYYY-MM-DD。",
    },
    {
        "code": "data_notes",
        "display_name": "数据备注",
        "group": "Source",
        "data_type": "text",
        "unit": "",
        "required": False,
        "description": "来源、口径或待核实事项。",
    },
)


@dataclass(frozen=True)
class ImportTemplateProfile:
    category_slug: str
    category_name: str
    product_type_code: str
    product_type_name: str
    description: str
    fields: tuple

    @property
    def key(self):
        return f"{self.category_slug}--{self.product_type_code}"

    @property
    def filename(self):
        return f"{self.key}.xlsx"

    @property
    def path(self):
        return Path(settings.BASE_DIR) / "import_templates" / "by_product_type" / self.filename


CATEGORY_NAMES = {
    "access-point": "Access Point",
    "managed-switches": "Managed Switch",
    "unmanaged-easy-smart-switches": "Unmanaged / Easy Smart Switch",
    "gateway": "Router / Gateway",
    "accessories": "Accessories",
}


def _template_for(category_slug, product_type_code):
    exact = next(
        (
            template
            for template in TEMPLATES
            if template["category_slug"] == category_slug
            and template["form_factor"] == product_type_code
        ),
        None,
    )
    if exact:
        return exact
    return next(
        template
        for template in TEMPLATES
        if template["category_slug"] == category_slug and not template["form_factor"]
    )


def _deduplicated_codes(template):
    return tuple(dict.fromkeys(code for code, _priority in template["fields"]))


def iter_template_profiles():
    for category_slug, product_types in PRODUCT_TYPE_DEFINITIONS.items():
        for code, name, type_description in product_types:
            template = _template_for(category_slug, code)
            spec_fields = []
            for spec_code in _deduplicated_codes(template):
                definition = SPEC_DEFINITIONS[spec_code]
                spec_fields.append(
                    {
                        "code": spec_code,
                        "display_name": definition["display_name"],
                        "group": definition["group"],
                        "data_type": definition["data_type"],
                        "unit": definition["unit"],
                        "required": False,
                        "description": definition["description"],
                    }
                )
            yield ImportTemplateProfile(
                category_slug=category_slug,
                category_name=CATEGORY_NAMES[category_slug],
                product_type_code=code,
                product_type_name=name,
                description=type_description,
                fields=tuple(BASE_FIELDS) + tuple(spec_fields),
            )


def get_template_profile(category_slug, product_type_code):
    return next(
        (
            profile
            for profile in iter_template_profiles()
            if profile.category_slug == category_slug
            and profile.product_type_code == product_type_code
        ),
        None,
    )
