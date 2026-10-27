from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductSpec, ProductType, SpecDefinition
from catalog.wireless import add_band_width_row, ensure_band_width, product_has_wifi


class WirelessFieldTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        self.gateway = Category.objects.create(name="Gateway", slug="gateway")
        self.width, _ = SpecDefinition.objects.get_or_create(code="max_channel_width_mhz",
            defaults={"display_name": "Band Width", "data_type": "integer", "unit": "MHz"})

    def test_wired_router_ignores_generic_extracted_wifi_text(self):
        product = Product.objects.create(brand=self.brand, category=self.gateway, model="ER605")
        definition = SpecDefinition.objects.create(code="router_wifi_standard", display_name="Wi-Fi Standard")
        ProductSpec.objects.create(product=product, definition=definition, value_text="Wi-Fi 7")
        self.assertFalse(product_has_wifi(product))
        ensure_band_width(product)
        self.assertEqual(add_band_width_row(product, []), [])
        self.assertFalse(product.specs.filter(definition=self.width).exists())

    def test_cellular_wifi_router_has_one_editable_width_and_retains_values(self):
        product = Product.objects.create(brand=self.brand, category=self.gateway, model="ER706W-4G")
        radio = SpecDefinition.objects.create(code="matrix-gateway-010", display_name="Wi-Fi Frequency & Signal Rate")
        ProductSpec.objects.create(product=product, definition=radio, value_text="5 GHz: 2402 Mbps")
        self.assertTrue(product_has_wifi(product))
        ensure_band_width(product)
        width = product.specs.get(definition=self.width)
        self.assertEqual(width.value_status, "unknown")
        width.value_status = "published"
        width.value_number = 160
        width.save()
        ensure_band_width(product)
        rows = add_band_width_row(product, add_band_width_row(product, []))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["display_name"], "Band Width")
        self.assertEqual(rows[0]["display_value"], "160 MHz")

    def test_wireless_router_type_and_bridges_are_covered_without_values(self):
        kind = ProductType.objects.create(category=self.gateway, code="wireless_router", name="Wireless Router")
        product = Product.objects.create(brand=self.brand, category=self.gateway, product_type=kind, model="Wireless")
        bridge = Product.objects.create(brand=self.brand,
            category=Category.objects.create(name="Bridge", slug="wireless-bridge"), model="Bridge")
        for item in (product, bridge):
            self.assertTrue(product_has_wifi(item))
            ensure_band_width(item)
            self.assertEqual(add_band_width_row(item, [])[0]["display_value"], "Unknown")
