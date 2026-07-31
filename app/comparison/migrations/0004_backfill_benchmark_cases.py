from django.db import migrations


def backfill_benchmark_cases(apps, schema_editor):
    BenchmarkCase = apps.get_model("comparison", "BenchmarkCase")
    ProductMatch = apps.get_model("comparison", "ProductMatch")

    pairs = ProductMatch.objects.values_list("our_product_id", "region").distinct()
    for our_product_id, region in pairs:
        product = ProductMatch.objects.filter(our_product_id=our_product_id).first().our_product
        benchmark_case, _ = BenchmarkCase.objects.get_or_create(
            anchor_product_id=our_product_id,
            region=region,
            name=f"{product.model} {region} competitor benchmark",
            defaults={
                "status": "approved",
                "scenario": "Migrated from legacy product matches",
            },
        )
        for rank, match in enumerate(
            ProductMatch.objects.filter(
                our_product_id=our_product_id,
                region=region,
                benchmark_case_id__isnull=True,
            ).order_by("competitor_product_id"),
            start=1,
        ):
            ProductMatch.objects.filter(pk=match.pk).update(
                benchmark_case_id=benchmark_case.pk,
                rank=rank,
            )


def reverse_backfill(apps, schema_editor):
    ProductMatch = apps.get_model("comparison", "ProductMatch")
    BenchmarkCase = apps.get_model("comparison", "BenchmarkCase")
    ProductMatch.objects.update(benchmark_case_id=None, rank=0)
    BenchmarkCase.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0003_backfill_product_database"),
        ("comparison", "0003_benchmarkcase_alter_productmatch_options_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_benchmark_cases, reverse_backfill),
    ]
