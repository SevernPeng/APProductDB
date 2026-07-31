import re

import django.db.models.deletion
from django.db import migrations, models


PRODUCT_TYPES = {
    "access-point": (
        ("ceiling", "Ceiling Mount"),
        ("wall", "Wall Mount"),
        ("wall_plate", "Wall Plate"),
        ("outdoor", "Outdoor"),
        ("desktop", "Desktop"),
        ("extender", "Extender"),
        ("other", "Other AP"),
    ),
    "managed-switches": (
        ("l2", "Layer 2"),
        ("l2_plus", "Layer 2+"),
        ("l3", "Layer 3"),
        ("unknown", "Unknown Layer"),
    ),
    "unmanaged-easy-smart-switches": (
        ("unmanaged", "Unmanaged"),
        ("easy_smart", "Easy Smart"),
        ("unknown", "Unknown Management Type"),
    ),
    "gateway": (
        ("wired_router", "Wired Router"),
        ("wireless_router", "Wireless Router"),
        ("cellular_router", "Cellular Router"),
        ("outdoor_cellular_router", "Outdoor Cellular Router"),
        ("integrated_gateway", "Integrated Gateway"),
        ("other", "Other Router"),
    ),
    "accessories": (
        ("poe_injector", "PoE Injector"),
        ("power_supply", "Power Supply"),
        ("media_converter", "Media Converter"),
        ("optical_module", "Optical Module"),
        ("dac_cable", "DAC Cable"),
        ("mounting", "Mounting Accessory"),
        ("chassis", "Chassis"),
        ("antenna", "Antenna"),
        ("junction_box", "Junction Box"),
        ("other", "Other Accessory"),
    ),
}


def infer_code(category_slug, model, ap_type):
    upper = (model or "").upper()
    if category_slug == "access-point":
        if "EXTENDER" in upper:
            return "extender"
        if ap_type in {
            "ceiling",
            "wall",
            "wall_plate",
            "outdoor",
            "desktop",
            "other",
        }:
            return ap_type
        return "ceiling"
    if category_slug == "managed-switches":
        if re.match(r"^(S7|S6|SX6|SG6|SG5)", upper):
            return "l3"
        if re.match(r"^(SG3|SX3)", upper):
            return "l2_plus"
        if re.match(r"^(SG2|ES)", upper):
            return "l2"
        return "unknown"
    if category_slug == "unmanaged-easy-smart-switches":
        if re.search(r"(?:E|DE|PE|MPE|GE)$", upper):
            return "easy_smart"
        if upper.startswith(("DS", "LS", "TL-SF", "TL-SG")):
            return "unmanaged"
        return "unknown"
    if category_slug == "gateway":
        if "FUSION" in upper or upper.endswith("PC"):
            return "integrated_gateway"
        if ("4G" in upper or "5G" in upper or "LTE" in upper) and "OUTDOOR" in upper:
            return "outdoor_cellular_router"
        if "4G" in upper or "5G" in upper or "LTE" in upper:
            return "cellular_router"
        if re.match(r"^ER\d+W", upper):
            return "wireless_router"
        if upper.startswith(("ER", "UXG", "CCR", "RB", "VIGOR")):
            return "wired_router"
        return "other"
    if category_slug == "accessories":
        if upper.startswith("POE"):
            return "poe_injector"
        if upper.startswith("PSM"):
            return "power_supply"
        if upper == "MC1400":
            return "chassis"
        if upper.startswith("MC"):
            return "media_converter"
        if re.match(r"^(?:I?SM)\d+.*-\d+M$", upper):
            return "dac_cable"
        if upper.startswith(("SM", "ISM")):
            return "optical_module"
        if "MOUNT" in upper or "RACK" in upper:
            return "mounting"
        if upper.startswith("APM"):
            return "antenna"
        if upper.startswith("OJB"):
            return "junction_box"
        return "other"
    return None


def create_types_and_backfill(apps, schema_editor):
    Category = apps.get_model("catalog", "Category")
    Product = apps.get_model("catalog", "Product")
    ProductType = apps.get_model("catalog", "ProductType")

    types = {}
    for category_slug, definitions in PRODUCT_TYPES.items():
        category = Category.objects.filter(slug=category_slug).first()
        if category is None:
            continue
        for order, (code, name) in enumerate(definitions, start=1):
            product_type, _ = ProductType.objects.update_or_create(
                category=category,
                code=code,
                defaults={
                    "name": name,
                    "display_order": order * 10,
                    "active": True,
                },
            )
            types[(category_slug, code)] = product_type

    for product in Product.objects.select_related("category").iterator():
        code = infer_code(product.category.slug, product.model, product.ap_type)
        product_type = types.get((product.category.slug, code))
        if product_type is not None:
            Product.objects.filter(pk=product.pk).update(product_type=product_type)


def clear_product_types(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    ProductType = apps.get_model("catalog", "ProductType")
    Product.objects.update(product_type=None)
    ProductType.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_product_type_specific_legacy_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.SlugField(max_length=50)),
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("display_order", models.PositiveIntegerField(default=0)),
                ("active", models.BooleanField(default=True)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="product_types",
                        to="catalog.category",
                    ),
                ),
            ],
            options={
                "ordering": ("category", "display_order", "name"),
            },
        ),
        migrations.AddConstraint(
            model_name="producttype",
            constraint=models.UniqueConstraint(
                fields=("category", "code"),
                name="catalog_unique_category_product_type_code",
            ),
        ),
        migrations.AddConstraint(
            model_name="producttype",
            constraint=models.UniqueConstraint(
                fields=("category", "name"),
                name="catalog_unique_category_product_type_name",
            ),
        ),
        migrations.AddField(
            model_name="product",
            name="product_type",
            field=models.ForeignKey(
                blank=True,
                help_text="Category-specific form factor or management layer.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="products",
                to="catalog.producttype",
            ),
        ),
        migrations.AlterField(
            model_name="comparisontemplate",
            name="form_factor",
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.RunPython(create_types_and_backfill, clear_product_types),
    ]
