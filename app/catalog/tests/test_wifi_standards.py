from io import StringIO

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Brand, Category, Product
from catalog.wifi_standards import omada_wifi_standard
from comparison.models import ProductMatch


class WifiStandardTests(TestCase):
    def setUp(self):
        self.own = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        self.other = Brand.objects.create(name="Other", slug="other")
        self.category = Category.objects.create(name="Access Point", slug="access-point")

    def product(self, model, brand=None, category=None):
        return Product.objects.create(model=model, brand=brand or self.own,
            category=category or self.category, wifi_standard="Unknown")

    def test_generation_and_bridge_exclusion(self):
        for model, standard in (("EAP787", "Wi-Fi 7"), ("EAP650-Wall", "Wi-Fi 6"),
                                ("EAP225", "Wi-Fi 5"), ("EAP115", "Wi-Fi 4")):
            self.assertEqual(omada_wifi_standard(self.product(model)), standard)
        bridge = Category.objects.create(name="Bridge", slug="wireless-bridge")
        self.assertIsNone(omada_wifi_standard(self.product("EAP115-Bridge KIT", category=bridge)))
        self.assertIsNone(omada_wifi_standard(self.product("EAP225", brand=self.other)))

    def test_sync_dry_run_idempotence_and_conflicts(self):
        anchor = self.product("EAP225")
        competitor = self.product("COMP", brand=self.other)
        ProductMatch.objects.create(our_product=anchor, competitor_product=competitor,
                                    match_type="direct", status="confirmed")
        call_command("sync_wifi_standards", dry_run=True, stdout=StringIO())
        competitor.refresh_from_db()
        self.assertEqual(competitor.wifi_standard, "Unknown")
        for _ in range(2):
            call_command("sync_wifi_standards", stdout=StringIO())
        competitor.refresh_from_db()
        self.assertEqual(competitor.wifi_standard, "Wi-Fi 5")
        anchor.refresh_from_db()
        self.assertEqual(anchor.wifi_standard, "Wi-Fi 5")
        newer = self.product("EAP650")
        ProductMatch.objects.create(our_product=newer, competitor_product=competitor,
                                    match_type="direct", status="confirmed")
        call_command("sync_wifi_standards", stdout=StringIO())
        competitor.refresh_from_db()
        self.assertEqual(competitor.wifi_standard, "Wi-Fi 5")
