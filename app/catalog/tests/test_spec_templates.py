from decimal import Decimal

from django.core.management import call_command
from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition
from catalog.services import template_definitions, template_fields
from comparison.services import build_comparison_rows


class ProductTypeTemplateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("initialize_catalog", verbosity=0)

    def test_each_product_category_has_its_own_fields(self):
        gateway = Category.objects.get(slug="gateway")
        managed = Category.objects.get(slug="managed-switches")
        gateway_codes = {item.code for item in template_definitions(gateway)}
        managed_codes = {item.code for item in template_definitions(managed)}

        self.assertIn("vpn_throughput_mbps", gateway_codes)
        self.assertNotIn("switching_capacity_gbps", gateway_codes)
        self.assertIn("switching_capacity_gbps", managed_codes)
        self.assertIn("poe_budget_w", managed_codes)
        self.assertNotIn("supported_bands", managed_codes)

    def test_managed_switch_comparison_does_not_show_ap_fields(self):
        brand = Brand.objects.get(name="TP-Link")
        category = Category.objects.get(slug="managed-switches")
        first = Product.objects.create(brand=brand, category=category, model="SG3428X")
        second = Product.objects.create(brand=brand, category=category, model="SG3452X")
        capacity = SpecDefinition.objects.get(code="switching_capacity_gbps")
        bands = SpecDefinition.objects.get(code="supported_bands")
        ProductSpec.objects.create(product=first, definition=capacity, value_number=Decimal("128"))
        ProductSpec.objects.create(product=second, definition=capacity, value_number=Decimal("176"))
        ProductSpec.objects.create(product=first, definition=bands, value_text="2.4 / 5 GHz")

        rows = build_comparison_rows([first, second])
        codes = {row["code"] for row in rows}

        self.assertIn("switching_capacity_gbps", codes)
        self.assertNotIn("poe_standard", codes)
        self.assertNotIn("supported_bands", codes)
        self.assertNotIn("ap_type", codes)
        self.assertNotIn("wifi_standard", codes)

    def test_unmanaged_operational_features_are_all_p0(self):
        category = Category.objects.get(slug="unmanaged-easy-smart-switches")
        template = category.comparison_templates.get(active=True, form_factor="")
        priorities = dict(
            template.fields.filter(
                spec_definition__code__in={
                    "extend_mode",
                    "poe_auto_recovery",
                    "port_isolation",
                    "loop_prevention",
                }
            ).values_list("spec_definition__code", "priority")
        )

        self.assertEqual(
            priorities,
            {
                "extend_mode": "p0",
                "poe_auto_recovery": "p0",
                "port_isolation": "p0",
                "loop_prevention": "p0",
            },
        )

    def test_unmanaged_template_uses_independent_feature_fields(self):
        category = Category.objects.get(slug="unmanaged-easy-smart-switches")
        fields_by_code = {
            field.spec_definition.code: field
            for field in template_fields(category)
        }

        for code in {
            "management_type",
            "vlan_support",
            "qos_support",
            "link_aggregation",
            "igmp_snooping",
            "port_mirroring",
            "cable_test",
            "installation",
        }:
            self.assertIn(code, fields_by_code)
        self.assertNotIn("easy_smart_features", fields_by_code)
        self.assertEqual(fields_by_code["mac_address_table"].priority, "p1")
        self.assertEqual(fields_by_code["fanless"].priority, "p1")
        self.assertEqual(fields_by_code["dimensions_mm"].priority, "p2")
        self.assertEqual(fields_by_code["operating_temperature_c"].priority, "p2")

    def test_template_fields_preserve_priority_and_display_group(self):
        category = Category.objects.get(slug="managed-switches")
        fields_by_code = {
            field.spec_definition.code: field
            for field in template_fields(category)
        }

        self.assertEqual(fields_by_code["switching_capacity_gbps"].priority, "p0")
        self.assertEqual(fields_by_code["switching_capacity_gbps"].display_group, "Performance")
        self.assertEqual(fields_by_code["mac_address_table"].priority, "p1")
        self.assertEqual(fields_by_code["dimensions_mm"].priority, "p2")

    def test_comparison_hides_p2_by_default_and_can_include_it(self):
        brand = Brand.objects.get(name="TP-Link")
        category = Category.objects.get(slug="managed-switches")
        first = Product.objects.create(brand=brand, category=category, model="SG-P2-A")
        second = Product.objects.create(brand=brand, category=category, model="SG-P2-B")
        dimensions = SpecDefinition.objects.get(code="dimensions_mm")
        ProductSpec.objects.create(
            product=first,
            definition=dimensions,
            value_text="440 × 330 × 44",
        )

        default_codes = {row["code"] for row in build_comparison_rows([first, second])}
        extended_rows = build_comparison_rows(
            [first, second], include_extended=True
        )
        extended_by_code = {row["code"]: row for row in extended_rows}

        self.assertNotIn("dimensions_mm", default_codes)
        self.assertEqual(extended_by_code["dimensions_mm"]["priority"], "p2")
