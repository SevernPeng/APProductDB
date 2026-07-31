"""Measure context reduction without losing reviewed evidence pages."""

import argparse
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DJANGO_SECRET_KEY", "datasheet-benchmark-local-only")
os.environ.setdefault("AP_PRODUCT_DATA_ROOT", str(PROJECT_ROOT))

import django  # noqa: E402

sys.argv.append("pytest-datasheet-benchmark")
django.setup()
sys.argv.pop()

from catalog.ai_datasheets import (  # noqa: E402
    _evidence_supported,
    _select_relevant_text,
    _split_pdf_pages,
)
from catalog.management.commands.crawl_product_specs import extract_specs  # noqa: E402
from catalog.spec_templates import SPEC_DEFINITIONS  # noqa: E402


def _pdf_text(path):
    reader = PdfReader(BytesIO(path.read_bytes()))
    chunks = []
    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text(extraction_mode="layout") or ""
        except (TypeError, ValueError):
            text = page.extract_text() or ""
        chunks.append(f"\n=== PDF PAGE {page_number} ===\n{text}")
    return "".join(chunks)


def _field_catalog(codes):
    fields = []
    for code in codes:
        definition = SPEC_DEFINITIONS.get(code, {})
        fields.append(
            {
                "code": code,
                "name": definition.get("display_name", code),
                "group": definition.get("group", ""),
                "description": definition.get("description", ""),
                "collection_rule": "",
            }
        )
    return fields


def run(dataset_path, pdf_dir):
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    truth_by_case = {}
    for row in dataset["truth"]:
        if row[3] == "Published" and row[8]:
            truth_by_case.setdefault(row[1], []).append(row)

    total_chars = selected_chars = 0
    evidence_pages = selected_evidence_pages = 0
    text_documents = 0
    rows = []
    category_slugs = {
        "Access Point": "access-point",
        "Gateway": "gateway",
        "Managed Switch": "managed-switches",
        "Unmanaged / Easy Smart Switch": "unmanaged-easy-smart-switches",
        "Wireless Bridge": "wireless-bridge",
        "Accessories": "accessories",
    }
    for case in dataset["cases"]:
        case_id, model = case[0], case[2]
        pdf_path = pdf_dir / Path(case[7]).name
        if not pdf_path.exists():
            continue
        text = _pdf_text(pdf_path)
        if len(re.sub(r"\s+", "", text)) < 500:
            continue
        truth = truth_by_case.get(case_id, [])
        rule_specs = extract_specs(
            text,
            category_slugs.get(case[3], ""),
        )
        truth = [row for row in truth if row[2] not in rule_specs]
        if not truth:
            continue
        codes = sorted({row[2] for row in truth})
        selected = _select_relevant_text(text, model, _field_catalog(codes))
        selected_pages = {
            page_number for page_number, _ in _split_pdf_pages(selected)
        }
        expected_pages = {int(row[8]) for row in truth}
        hits = len(expected_pages & selected_pages)
        total = len(expected_pages)
        rows.append(
            {
                "case_id": case_id,
                "model": model,
                "source_pages": len(_split_pdf_pages(text)),
                "selected_pages": len(selected_pages),
                "evidence_page_recall": hits / total if total else 1,
                "rule_fields": len(rule_specs),
                "ai_target_fields": len(codes),
                "evidence_text_recall": (
                    sum(
                        1
                        for row in truth
                        if _evidence_supported(
                            row[7],
                            int(row[8]),
                            dict(_split_pdf_pages(selected)),
                        )
                    )
                    / len(truth)
                ),
            }
        )
        total_chars += len(text)
        selected_chars += len(selected)
        evidence_pages += total
        selected_evidence_pages += hits
        text_documents += 1

    return {
        "text_documents": text_documents,
        "evidence_pages": evidence_pages,
        "selected_evidence_pages": selected_evidence_pages,
        "evidence_page_recall": (
            selected_evidence_pages / evidence_pages if evidence_pages else 1
        ),
        "source_characters": total_chars,
        "selected_characters": selected_chars,
        "context_reduction": 1 - (selected_chars / total_chars),
        "documents": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        type=Path,
        default=PROJECT_ROOT
        / "datasets"
        / "datasheet-benchmark"
        / "reviewed_ground_truth.json",
    )
    parser.add_argument(
        "--pdf-dir",
        type=Path,
        default=PROJECT_ROOT
        / "datasets"
        / "datasheet-benchmark"
        / "pdfs",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(run(args.dataset, args.pdf_dir), indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
