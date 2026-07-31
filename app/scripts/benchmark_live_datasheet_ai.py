"""Run one read-only adaptive AI extraction and report Ollama timings."""

import argparse
import json
import os
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from catalog.ai_datasheets import AIExtractionError, extract_specs_with_ai  # noqa: E402
from catalog.datasheets import _ai_target_items, _pdf_document  # noqa: E402
from catalog.management.commands.crawl_product_specs import extract_specs  # noqa: E402
from catalog.models import Product  # noqa: E402
from catalog.product_types import product_type_code  # noqa: E402
from catalog.services import template_fields  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("product_id", type=int)
    parser.add_argument("pdf", type=Path)
    args = parser.parse_args()

    product = Product.objects.select_related(
        "brand", "category", "product_type"
    ).get(pk=args.product_id)
    document = _pdf_document(args.pdf.read_bytes())
    items = template_fields(product.category, product_type_code(product))
    rule_specs = extract_specs(document.text, product.category.slug)
    ai_items, resolved = _ai_target_items(product, items, rule_specs)
    started = time.perf_counter()
    try:
        result = extract_specs_with_ai(product, document, ai_items)
        accepted_fields = sorted(result.specs)
        model = result.model_name
        metrics = result.metrics
        error = ""
    except AIExtractionError as exc:
        accepted_fields = []
        model = os.getenv("AI_DATASHEET_TEXT_MODEL", "")
        metrics = exc.metrics
        error = str(exc)
    print(
        json.dumps(
            {
                "product": f"{product.brand.name} {product.model}",
                "pages": document.page_count,
                "template_fields": len(items),
                "resolved_before_ai": len(resolved),
                "ai_target_fields": len(ai_items),
                "accepted_ai_fields": accepted_fields,
                "elapsed_seconds": round(time.perf_counter() - started, 2),
                "model": model,
                "error": error,
                "metrics": metrics,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
