import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0010_alter_product_lifecycle_status_and_more")]

    operations = [
        migrations.CreateModel(
            name="PriceSource",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("code", models.SlugField(max_length=50, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("base_url", models.URLField()),
                ("active", models.BooleanField(default=True)),
                ("last_synced_at", models.DateTimeField(blank=True, null=True)),
                ("last_sync_status", models.CharField(blank=True, max_length=20)),
                ("last_sync_message", models.TextField(blank=True)),
            ],
            options={"ordering": ("name",)},
        ),
        migrations.CreateModel(
            name="ProductPriceSnapshot",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("external_id", models.CharField(blank=True, max_length=100)),
                ("external_model", models.CharField(max_length=200)),
                ("product_url", models.URLField()),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("unit_price", models.DecimalField(decimal_places=4, max_digits=14)),
                ("list_price", models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ("special_price", models.DecimalField(blank=True, decimal_places=4, max_digits=14, null=True)),
                ("tax_included", models.BooleanField(default=False)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="price_snapshots", to="catalog.product")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="price_snapshots", to="catalog.pricesource")),
            ],
            options={"ordering": ("-created_at", "-pk")},
        ),
        migrations.AddIndex(
            model_name="productpricesnapshot",
            index=models.Index(fields=["product", "source", "-created_at"], name="catalog_price_product_idx"),
        ),
    ]
