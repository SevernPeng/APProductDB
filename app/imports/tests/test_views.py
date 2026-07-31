import tempfile

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from audit.models import AuditLog
from catalog.models import Product, ProductType
from imports.models import ImportJob

from .helpers import workbook_upload


class ImportViewTests(TestCase):
    def setUp(self):
        self.media = tempfile.TemporaryDirectory()
        self.override = override_settings(MEDIA_ROOT=self.media.name)
        self.override.enable()
        self.addCleanup(self.override.disable)
        self.addCleanup(self.media.cleanup)
        self.admin = get_user_model().objects.create_superuser("admin", password="secret")
        self.viewer = get_user_model().objects.create_user("viewer", password="secret")
        call_command("initialize_catalog", verbosity=0)

    def test_only_superusers_can_open_import_page(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("imports:upload"))
        self.assertEqual(response.status_code, 302)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("imports:upload"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '<details class="import-template-group"',
            count=5,
        )
        self.assertNotContains(response, 'data-bs-toggle="collapse"')

    def test_upload_validates_but_requires_separate_confirmation(self):
        self.client.force_login(self.admin)
        product_type = ProductType.objects.get(
            category__slug="access-point", code="ceiling"
        )
        response = self.client.post(
            reverse("imports:upload"),
            {
                "product_type": product_type.pk,
                "mode": ImportJob.Mode.CREATE_ONLY,
                "uploaded_file": workbook_upload(),
            },
        )
        job = ImportJob.objects.get()
        self.assertRedirects(response, reverse("imports:detail", args=(job.pk,)))
        self.assertEqual(job.status, ImportJob.Status.READY)
        self.assertEqual(Product.objects.count(), 0)
        response = self.client.post(reverse("imports:detail", args=(job.pk,)), follow=True)
        self.assertContains(response, "Excel 已在单一数据库事务中导入成功")
        self.assertEqual(Product.objects.count(), 2)
        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.admin,
                action="excel_import.completed",
                object_id=str(job.pk),
            ).exists()
        )

    def test_non_xlsx_file_is_rejected_before_job_creation(self):
        self.client.force_login(self.admin)
        product_type = ProductType.objects.get(
            category__slug="access-point", code="ceiling"
        )
        upload = workbook_upload(filename="invalid.xls")
        response = self.client.post(
            reverse("imports:upload"),
            {
                "product_type": product_type.pk,
                "mode": ImportJob.Mode.PREVIEW,
                "uploaded_file": upload,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "只支持 .xlsx 文件")
        self.assertFalse(ImportJob.objects.exists())

    def test_source_workbook_download_requires_superuser(self):
        job = ImportJob.objects.create(
            uploaded_file=workbook_upload(),
            uploaded_by=self.admin,
            mode=ImportJob.Mode.PREVIEW,
        )
        url = reverse("imports:source_file", args=(job.pk,))
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.admin)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(len(b"".join(response.streaming_content)), 0)
        response.close()

    def test_product_type_template_download_is_available(self):
        self.client.force_login(self.admin)
        product_type = ProductType.objects.get(
            category__slug="accessories", code="optical_module"
        )
        response = self.client.get(
            reverse("imports:download_template", args=(product_type.pk,))
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertGreater(len(b"".join(response.streaming_content)), 0)
        response.close()
