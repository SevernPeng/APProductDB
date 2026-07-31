import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from catalog.ai_datasheets import (
    AIExtractionError,
    _field_catalog,
    _models_equivalent,
    _select_relevant_text,
    extract_specs_with_ai,
)
from catalog.datasheets import ExtractedDocument
from catalog.models import Brand, Category, Product, SpecDefinition


@override_settings(
    AI_DATASHEET_ENABLED=True,
    AI_DATASHEET_BASE_URL="http://127.0.0.1:11434/",
    AI_DATASHEET_MODEL="qwen3-vl:4b",
    AI_DATASHEET_TEXT_MODEL="qwen3:1.7b",
    AI_DATASHEET_VISION_MODEL="qwen3-vl:2b-instruct",
    AI_DATASHEET_MIN_CONFIDENCE=0.72,
    AI_DATASHEET_OCR_THRESHOLD=1,
    AI_DATASHEET_MAX_TEXT_CHARS=600000,
    AI_DATASHEET_CONTEXT_LENGTH=32768,
    AI_DATASHEET_KEEP_ALIVE="5m",
    AI_DATASHEET_TIMEOUT=60,
    AI_DATASHEET_MAX_OUTPUT_TOKENS=3072,
)
class AIDatasheetExtractionTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="TP-Link", slug="tp-link")
        category = Category.objects.create(name="Access Point", slug="access-point")
        self.product = Product.objects.create(
            brand=brand,
            category=category,
            model="EAP772",
        )
        self.definition = SpecDefinition.objects.create(
            category=category,
            code="max_power_consumption_w",
            display_name="Maximum Power Consumption",
            group="Power",
            data_type=SpecDefinition.DataType.DECIMAL,
            unit="W",
            is_core=True,
        )
        self.template_items = [
            SimpleNamespace(
                spec_definition=self.definition,
                display_group="Power",
            )
        ]
        self.document = ExtractedDocument(
            text="EAP772 Maximum Power Consumption: 24 W",
            final_url="https://www.tp-link.com/EAP772.pdf",
            content=b"%PDF-test",
            page_count=2,
            is_pdf=True,
        )

    def response_payload(self, *, model="EAP772", confidence=0.96):
        result = {
            "document_match": {
                "model_present": True,
                "matched_model": model,
                "model_evidence": f"TP-Link {model}",
                "page_number": 1,
                "confidence": 0.99,
            },
            "specs": [
                {
                    "code": "max_power_consumption_w",
                    "value_kind": "number",
                    "value_text": "",
                    "value_number": 24,
                    "value_boolean": None,
                    "unit": "W",
                    "raw_value": "Maximum Power Consumption: 24 W",
                    "page_number": 2,
                    "confidence": confidence,
                }
            ],
        }
        return {
            "message": {"role": "assistant", "content": json.dumps(result)},
            "total_duration": 1_250_000_000,
            "prompt_eval_count": 800,
            "prompt_eval_duration": 700_000_000,
            "eval_count": 120,
            "eval_duration": 500_000_000,
        }

    @patch("catalog.ai_datasheets._request_ollama")
    def test_layout_text_is_sent_with_schema_and_evidence_is_returned(self, request_ollama):
        request_ollama.return_value = self.response_payload()

        result = extract_specs_with_ai(
            self.product,
            self.document,
            self.template_items,
        )

        body = request_ollama.call_args.args[0]
        self.assertEqual(body["model"], "qwen3:1.7b")
        self.assertEqual(body["options"]["num_predict"], 3072)
        self.assertIs(body["think"], False)
        self.assertEqual(body["format"]["type"], "object")
        self.assertIn("DOCUMENT TEXT WITH PAGE MARKERS", body["messages"][0]["content"])
        self.assertNotIn("images", body["messages"][0])
        self.assertEqual(
            result.specs["max_power_consumption_w"],
            ("number", 24, "Maximum Power Consumption: 24 W"),
        )
        self.assertEqual(
            result.metadata["max_power_consumption_w"]["page_number"],
            2,
        )
        self.assertEqual(result.metrics["total_duration_ms"], 1250.0)
        self.assertEqual(result.metrics["prompt_eval_count"], 800)

    @patch("catalog.ai_datasheets._request_ollama")
    def test_low_confidence_spec_is_omitted(self, request_ollama):
        request_ollama.return_value = self.response_payload(confidence=0.4)

        result = extract_specs_with_ai(
            self.product,
            self.document,
            self.template_items,
        )

        self.assertEqual(result.specs, {})

    @patch("catalog.ai_datasheets._request_ollama")
    def test_qwen_thinking_field_is_used_when_content_is_empty(self, request_ollama):
        payload = self.response_payload()
        payload["message"]["thinking"] = payload["message"]["content"]
        payload["message"]["content"] = ""
        request_ollama.return_value = payload

        result = extract_specs_with_ai(
            self.product,
            self.document,
            self.template_items,
        )

        self.assertEqual(
            result.specs["max_power_consumption_w"],
            ("number", 24, "Maximum Power Consumption: 24 W"),
        )

    @patch("catalog.ai_datasheets._request_ollama")
    def test_wrong_model_is_rejected(self, request_ollama):
        request_ollama.return_value = self.response_payload(model="EAP773")

        with self.assertRaisesMessage(AIExtractionError, "足够置信度"):
            extract_specs_with_ai(
                self.product,
                self.document,
                self.template_items,
            )

    def test_long_pdf_context_keeps_head_and_target_model_pages(self):
        pages = []
        for page_number in range(1, 31):
            content = "generic marketing copy"
            if page_number == 24:
                content = "EAP772 Maximum Power Consumption: 24 W"
            pages.append(f"\n=== PDF PAGE {page_number} ===\n{content}")

        selected = _select_relevant_text(
            "".join(pages),
            self.product.model,
            _field_catalog(self.template_items),
        )

        self.assertIn("=== PDF PAGE 1 ===", selected)
        self.assertIn("=== PDF PAGE 24 ===", selected)
        self.assertLessEqual(selected.count("=== PDF PAGE"), 12)
        self.assertLessEqual(len(selected), 600000)

    def test_model_alias_allows_sku_inside_descriptive_model_name(self):
        self.assertTrue(
            _models_equivalent(
                "2530-24 Switch (J9782A)",
                "J9782A",
            )
        )
        self.assertFalse(_models_equivalent("EAP772", "EAP773"))

    @patch("catalog.ai_datasheets._request_ollama")
    def test_page_evidence_must_be_supported_by_extracted_text(
        self,
        request_ollama,
    ):
        request_ollama.return_value = self.response_payload()
        document = ExtractedDocument(
            text=(
                "\n=== PDF PAGE 1 ===\nTP-Link EAP772 Datasheet"
                "\n=== PDF PAGE 2 ===\nMaximum Power Consumption: 18 W"
            ),
            final_url=self.document.final_url,
            content=self.document.content,
            page_count=2,
            is_pdf=True,
        )

        result = extract_specs_with_ai(
            self.product,
            document,
            self.template_items,
        )

        self.assertEqual(result.specs, {})

    @patch("catalog.ai_datasheets._request_ollama")
    def test_returned_unit_must_match_database_unit(self, request_ollama):
        payload = self.response_payload()
        parsed = json.loads(payload["message"]["content"])
        parsed["specs"][0]["unit"] = "kW"
        payload["message"]["content"] = json.dumps(parsed)
        request_ollama.return_value = payload

        result = extract_specs_with_ai(
            self.product,
            self.document,
            self.template_items,
        )

        self.assertEqual(result.specs, {})

    @patch("catalog.ai_datasheets._request_ollama")
    def test_incomplete_structured_response_is_reported_as_ai_error(
        self,
        request_ollama,
    ):
        request_ollama.return_value = {
            "message": {"content": json.dumps({"document_match": {}})}
        }

        with self.assertRaisesMessage(AIExtractionError, "字段结构不完整"):
            extract_specs_with_ai(
                self.product,
                self.document,
                self.template_items,
            )
