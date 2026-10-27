"""Materialize the reviewed presentation rules without changing source rows."""
import io
import json
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Product, ProductSpec, SpecDefinition
from catalog.product_types import product_type_code
from catalog.services import template_fields
from catalog.spec_applicability import has_published_value
from comparison.spec_values import SpecResolver


def typed_value(definition, display):
    values = {"value_text": "", "value_number": None, "value_boolean": None}
    if display in {"Unknown", "Not Published", "Not Applicable"}:
        return None
    if definition.data_type in {"integer", "decimal"}:
        match = re.fullmatch(r"([\d,]+(?:\.\d+)?)\s*([A-Za-z]*)", display.strip())
        if not match:
            return None
        number = Decimal(match[1].replace(",", ""))
        source_unit, target_unit = match[2], definition.unit
        conversions = {("Gbps", "Mbps"): 1000, ("Mbps", "Gbps"): Decimal("0.001"),
                       ("Mbit", "MB"): Decimal("0.125"), ("KB", "bytes"): 1024}
        if source_unit != target_unit:
            factor = conversions.get((source_unit, target_unit))
            if factor is None:
                return None
            number *= factor
        if definition.data_type == "integer" and number != number.to_integral_value():
            return None
        values["value_number"] = number.quantize(Decimal("0.001"))
    elif definition.data_type == "boolean":
        if display.strip().casefold() not in {"yes", "no", "true", "false", "√", "✓"}:
            return None
        values["value_boolean"] = display.strip().casefold() in {"yes", "true", "√", "✓"}
    else:
        values["value_text"] = display
    return values


class Command(BaseCommand):
    help = "Sync canonical specs from existing source data using the latest reviewed format rules."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--report", type=Path)

    @transaction.atomic
    def handle(self, *args, **options):
        wifi_output = io.StringIO()
        call_command("sync_wifi_standards", stdout=wifi_output)
        definitions = {d.code: d for d in SpecDefinition.objects.filter(active=True).exclude(code__startswith="matrix-")}
        products = Product.objects.select_related("brand", "category", "product_type").prefetch_related("specs__definition")
        changes, skipped = [], []
        field_cache = {}
        for product in products:
            cache_key = (product.category_id, product_type_code(product))
            if cache_key not in field_cache:
                field_cache[cache_key] = {f.spec_definition.code for f in template_fields(product.category, cache_key[1])}
            resolver = SpecResolver(product, list(definitions.values()))
            codes = field_cache[cache_key] | (set(resolver.specs) & set(definitions))
            wireless = product.category.slug in {"access-point", "wireless-bridge"}
            if wireless:
                codes |= {"supported_bands", "antenna_type", "total_spatial_streams", "rate_2g_mbps", "rate_5g_mbps", "rate_6g_mbps", "mesh_support", "fast_roaming"}
            # Resolve supported bands before downstream wireless calculations.
            for code in sorted(codes, key=lambda code: (code != "supported_bands", code)):
                definition = definitions.get(code)
                if definition is None:
                    continue
                existing = resolver.specs.get(code)
                if existing and existing.value_status == "not_applicable":
                    continue
                value = None
                if wireless and code == "antenna_type":
                    value = resolver.antenna()
                elif wireless and (code.startswith("rate_") or code == "total_spatial_streams"):
                    value = resolver.wireless_value(code)
                elif wireless and code in {"mesh_support", "fast_roaming"}:
                    value = resolver.wireless_function(code)
                if value is None:
                    if has_published_value(existing):
                        continue
                    value = resolver.resolve(code)
                if value is None:
                    continue
                typed = typed_value(definition, value.display_value)
                if typed is None:
                    if code == "fast_roaming" and value.display_value == "Unknown" and has_published_value(existing):
                        typed = {"value_text": "", "value_number": None, "value_boolean": None}
                    else:
                        if value.display_value not in {"Unknown", "Not Published", "Not Applicable"}:
                            skipped.append({"product": product.pk, "code": code, "value": value.display_value})
                        continue
                status = "unknown" if value.display_value == "Unknown" else "published"
                if existing and existing.value_status == status and all(getattr(existing, k) == v for k, v in typed.items()):
                    continue
                before = {k: getattr(existing, k) for k in ("value_status", "value_text", "value_number", "value_boolean", "unit", "raw_value", "source_url", "source_note")} if existing else None
                defaults = {**typed, "value_status": status, "unit": definition.unit,
                            "normalized_value": value.display_value, "raw_value": value.display_value,
                            "source_url": value.effective_source_url,
                            "source_note": f"Synchronized from existing product specifications using reviewed format rules: {code}.",
                            "verified_date": existing.verified_date if existing else None}
                updated, created = ProductSpec.objects.update_or_create(product=product, definition=definition, defaults=defaults)
                resolver.specs[code] = updated
                changes.append({"product_id": product.pk, "model": product.model, "code": code,
                                "created": created, "before": before, "after": defaults})
        report = {"dry_run": options["dry_run"], "wifi": json.loads(wifi_output.getvalue()),
                  "changed_specs": len(changes), "created_specs": sum(c["created"] for c in changes),
                  "products_changed": len({c["product_id"] for c in changes}),
                  "by_field": dict(Counter(c["code"] for c in changes)),
                  "skipped_complex_values": len(skipped), "changes": changes, "skipped": skipped}
        if options["dry_run"]:
            transaction.set_rollback(True)
        if options["report"]:
            Path(options["report"]).write_text(json.dumps(report, default=str, indent=2), encoding="utf-8")
        self.stdout.write(json.dumps({k: v for k, v in report.items() if k not in {"changes", "skipped", "wifi"}}))
