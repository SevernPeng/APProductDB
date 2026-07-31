from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_product_type_taxonomy"),
        ("imports", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="importjob",
            name="product_type",
            field=models.ForeignKey(
                blank=True,
                help_text="Product form selected before downloading and uploading a template.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="import_jobs",
                to="catalog.producttype",
            ),
        ),
    ]
