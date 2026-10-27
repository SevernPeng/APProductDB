from django.db import migrations


def migrate_mobile_app(apps, schema_editor):
    Definition = apps.get_model("catalog", "SpecDefinition")
    Spec = apps.get_model("catalog", "ProductSpec")
    for definition in Definition.objects.all():
        if " ".join(definition.display_name.split()).casefold() not in {"omada app", "mobile app"}:
            continue
        definition.display_name = "Mobile APP"
        definition.data_type = "text"
        definition.save(update_fields=["display_name", "data_type"])
        for spec in Spec.objects.filter(definition=definition):
            text = spec.value_text.strip()
            if spec.value_boolean is not None:
                text = "Yes" if spec.value_boolean else "No"
            if spec.product.brand.slug == "tp-link" and text.casefold() == "yes":
                text = "Omada APP"
            spec.value_text = text
            spec.value_boolean = None
            spec.save(update_fields=["value_text", "value_boolean"])


class Migration(migrations.Migration):
    dependencies = [("catalog", "0013_product_nom_records")]
    operations = [migrations.RunPython(migrate_mobile_app, migrations.RunPython.noop)]
