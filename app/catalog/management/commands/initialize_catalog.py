from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import (
    Brand,
    Category,
    ComparisonTemplate,
    ProductType,
    SpecDefinition,
    TemplateField,
)
from catalog.product_types import PRODUCT_TYPE_DEFINITIONS
from catalog.spec_templates import SPEC_DEFINITIONS, TEMPLATES

BRANDS = (
    {"name": "TP-Link", "slug": "tp-link", "is_own_brand": True},
    {"name": "Ubiquiti", "slug": "ubiquiti", "is_own_brand": False},
    {"name": "Ruijie", "slug": "ruijie", "is_own_brand": False},
    {"name": "Reyee", "slug": "reyee", "is_own_brand": False},
)

CATEGORY_TREE = (
    ("Wireless", "wireless", None),
    ("Access Point", "access-point", "wireless"),
    ("Wireless Bridge", "wireless-bridge", "wireless"),
    ("Routing", "routing", None),
    ("Gateway", "gateway", "routing"),
    ("Switching", "switching", None),
    ("Managed Switch", "managed-switches", "switching"),
    ("Unmanaged / Easy Smart Switch", "unmanaged-easy-smart-switches", "switching"),
    ("Accessories", "accessories", None),
)


class Command(BaseCommand):
    help = "Create or update product categories, specification definitions, and type-specific templates."

    @transaction.atomic
    def handle(self, *args, **options):
        for data in BRANDS:
            Brand.objects.update_or_create(
                name=data["name"],
                defaults={**data, "active": True},
            )

        categories = {}
        for name, slug, parent_slug in CATEGORY_TREE:
            category, _ = Category.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "parent": categories.get(parent_slug),
                    "active": True,
                },
            )
            categories[slug] = category

        active_product_type_ids = []
        for category_slug, product_types in PRODUCT_TYPE_DEFINITIONS.items():
            category = categories[category_slug]
            for order, (code, name, description) in enumerate(product_types, start=1):
                product_type, _ = ProductType.objects.update_or_create(
                    category=category,
                    code=code,
                    defaults={
                        "name": name,
                        "description": description,
                        "display_order": order * 10,
                        "active": True,
                    },
                )
                active_product_type_ids.append(product_type.pk)
        ProductType.objects.filter(
            category__slug__in=PRODUCT_TYPE_DEFINITIONS,
        ).exclude(pk__in=active_product_type_ids).update(active=False)

        definitions = {}
        for order, (code, metadata) in enumerate(SPEC_DEFINITIONS.items(), start=1):
            category = categories.get(metadata["category_slug"])
            definition, _ = SpecDefinition.objects.update_or_create(
                code=code,
                defaults={
                    "display_name": metadata["display_name"],
                    "group": metadata["group"],
                    "category": category,
                    "data_type": metadata["data_type"],
                    "unit": metadata["unit"],
                    "is_filterable": metadata["is_filterable"],
                    "is_core": True,
                    "display_order": order * 10,
                    "description": metadata["description"],
                    "collection_rule": metadata["description"],
                    "comparison_direction": metadata["comparison_direction"],
                    "active": True,
                },
            )
            definitions[code] = definition

        active_template_ids = []
        for template_data in TEMPLATES:
            category = categories[template_data["category_slug"]]
            template, _ = ComparisonTemplate.objects.update_or_create(
                category=category,
                form_factor=template_data["form_factor"],
                name=template_data["name"],
                version=1,
                defaults={
                    "description": template_data["description"],
                    "active": True,
                },
            )
            active_template_ids.append(template.pk)
            desired_definition_ids = []
            for display_order, (code, priority) in enumerate(template_data["fields"], start=1):
                definition = definitions[code]
                desired_definition_ids.append(definition.pk)
                TemplateField.objects.update_or_create(
                    template=template,
                    spec_definition=definition,
                    defaults={
                        "priority": priority,
                        "required": priority == TemplateField.Priority.P0,
                        "display_group": definition.group,
                        "display_order": display_order * 10,
                        "highlight_relevance": priority == TemplateField.Priority.P0,
                    },
                )
            template.fields.exclude(spec_definition_id__in=desired_definition_ids).delete()

        managed_category_ids = [categories[item["category_slug"]].pk for item in TEMPLATES]
        ComparisonTemplate.objects.filter(category_id__in=managed_category_ids).exclude(
            pk__in=active_template_ids
        ).update(active=False)

        self.stdout.write(
            self.style.SUCCESS(
                f"Initialized {len(BRANDS)} brands, {len(CATEGORY_TREE)} categories, "
                f"{sum(len(items) for items in PRODUCT_TYPE_DEFINITIONS.values())} product types, "
                f"{len(SPEC_DEFINITIONS)} specification definitions, and "
                f"{len(TEMPLATES)} comparison templates."
            )
        )
