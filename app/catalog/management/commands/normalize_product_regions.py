from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product, SpecEvidence
from catalog.regions import OFFICIAL_LATEST_HARDWARE, canonical_product_region
from changes.models import ChangeRequest
from comparison.models import BenchmarkCase, ProductMatch


class Command(BaseCommand):
    help = "Normalize wireless products to US and wired products to UN, merging regional duplicates."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    @transaction.atomic
    def handle(self, *args, **options):
        products = list(Product.objects.select_related("category").order_by("pk"))
        products_by_identity = {}
        merge_map = {}
        for product in products:
            desired_region = canonical_product_region(product.category.slug)
            if not desired_region:
                continue
            identity = (
                product.brand_id,
                product.model_key,
                product.category_id,
            )
            products_by_identity.setdefault(identity, []).append(product)

        def version_key(value):
            chunks = (value or "").upper().lstrip("V").split(".")
            return tuple(int(chunk) if chunk.isdigit() else -1 for chunk in chunks)

        for grouped_products in products_by_identity.values():
            if len(grouped_products) < 2:
                continue
            desired_region = canonical_product_region(grouped_products[0].category.slug)
            target = max(
                grouped_products,
                key=lambda item: (
                    item.region == desired_region,
                    version_key(item.hardware_version),
                    -item.pk,
                ),
            )
            for product in grouped_products:
                if product.pk != target.pk:
                    merge_map[product.pk] = target.pk

        def canonical_id(product_id):
            return merge_map.get(product_id, product_id)

        case_map = {}
        for case in BenchmarkCase.objects.filter(anchor_product_id__in=merge_map).order_by("pk"):
            target_anchor_id = canonical_id(case.anchor_product_id)
            target_region = canonical_product_region(case.anchor_product.category.slug)
            target_case = (
                BenchmarkCase.objects.exclude(pk=case.pk)
                .filter(anchor_product_id=target_anchor_id, region=target_region)
                .order_by("pk")
                .first()
            )
            if target_case:
                case_map[case.pk] = target_case.pk
            else:
                case.anchor_product_id = target_anchor_id
                case.region = target_region
                case.name = case.name.replace("Global", target_region)
                case.save(update_fields=("anchor_product", "region", "name", "updated_at"))

        matches_merged = 0
        for match in ProductMatch.objects.select_related(
            "our_product__category", "benchmark_case"
        ).order_by("pk"):
            new_our_id = canonical_id(match.our_product_id)
            new_competitor_id = canonical_id(match.competitor_product_id)
            new_case_id = case_map.get(match.benchmark_case_id, match.benchmark_case_id)
            new_region = canonical_product_region(match.our_product.category.slug) or match.region
            duplicate_query = ProductMatch.objects.exclude(pk=match.pk)
            if new_case_id:
                duplicate = duplicate_query.filter(
                    benchmark_case_id=new_case_id,
                    competitor_product_id=new_competitor_id,
                ).first()
            else:
                duplicate = duplicate_query.filter(
                    benchmark_case__isnull=True,
                    our_product_id=new_our_id,
                    competitor_product_id=new_competitor_id,
                    region=new_region,
                ).first()
            if duplicate:
                ChangeRequest.objects.filter(target_match=match).update(target_match=duplicate)
                match.delete()
                matches_merged += 1
            else:
                ProductMatch.objects.filter(pk=match.pk).update(
                    our_product_id=new_our_id,
                    competitor_product_id=new_competitor_id,
                    benchmark_case_id=new_case_id,
                    region=new_region,
                )

        BenchmarkCase.objects.filter(pk__in=case_map).delete()

        specs_merged = 0
        for source_id, target_id in merge_map.items():
            source = Product.objects.get(pk=source_id)
            target = Product.objects.get(pk=target_id)
            target_specs = {spec.definition_id: spec for spec in target.specs.all()}
            for source_spec in list(source.specs.all()):
                target_spec = target_specs.get(source_spec.definition_id)
                if not target_spec:
                    source_spec.product = target
                    source_spec.save(update_fields=("product", "updated_at"))
                    target_specs[source_spec.definition_id] = source_spec
                    continue
                ChangeRequest.objects.filter(target_spec=source_spec).update(target_spec=target_spec)
                for evidence in list(source_spec.evidence.all()):
                    duplicate_evidence = SpecEvidence.objects.filter(
                        product_spec=target_spec,
                        source_document=evidence.source_document,
                        source_location=evidence.source_location,
                    ).exists()
                    if duplicate_evidence:
                        evidence.delete()
                    else:
                        evidence.product_spec = target_spec
                        evidence.save(update_fields=("product_spec", "updated_at"))
                source_spec.delete()
                specs_merged += 1
            source.highlights.update(product=target)
            ChangeRequest.objects.filter(target_product=source).update(target_product=target)
            for field in (
                "official_url",
                "datasheet_url",
                "image",
                "notes",
                "wifi_standard",
                "sku",
            ):
                if not getattr(target, field) and getattr(source, field):
                    setattr(target, field, getattr(source, field))
            target.is_published = target.is_published or source.is_published
            target.save()
            source.delete()

        regions_updated = 0
        for product in Product.objects.select_related("category"):
            desired_region = canonical_product_region(product.category.slug)
            update_fields = []
            if desired_region and product.region != desired_region:
                product.region = desired_region
                update_fields.append("region")
                regions_updated += 1
            latest = OFFICIAL_LATEST_HARDWARE.get(
                (product.brand.slug, product.model_key, desired_region)
            )
            if latest:
                latest_version, latest_url = latest
                if product.hardware_version != latest_version:
                    product.hardware_version = latest_version
                    update_fields.append("hardware_version")
                if product.official_url != latest_url:
                    product.official_url = latest_url
                    update_fields.append("official_url")
            if update_fields:
                product.save(update_fields=tuple(update_fields) + ("updated_at",))

        for case in BenchmarkCase.objects.select_related("anchor_product__category"):
            desired_region = canonical_product_region(case.anchor_product.category.slug)
            if desired_region and case.region != desired_region:
                old_region = case.region
                case.region = desired_region
                case.name = case.name.replace(old_region, desired_region)
                case.save(update_fields=("region", "name", "updated_at"))
        for match in ProductMatch.objects.select_related("our_product__category"):
            desired_region = canonical_product_region(match.our_product.category.slug)
            if desired_region and match.region != desired_region:
                ProductMatch.objects.filter(pk=match.pk).update(region=desired_region)

        summary = {
            "products_merged": len(merge_map),
            "specs_merged": specs_merged,
            "matches_merged": matches_merged,
            "regions_updated": regions_updated,
        }
        if options["dry_run"]:
            transaction.set_rollback(True)
            self.stdout.write(f"DRY RUN: {summary}")
        else:
            self.stdout.write(self.style.SUCCESS(f"NORMALIZED: {summary}"))
