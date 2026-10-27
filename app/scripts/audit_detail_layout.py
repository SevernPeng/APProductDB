"""Run with manage.py shell on a disposable database copy; edit GETs add placeholders."""
import json
import os
from collections import OrderedDict
from pathlib import Path
from unittest.mock import patch

from django.conf import settings
from django.db import transaction
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from catalog.models import Product
from catalog.wireless import product_has_wifi
from core.product_spec_layout import reference_product
from core.views import product_detail


@transaction.atomic
def run():
    if Path(settings.DATABASES["default"]["NAME"]).name != "detail-layout-audit.sqlite3":
        raise RuntimeError("Use the disposable detail-layout-audit.sqlite3 database copy.")
    user = get_user_model().objects.filter(is_active=True, is_superuser=True).first()
    if not user:
        raise RuntimeError("An existing active administrator is required for the audit copy.")
    factory = RequestFactory()
    before = {p["id"]: p for p in json.loads((settings.PROJECT_ROOT / "output/detail-fields-before.json").read_text(encoding="utf-8"))}
    references = {}
    records, failures = [], []
    report = settings.PROJECT_ROOT / "output/detail-layout-audit.json"
    recheck_ids = None
    if os.getenv("AUDIT_RECHECK_FAILURES") == "1":
        previous = json.loads(report.read_text(encoding="utf-8"))
        recheck_ids = {item["id"] for item in previous["summary"]["failures"]}
        records = [item for item in previous["products"] if item["id"] not in recheck_ids]

    def context(pk, edit=False):
        request = factory.get(f"/products/{pk}/", {"edit": "1"} if edit else {})
        request.user = user
        with patch("core.views.render", side_effect=lambda request, template, context: context):
            return product_detail(request, pk)

    def fields(ctx):
        return [(g["name"], r["display_name"]) for g in ctx["spec_groups"] for r in g["rows"]]

    products = Product.objects.filter(brand__is_own_brand=False, is_published=True).select_related(
        "brand", "category", "product_type").prefetch_related("specs__definition")
    if recheck_ids is not None:
        products = products.filter(pk__in=recheck_ids)
    for index, product in enumerate(products, 1):
        reference = reference_product(product)
        if reference is None:
            failures.append({"id": product.pk, "error": "No TP-Link reference"})
            continue
        if reference.pk not in references:
            references[reference.pk] = fields(context(reference.pk))
        expected = list(references[reference.pk])
        if not product_has_wifi(product):
            expected = [field for field in expected if field[1] != "Band Width"]
        elif not any(field[1] == "Band Width" for field in expected):
            expected.append(("WIRELESS FEATURES", "Band Width"))
        groups = OrderedDict()
        for group, name in expected:
            groups.setdefault(group, []).append(name)
        expected = [(group, name) for group, names in groups.items() for name in names]
        browse = context(product.pk)
        edit = context(product.pk, True)
        again = context(product.pk)
        errors = []
        for name, ctx in (("browse", browse), ("edit", edit), ("after_edit", again)):
            if fields(ctx) != expected:
                errors.append({"mode": name, "extra": list(set(fields(ctx)) - set(expected)),
                               "missing": list(set(expected) - set(fields(ctx)))})
        for group in edit["spec_groups"]:
            for row in group["rows"]:
                if row.get("definition") and not row.get("edit_item"):
                    errors.append({"uneditable": row["display_name"]})
        if errors:
            failures.append({"id": product.pk, "model": product.model, "errors": errors})
        names = [name for _, name in fields(browse)]
        records.append({"id": product.pk, "brand": product.brand.slug, "model": product.model,
            "reference": reference.model, "reference_id": reference.pk, "fields": names,
            "removed": sorted(set(before.get(product.pk, {}).get("fields", [])) - set(names))})
        if index % 100 == 0:
            print(f"Checked {index} competitor detail/edit pages", flush=True)
    summary = {"competitors_checked": len(records), "references_checked": len({r["reference_id"] for r in records}),
        "products_with_removed_fields": sum(bool(r["removed"]) for r in records),
        "removed_field_occurrences": sum(len(r["removed"]) for r in records),
        "wifi_products": sum(product_has_wifi(p) for p in Product.objects.select_related(
            "brand", "category", "product_type").prefetch_related("specs__definition")),
        "failures": failures}
    report.write_text(json.dumps({"summary": summary, "products": records}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if failures:
        raise RuntimeError(f"{len(failures)} products failed layout audit; see {report}")


run()
