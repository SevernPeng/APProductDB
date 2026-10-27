from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("catalog", "0012_productpricelisting")]

    operations = [
        migrations.AddField(
            model_name="product",
            name="nom_records",
            field=models.JSONField(default=list, blank=True, editable=False),
        ),
    ]
