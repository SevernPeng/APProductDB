import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from catalog.models import Product, ProductSpec, ProductType
from comparison.models import ProductMatch
from imports.models import ImportJob
from imports.services import execute_import_job, validate_import_job

from .helpers import (
    create_job,
    product_row,
    product_type_workbook_upload,
    workbook_upload,
)


class ImportServiceTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media.cleanup)
        self.user = get_user_model().objects.create_superuser("importer", password="secret")
        call_command("initialize_catalog", verbosity=0)

    def validate(self, upload=None, mode=ImportJob.Mode.PREVIEW):
        job = create_job(self.user, upload or workbook_upload(), mode)
        plan = validate_import_job(job)
        job.refresh_from_db()
        return job, plan

    def test_preview_validates_without_writing_and_recalculates_aggregate(self):
        job, plan = self.validate()
        self.assertEqual(job.status, ImportJob.Status.READY)
        self.assertEqual((job.total_rows, job.valid_rows, job.error_rows), (3, 3, 0))
        self.assertEqual((len(plan.products), len(plan.matches)), (2, 1))
        self.assertEqual(plan.products[0].aggregate_rate, 10777)
        self.assertEqual(Product.objects.count(), 0)

    def test_missing_sheet_is_reported(self):
        job, plan = self.validate(workbook_upload(missing_sheet="Match Map"))
        self.assertEqual(job.status, ImportJob.Status.INVALID)
        self.assertIn("missing_sheet", {issue.error_code for issue in plan.issues})

    def test_missing_required_column_is_reported(self):
        job, plan = self.validate(workbook_upload(missing_spec_column="Official Source"))
        self.assertEqual(job.status, ImportJob.Status.INVALID)
        self.assertIn("missing_column", {issue.error_code for issue in plan.issues})

    def test_duplicate_product_reports_excel_row(self):
        upload = workbook_upload(products=[product_row(), product_row()])
        job, plan = self.validate(upload)
        issue = next(issue for issue in plan.issues if issue.error_code == "duplicate_product")
        self.assertEqual((issue.sheet_name, issue.row_number), ("Spec Data", 3))
        self.assertTrue(job.error_report.name.endswith(".csv"))

    def test_non_numeric_rate_is_rejected(self):
        upload = workbook_upload(products=[product_row(**{"5 GHz Max Rate (Mbps)": "fast"})], matches=[])
        _, plan = self.validate(upload)
        self.assertIn("invalid_number", {issue.error_code for issue in plan.issues})

    def test_invalid_url_is_rejected(self):
        upload = workbook_upload(products=[product_row(**{"Official Source": "not a url"})], matches=[])
        _, plan = self.validate(upload)
        self.assertIn("invalid_url", {issue.error_code for issue in plan.issues})

    def test_unknown_match_product_is_rejected(self):
        upload = workbook_upload(matches=[["EAP-TEST", "Ubiquiti", "MISSING", "", ""]])
        _, plan = self.validate(upload)
        self.assertIn("unknown_product", {issue.error_code for issue in plan.issues})

    def test_duplicate_match_is_rejected(self):
        upload = workbook_upload(matches=[["EAP-TEST", "Ubiquiti", "U7-TEST", "Ubiquiti", "U7-TEST"]])
        _, plan = self.validate(upload)
        self.assertIn("duplicate_match", {issue.error_code for issue in plan.issues})

    def test_create_only_imports_products_specs_and_match(self):
        job, _ = self.validate(mode=ImportJob.Mode.CREATE_ONLY)
        counters = execute_import_job(job)
        self.assertEqual(counters["products_created"], 2)
        self.assertEqual(counters["matches_created"], 1)
        self.assertEqual(Product.objects.count(), 2)
        self.assertEqual(ProductMatch.objects.count(), 1)
        self.assertGreater(ProductSpec.objects.count(), 20)
        job.refresh_from_db()
        self.assertEqual(job.status, ImportJob.Status.IMPORTED)

    def test_create_only_rejects_existing_product(self):
        first_job, _ = self.validate(mode=ImportJob.Mode.CREATE_ONLY)
        execute_import_job(first_job)
        second_job, plan = self.validate(mode=ImportJob.Mode.CREATE_ONLY)
        self.assertEqual(second_job.status, ImportJob.Status.INVALID)
        self.assertIn("product_exists", {issue.error_code for issue in plan.issues})

    def test_create_and_update_updates_existing_product_and_specs(self):
        first_job, _ = self.validate(mode=ImportJob.Mode.CREATE_ONLY)
        execute_import_job(first_job)
        products = [
            product_row(**{"Data Notes": "Updated", "5 GHz Max Rate (Mbps)": 5000}),
            product_row(brand="Ubiquiti", model="U7-TEST"),
        ]
        second_job, _ = self.validate(workbook_upload(products=products), ImportJob.Mode.CREATE_UPDATE)
        counters = execute_import_job(second_job)
        self.assertEqual(counters["products_updated"], 2)
        product = Product.objects.get(model_key="EAPTEST")
        self.assertEqual(product.notes, "Updated")
        self.assertEqual(product.aggregate_rate_mbps, 11453)

    def test_serious_error_rolls_back_entire_import(self):
        job, _ = self.validate(mode=ImportJob.Mode.CREATE_ONLY)
        with patch("imports.services.ProductMatch.save", side_effect=RuntimeError("forced failure")):
            with self.assertRaises(RuntimeError):
                execute_import_job(job)
        self.assertEqual(Product.objects.count(), 0)
        self.assertEqual(ProductSpec.objects.count(), 0)
        self.assertEqual(ProductMatch.objects.count(), 0)
        job.refresh_from_db()
        self.assertEqual(job.status, ImportJob.Status.FAILED)

    def test_product_type_template_validates_and_imports(self):
        product_type = ProductType.objects.get(
            category__slug="accessories",
            code="optical_module",
        )
        upload = product_type_workbook_upload(
            product_type,
            products=[
                {
                    "brand": "TP-Link",
                    "model": "SM-TEST",
                    "region": "Global",
                    "hardware_version": "V1",
                    "lifecycle_status": "active",
                    "official_url": "https://example.com/sm-test",
                    "last_verified": "2026-07-27",
                    "accessory_data_rate_gbps": 10,
                    "accessory_wavelength_nm": 1310,
                }
            ],
        )
        job = create_job(
            self.user,
            upload,
            ImportJob.Mode.CREATE_ONLY,
            product_type=product_type,
        )
        validate_import_job(job)
        job.refresh_from_db()
        self.assertEqual(job.status, ImportJob.Status.READY)
        execute_import_job(job)
        product = Product.objects.get(model="SM-TEST")
        self.assertEqual(product.product_type, product_type)
        self.assertTrue(
            ProductSpec.objects.filter(
                product=product,
                definition__code="accessory_data_rate_gbps",
                value_number=10,
            ).exists()
        )

    def test_product_type_template_rejects_metadata_mismatch(self):
        product_type = ProductType.objects.get(
            category__slug="managed-switches",
            code="l2",
        )
        job = create_job(
            self.user,
            product_type_workbook_upload(
                product_type,
                metadata_product_type_code="l3",
            ),
            product_type=product_type,
        )
        plan = validate_import_job(job)
        self.assertTrue(
            any(issue.error_code == "template_mismatch" for issue in plan.issues)
        )
