from django.db import migrations


def backfill_product_database(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    ProductModel = apps.get_model("catalog", "ProductModel")
    ProductSpec = apps.get_model("catalog", "ProductSpec")
    SourceDocument = apps.get_model("catalog", "SourceDocument")
    SpecEvidence = apps.get_model("catalog", "SpecEvidence")

    for product in Product.objects.select_related("brand", "category").all():
        product_model, _ = ProductModel.objects.get_or_create(
            brand_id=product.brand_id,
            model_key=product.model_key,
            defaults={
                "category_id": product.category_id,
                "model": product.model,
                "lifecycle_status": product.lifecycle_status,
                "active": True,
            },
        )
        if product.product_model_id != product_model.id:
            Product.objects.filter(pk=product.pk).update(product_model_id=product_model.id)

    status_map = {
        "not published": "not_published",
        "not applicable": "not_applicable",
        "unknown": "unknown",
    }
    for spec in ProductSpec.objects.select_related(
        "product",
        "product__brand",
        "definition",
    ).all():
        text_value = (spec.value_text or "").strip()
        status = status_map.get(text_value.casefold(), "published")
        updates = {
            "value_status": status,
            "unit": spec.unit or spec.definition.unit,
        }
        if status != "published":
            updates["raw_value"] = spec.raw_value or text_value
            updates["value_text"] = ""
            updates["normalized_value"] = ""
        elif not spec.normalized_value:
            if spec.value_number is not None:
                updates["normalized_value"] = format(spec.value_number, "f")
            else:
                updates["normalized_value"] = text_value
        ProductSpec.objects.filter(pk=spec.pk).update(**updates)

        source_url = spec.source_url or spec.product.official_url
        if not source_url:
            continue
        document_type = "specification" if spec.source_url else "product_page"
        source, _ = SourceDocument.objects.get_or_create(
            url=source_url,
            document_version="",
            defaults={
                "brand_id": spec.product.brand_id,
                "document_type": document_type,
                "title": f"{spec.product.brand.name} {spec.product.model}",
                "region": spec.product.region,
                "accessed_date": spec.verified_date,
                "active": True,
            },
        )
        SpecEvidence.objects.get_or_create(
            product_spec_id=spec.pk,
            source_document_id=source.pk,
            source_location=(spec.source_note or "")[:250],
            defaults={
                "source_excerpt": spec.source_note,
                "evidence_level": "a" if spec.source_url else "b",
            },
        )


def reverse_backfill(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    Product.objects.update(product_model_id=None)


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0002_product_datasheet_url_product_launch_date_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_product_database, reverse_backfill),
    ]
