from datetime import date
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from catalog.models import Brand, Category, Product
from catalog.nom import has_current_nom, matches_product, parse_identity, read_tracker


def evidence(**overrides):
    return {
        "model_key": "EAP772", "regions": ["US"], "versions": ["1.0", "2.20"],
        "ready": True,
        "certificates": [{"number": "ANC123", "permanent": True, "expires_on": None}],
        **overrides,
    }


class NomEvidenceTests(SimpleTestCase):
    def test_exact_model_region_and_version_matching(self):
        product = Product(model_key="EAP772", region="US", hardware_version="V1")
        self.assertTrue(matches_product(evidence(), product))
        product.hardware_version = "V2"
        self.assertFalse(matches_product(evidence(), product))
        product.hardware_version = ""
        self.assertTrue(matches_product(evidence(), product))
        product.region = "EU"
        self.assertFalse(matches_product(evidence(), product))
        product.region = "US"
        product.model_key = "EAP772OUTDOOR"
        self.assertFalse(matches_product(evidence(), product))

    def test_parse_model_with_multiple_regions_and_versions(self):
        self.assertEqual(parse_identity("EAP772(US)(EU) V1.0, V2.20"),
                         ("EAP772", ["US", "EU"], ["1.0", "2.20"]))
        self.assertEqual(parse_identity("EAP610 V1.0, V2.20"),
                         ("EAP610", [], ["1.0", "2.20"]))
        self.assertEqual(parse_identity("EAP650 D120-Outdoor (US) V1.20")[0],
                         "EAP650D120OUTDOOR")

    def test_only_ready_and_current_certificates_display(self):
        today = date(2026, 9, 14)
        self.assertFalse(has_current_nom([], today))
        self.assertFalse(has_current_nom([evidence(ready=False)], today))
        self.assertFalse(has_current_nom([evidence(certificates=[])], today))
        self.assertTrue(has_current_nom([evidence()], today))
        for expiry, expected in [("2026-09-13", False), ("2026-09-14", True),
                                 ("2027-01-01", True), (None, False)]:
            with self.subTest(expiry=expiry):
                record = evidence(certificates=[{
                    "number": "NYC123", "permanent": False, "expires_on": expiry,
                }])
                self.assertEqual(has_current_nom([record], today), expected)

    @patch("xlrd.open_workbook")
    def test_read_tracker_ignores_na_and_ift_only(self, open_workbook):
        from unittest.mock import Mock

        row = [""] * 29
        row[0:2] = ["EAP772 (US) V1.0", "YES"]
        row[5], row[8], row[9], row[12] = "N/A", "IFT123", "-", "NYC123"
        row[14] = 46279  # 2026-09-14 in Excel's 1900 date system.
        sheet = Mock(name="sheet")
        sheet.name, sheet.nrows = "NOM_2026", 6
        headers = {(3, 0): "MODELS", (3, 1): "READY"}
        for standard, col in [("NOM-001", 5), ("NOM-208", 9), ("NOM-019", 12),
                              ("NOM-003", 21), ("NOM-030", 24)]:
            group_col = 8 if standard == "NOM-208" else col
            headers[(2, group_col)], headers[(3, col)] = standard, "CERTIFICATE"
        sheet.cell_value.side_effect = lambda r, c: headers[(r, c)]
        sheet.row_values.return_value = row
        open_workbook.return_value.sheet_by_name.return_value = sheet
        open_workbook.return_value.datemode = 0
        records = read_tracker(Path("tracker.xls"))
        self.assertEqual(records[0]["row"], 6)
        self.assertEqual(len(records[0]["certificates"]), 1)
        self.assertEqual(records[0]["certificates"][0]["expires_on"], "2026-09-14")


class NomImportAndDisplayTests(TestCase):
    def setUp(self):
        brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        category = Category.objects.create(name="Access Point", slug="access-point")
        self.product = Product.objects.create(brand=brand, category=category, model="EAP772")
        self.other = Product.objects.create(
            brand=Brand.objects.create(name="Other", slug="other"),
            category=category, model="EAP772",
        )
        user = get_user_model().objects.create_user(username="nom-viewer")
        self.client.force_login(user)

    @patch("catalog.management.commands.import_nom_certifications.read_tracker")
    def test_import_is_scoped_idempotent_and_supports_dry_run(self, read):
        read.return_value = [evidence()]
        call_command("import_nom_certifications", "tracker.xls", dry_run=True, stdout=StringIO())
        self.product.refresh_from_db()
        self.assertFalse(self.product.has_nom)
        call_command("import_nom_certifications", "tracker.xls", stdout=StringIO())
        self.product.refresh_from_db()
        self.other.refresh_from_db()
        self.assertTrue(self.product.has_nom)
        self.assertFalse(self.other.has_nom)
        output = StringIO()
        call_command("import_nom_certifications", "tracker.xls", stdout=output)
        self.assertIn("0 products updated", output.getvalue())
        read.return_value = [evidence(ready=False)]
        call_command("import_nom_certifications", "tracker.xls", stdout=StringIO())
        self.product.refresh_from_db()
        self.assertFalse(self.product.has_nom)

    def test_badge_only_appears_for_certified_products_on_both_pages(self):
        urls = [reverse("product-list"), reverse("product-detail", args=[self.product.pk])]
        for records, visible in [([], False), ([evidence()], True),
                                 ([evidence(ready=False)], False)]:
            Product.objects.filter(pk=self.product.pk).update(nom_records=records)
            for url in urls:
                with self.subTest(url=url, visible=visible):
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, 200)
                    if visible:
                        self.assertContains(response, '>NOM</span>', count=1)
                    else:
                        self.assertNotContains(response, '>NOM</span>')
