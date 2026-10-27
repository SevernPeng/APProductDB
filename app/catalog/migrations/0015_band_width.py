from django.db import migrations


def add_band_width(apps, schema_editor):
    Definition = apps.get_model("catalog", "SpecDefinition")
    Product = apps.get_model("catalog", "Product")
    Spec = apps.get_model("catalog", "ProductSpec")
    if not Product.objects.exists() and not Definition.objects.filter(code="max_channel_width_mhz").exists():
        return  # A fresh catalog is populated by initialize_catalog.
    definition, _ = Definition.objects.update_or_create(code="max_channel_width_mhz", defaults={
        "display_name": "Band Width", "data_type": "integer", "unit": "MHz",
        "active": True, "group": "Wireless",
    })
    from catalog.wireless import product_has_wifi
    for product in Product.objects.select_related("category", "brand", "product_type").prefetch_related("specs__definition"):
        if product_has_wifi(product):
            Spec.objects.get_or_create(product=product, definition=definition,
                defaults={"value_status": "unknown", "unit": "MHz"})


class Migration(migrations.Migration):
    dependencies = [("catalog", "0014_mobile_app")]
    operations = [migrations.RunPython(add_band_width, migrations.RunPython.noop)]
