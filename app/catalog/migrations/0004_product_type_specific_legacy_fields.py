from django.db import migrations, models


def clear_non_wireless_legacy_values(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.exclude(category__slug="access-point").update(ap_type="")
    Product.objects.exclude(
        category__slug__in=("access-point", "wireless-bridge")
    ).update(wifi_standard="")


class Migration(migrations.Migration):
    dependencies = [("catalog", "0003_backfill_product_database")]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="ap_type",
            field=models.CharField(
                blank=True,
                choices=[
                    ("ceiling", "Ceiling"),
                    ("wall", "Wall"),
                    ("wall_plate", "Wall Plate"),
                    ("outdoor", "Outdoor"),
                    ("desktop", "Desktop"),
                    ("other", "Other"),
                ],
                db_index=True,
                default="",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="wifi_standard",
            field=models.CharField(blank=True, default="", max_length=50),
        ),
        migrations.RunPython(clear_non_wireless_legacy_values, migrations.RunPython.noop),
    ]
