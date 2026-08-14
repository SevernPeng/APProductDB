from django.core.management import call_command
from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition


class InferWirelessBandsCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("initialize_catalog", verbosity=0)
        cls.brand = Brand.objects.get(name="Ubiquiti")
        cls.category = Category.objects.get(slug="access-point")
        cls.definition = SpecDefinition.objects.get(code="supported_bands")

    def product(self, model, standard):
        return Product.objects.create(
            brand=self.brand,
            category=self.category,
            model=model,
            wifi_standard=standard,
        )

    def test_infers_supported_bands_for_wifi_6_6e_and_7(self):
        wifi6 = self.product("W6", "Wi-Fi 6")
        wifi6e = self.product("W6E", "Wi-Fi 6E")
        wifi7 = self.product("W7", "Wi-Fi 7")

        call_command("infer_wireless_bands", apply=True, verbosity=0)

        values = {
            item.product_id: item.value_text
            for item in ProductSpec.objects.filter(
                product__in=(wifi6, wifi6e, wifi7),
                definition=self.definition,
                value_status=ProductSpec.ValueStatus.PUBLISHED,
            )
        }
        self.assertEqual(values[wifi6.id], "2.4 GHz / 5 GHz")
        self.assertEqual(values[wifi6e.id], "2.4 GHz / 5 GHz / 6 GHz")
        self.assertEqual(values[wifi7.id], "2.4 GHz / 5 GHz / 6 GHz")

    def test_does_not_override_official_product_specific_bands(self):
        product = self.product("W7-DUAL", "Wi-Fi 7")
        ProductSpec.objects.create(
            product=product,
            definition=self.definition,
            value_status=ProductSpec.ValueStatus.PUBLISHED,
            value_text="2.4 GHz / 5 GHz",
            source_note="Official dual-band specification.",
        )

        call_command("infer_wireless_bands", apply=True, verbosity=0)

        spec = ProductSpec.objects.get(product=product, definition=self.definition)
        self.assertEqual(spec.value_text, "2.4 GHz / 5 GHz")
        self.assertEqual(spec.source_note, "Official dual-band specification.")
