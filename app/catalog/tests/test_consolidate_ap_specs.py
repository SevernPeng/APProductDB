from django.core.management import call_command
from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition


class ConsolidateAPSpecsCommandTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("initialize_catalog", verbosity=0)
        cls.brand = Brand.objects.get(name="Ubiquiti")
        cls.category = Category.objects.get(slug="access-point")
        cls.ethernet = SpecDefinition.objects.get(code="ethernet_interfaces")
        cls.power = SpecDefinition.objects.get(code="power_method")
        cls.poe = SpecDefinition.objects.get(code="poe_input")
        cls.uplink = SpecDefinition.objects.create(
            code="uplink_interface",
            display_name="Uplink",
            group="Interfaces",
            category=cls.category,
            data_type="text",
        )
        cls.networking = SpecDefinition.objects.create(
            code="networking_interface",
            display_name="Networking Interface",
            group="Interfaces",
            category=cls.category,
            data_type="text",
        )

    def test_merges_wall_ports_and_power_then_removes_obsolete_fields(self):
        product = Product.objects.create(
            brand=self.brand,
            category=self.category,
            model="U6-IW",
            ap_type=Product.APType.WALL_PLATE,
        )
        ProductSpec.objects.create(product=product, definition=self.uplink, value_text="GbE")
        ProductSpec.objects.create(
            product=product,
            definition=self.networking,
            value_text="(1) Data-in: GbE RJ45 port; (4) Data-out: GbE RJ45 ports",
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.poe,
            value_text="802.3af / 802.3at",
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.power,
            value_text="PoE+; 48 V DC optional",
        )

        call_command("consolidate_ap_interface_power_specs", apply=True, verbosity=0)

        ethernet = ProductSpec.objects.get(product=product, definition=self.ethernet)
        power = ProductSpec.objects.get(product=product, definition=self.power)
        self.assertIn("Uplink/Data-in", ethernet.value_text)
        self.assertIn("Downlink/Data-out", ethernet.value_text)
        self.assertEqual(power.value_text, "PoE (802.3af / 802.3at) / DC (48 V)")
        self.assertFalse(SpecDefinition.objects.filter(code="uplink_interface").exists())
        self.assertFalse(SpecDefinition.objects.filter(code="networking_interface").exists())
        self.assertFalse(ProductSpec.objects.filter(product=product, definition=self.poe).exists())
