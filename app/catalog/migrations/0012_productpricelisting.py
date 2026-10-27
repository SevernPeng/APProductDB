import django.db.models.deletion
from django.db import migrations, models


def backfill_price_listings(apps, schema_editor):
    ProductPriceListing = apps.get_model("catalog", "ProductPriceListing")
    ProductPriceSnapshot = apps.get_model("catalog", "ProductPriceSnapshot")
    seen = set()
    snapshots = ProductPriceSnapshot.objects.exclude(external_id="").order_by(
        "product_id", "source_id", "-created_at", "-pk"
    )
    for snapshot in snapshots.iterator():
        key = (snapshot.product_id, snapshot.source_id)
        if key in seen:
            continue
        seen.add(key)
        ProductPriceListing.objects.create(
            source_id=snapshot.source_id,
            product_id=snapshot.product_id,
            external_id=snapshot.external_id,
            external_model=snapshot.external_model,
            product_url=snapshot.product_url,
            last_checked_at=snapshot.created_at,
            last_seen_at=snapshot.created_at,
        )


def remove_price_listings(apps, schema_editor):
    apps.get_model("catalog", "ProductPriceListing").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("catalog", "0011_pricesource_productpricesnapshot")]

    operations = [
        migrations.CreateModel(
            name="ProductPriceListing",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("external_id", models.CharField(max_length=100)),
                ("external_model", models.CharField(max_length=200)),
                ("product_url", models.URLField()),
                ("active", models.BooleanField(default=True)),
                ("last_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_seen_at", models.DateTimeField(blank=True, null=True)),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="price_listings", to="catalog.product")),
                ("source", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="product_listings", to="catalog.pricesource")),
            ],
            options={"ordering": ("source", "product")},
        ),
        migrations.AddConstraint(
            model_name="productpricelisting",
            constraint=models.UniqueConstraint(fields=("source", "product"), name="catalog_unique_product_price_listing"),
        ),
        migrations.AddIndex(
            model_name="productpricelisting",
            index=models.Index(fields=["source", "external_id"], name="catalog_price_external_idx"),
        ),
        migrations.RunPython(backfill_price_listings, remove_price_listings),
    ]
