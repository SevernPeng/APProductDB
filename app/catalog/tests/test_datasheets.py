import hashlib
from types import SimpleNamespace
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from catalog.datasheets import (
    DatasheetValidationError,
    ExtractedDocument,
    _html_pdf_links,
    process_datasheet_ingestion,
    validate_public_url,
)
from catalog.models import (
    Brand,
    Category,
    DatasheetIngestion,
    Product,
    ProductSpec,
    SourceDocument,
    SpecDefinition,
)


class DatasheetIngestionTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(
            name="TP-Link",
            slug="tp-link",
            official_website="https://www.tp-link.com/",
        )
        self.category = Category.objects.create(
            name="Access Point",
            slug="access-point",
        )
        self.product = Product.objects.create(
            brand=self.brand,
            category=self.category,
            model="EAP772",
        )
        self.dimensions = SpecDefinition.objects.create(
            category=self.category,
            code="dimensions_mm",
            display_name="Dimensions",
            group="Physical",
            data_type=SpecDefinition.DataType.TEXT,
            unit="mm",
            is_core=True,
        )

    def make_ingestion(self):
        return DatasheetIngestion.objects.create(
            product=self.product,
            source_type=DatasheetIngestion.SourceType.UPLOAD,
            uploaded_file=SimpleUploadedFile(
                "datasheet.pdf",
                b"%PDF-dummy",
                content_type="application/pdf",
            ),
        )

    @patch("catalog.datasheets.read_uploaded_document")
    def test_matching_model_imports_specs_after_validation(self, read_document):
        read_document.return_value = ExtractedDocument(
            text="TP-Link EAP772 Datasheet\nDimensions: 220 x 220 x 32.5 mm",
            final_url="",
            content=b"%PDF-matching",
            page_count=2,
            is_pdf=True,
        )
        result = process_datasheet_ingestion(self.make_ingestion().pk)

        self.assertEqual(result.status, DatasheetIngestion.Status.VALIDATED)
        self.assertEqual(result.detected_model, "EAP772")
        self.assertEqual(result.extracted_spec_count, 1)
        self.assertEqual(
            ProductSpec.objects.get(
                product=self.product,
                definition=self.dimensions,
            ).value_text,
            "220 x 220 x 32.5 mm",
        )
        source = SourceDocument.objects.get(product=self.product)
        self.assertEqual(source.document_type, SourceDocument.DocumentType.DATASHEET)
        self.assertTrue(source.file.name.endswith(".pdf"))

    @patch("catalog.datasheets.read_uploaded_document")
    def test_wrong_model_is_rejected_without_database_writes(self, read_document):
        read_document.return_value = ExtractedDocument(
            text="TP-Link EAP773 Datasheet\nDimensions: 220 x 220 x 32.5 mm",
            final_url="",
            content=b"%PDF-wrong",
            page_count=2,
            is_pdf=True,
        )
        result = process_datasheet_ingestion(self.make_ingestion().pk)

        self.assertEqual(result.status, DatasheetIngestion.Status.REJECTED)
        self.assertIn("EAP772", result.validation_message)
        self.assertFalse(ProductSpec.objects.filter(product=self.product).exists())
        self.assertFalse(SourceDocument.objects.filter(product=self.product).exists())

    @patch("catalog.datasheets.read_uploaded_document")
    def test_existing_published_value_is_retained(self, read_document):
        ProductSpec.objects.create(
            product=self.product,
            definition=self.dimensions,
            value_text="Original human value",
        )
        read_document.return_value = ExtractedDocument(
            text="EAP772\nDimensions: 220 x 220 x 32.5 mm",
            final_url="",
            content=b"%PDF-retain",
            page_count=1,
            is_pdf=True,
        )
        result = process_datasheet_ingestion(self.make_ingestion().pk)

        self.assertEqual(result.status, DatasheetIngestion.Status.VALIDATED)
        self.assertEqual(result.extracted_spec_count, 0)
        self.assertEqual(result.retained_spec_count, 1)
        self.assertEqual(
            ProductSpec.objects.get(
                product=self.product,
                definition=self.dimensions,
            ).value_text,
            "Original human value",
        )

    @patch("catalog.datasheets.extract_specs_with_ai")
    @patch("catalog.datasheets.ai_is_configured", return_value=True)
    @patch("catalog.datasheets.read_uploaded_document")
    def test_rule_result_avoids_ai_and_overwrites_previous_automated_value(
        self,
        read_document,
        ai_configured,
        extract_ai,
    ):
        ProductSpec.objects.create(
            product=self.product,
            definition=self.dimensions,
            value_text="Old automated value",
            source_note="已校验型号，并从 Datasheet 自动提取。",
        )
        read_document.return_value = ExtractedDocument(
            text="EAP772\nDimensions: 220 x 220 x 32.5 mm",
            final_url="",
            content=b"%PDF-ai",
            page_count=2,
            is_pdf=True,
        )
        result = process_datasheet_ingestion(self.make_ingestion().pk)

        result.refresh_from_db()
        self.assertEqual(
            result.extraction_method,
            DatasheetIngestion.ExtractionMethod.RULES,
        )
        self.assertEqual(result.ai_spec_count, 0)
        extract_ai.assert_not_called()
        spec = ProductSpec.objects.get(
            product=self.product,
            definition=self.dimensions,
        )
        self.assertEqual(spec.value_text, "220 x 220 x 32.5 mm")
        self.assertNotIn("AI", spec.source_note)

    def test_private_network_url_is_rejected(self):
        with self.assertRaises(DatasheetValidationError):
            validate_public_url("http://127.0.0.1/datasheet.pdf", ("127.0.0.1",))

    def test_non_official_domain_is_rejected_before_fetch(self):
        with self.assertRaisesMessage(
            DatasheetValidationError,
            "官方域名",
        ):
            validate_public_url(
                "https://malicious.example/EAP772.pdf",
                ("tp-link.com",),
            )

    def test_embedded_pdf_url_is_discovered_without_href(self):
        html = (
            b'<script>window.downloadGuide="https:\\/\\/files.tp-link.com'
            b'\\/datasheets\\/EAP772.pdf";</script>'
        )
        self.assertEqual(
            _html_pdf_links(html, "https://www.tp-link.com/product/eap772/"),
            ["https://files.tp-link.com/datasheets/EAP772.pdf"],
        )

    @patch("catalog.datasheets.fetch_url_document")
    def test_url_ingestion_uses_submitted_url_before_product_is_updated(
        self, fetch_document
    ):
        submitted_url = "https://www.tp-link.com/EAP772-datasheet.pdf"
        fetch_document.return_value = ExtractedDocument(
            text="TP-Link EAP772 Datasheet\nDimensions: 220 x 220 x 32.5 mm",
            final_url=submitted_url,
            content=b"%PDF-url",
            page_count=1,
            is_pdf=True,
        )
        ingestion = DatasheetIngestion.objects.create(
            product=self.product,
            source_type=DatasheetIngestion.SourceType.URL,
            source_url=submitted_url,
        )

        result = process_datasheet_ingestion(ingestion.pk)

        self.assertEqual(result.status, DatasheetIngestion.Status.VALIDATED)
        fetched_product, fetched_url = fetch_document.call_args.args
        self.assertEqual(fetched_product.pk, self.product.pk)
        self.assertEqual(fetched_url, submitted_url)
        self.product.refresh_from_db()
        self.assertEqual(self.product.datasheet_url, submitted_url)

    @patch("catalog.datasheets.extract_specs_with_ai")
    @patch("catalog.datasheets.ai_is_configured", return_value=True)
    @patch("catalog.datasheets.extract_specs")
    @patch("catalog.datasheets.template_fields")
    @patch("catalog.datasheets.read_uploaded_document")
    def test_ai_receives_only_fields_missing_after_rules(
        self,
        read_document,
        template_fields,
        extract_rules,
        ai_configured,
        extract_ai,
    ):
        power = SpecDefinition.objects.create(
            category=self.category,
            code="max_power_consumption_w",
            display_name="Maximum Power Consumption",
            group="Power",
            data_type=SpecDefinition.DataType.DECIMAL,
            unit="W",
            is_core=True,
        )
        template_fields.return_value = [
            SimpleNamespace(spec_definition=self.dimensions),
            SimpleNamespace(spec_definition=power),
        ]
        extract_rules.return_value = {
            "dimensions_mm": ("text", "220 x 220 x 32.5 mm", "Dimensions")
        }
        read_document.return_value = ExtractedDocument(
            text="EAP772 specifications",
            final_url="",
            content=b"%PDF-routing",
            page_count=2,
            is_pdf=True,
        )
        extract_ai.return_value = SimpleNamespace(
            specs={
                "max_power_consumption_w": ("number", 24, "Maximum power 24 W")
            },
            metadata={
                "max_power_consumption_w": {
                    "page_number": 2,
                    "confidence": 0.95,
                    "method": "ai",
                }
            },
            matched_model="EAP772",
            model_name="qwen3:1.7b",
            average_confidence=0.95,
            metrics={"input_page_count": 2},
        )

        result = process_datasheet_ingestion(self.make_ingestion().pk)

        self.assertEqual(result.status, DatasheetIngestion.Status.VALIDATED)
        ai_items = extract_ai.call_args.args[2]
        self.assertEqual(
            [item.spec_definition.code for item in ai_items],
            ["max_power_consumption_w"],
        )

    @patch("catalog.datasheets.extract_specs_with_ai")
    @patch("catalog.datasheets.read_uploaded_document")
    def test_identical_document_reuses_adaptive_pipeline_result(
        self, read_document, extract_ai
    ):
        content = b"%PDF-cached"
        ProductSpec.objects.create(
            product=self.product,
            definition=self.dimensions,
            value_text="220 x 220 x 32.5 mm",
        )
        cached = DatasheetIngestion.objects.create(
            product=self.product,
            source_type=DatasheetIngestion.SourceType.UPLOAD,
            status=DatasheetIngestion.Status.VALIDATED,
            file_sha256=hashlib.sha256(content).hexdigest(),
            extraction_details='{"pipeline_version":"adaptive-v1","cache_hit":false}',
            detected_model="EAP772",
            extraction_method=DatasheetIngestion.ExtractionMethod.HYBRID,
            ai_model="qwen3:1.7b",
            ai_spec_count=1,
        )
        read_document.return_value = ExtractedDocument(
            text="EAP772 Dimensions: 220 x 220 x 32.5 mm",
            final_url="",
            content=content,
            page_count=2,
            is_pdf=True,
        )

        result = process_datasheet_ingestion(self.make_ingestion().pk)

        self.assertEqual(result.status, DatasheetIngestion.Status.VALIDATED)
        self.assertIn("复用", result.validation_message)
        self.assertIn(f'"cached_ingestion_id":{cached.pk}', result.extraction_details)
        extract_ai.assert_not_called()
