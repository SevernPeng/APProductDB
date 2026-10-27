from decimal import Decimal
from io import StringIO

from django.core.management import call_command, CommandError
from django.test import TestCase

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition
from catalog.services import ensure_product_spec_placeholders
from catalog.product_types import infer_managed_switch_poe, infer_product_type_code
from catalog.spec_applicability import (
    field_is_applicable,
    switch_poe_state,
    switch_stacking_state,
)


class SpecApplicabilityTests(TestCase):
    def test_tp_link_tl_sx_family_is_unmanaged(self):
        self.assertEqual(
            infer_product_type_code(
                "unmanaged-easy-smart-switches", "TL-SX105"
            ),
            "unmanaged_non_poe",
        )

    def test_published_management_type_overrides_unknown_model_family(self):
        self.assertEqual(
            infer_product_type_code(
                "unmanaged-easy-smart-switches",
                "XS505M",
                management_type="Unmanaged",
            ),
            "unmanaged_non_poe",
        )

    def test_management_features_override_unmanaged_marketing_label(self):
        self.assertEqual(
            infer_product_type_code(
                "unmanaged-easy-smart-switches",
                "GS105E",
                management_type="Unmanaged",
                has_management_features=True,
            ),
            "easy_smart_non_poe",
        )

    def test_competitor_managed_switch_family_inference(self):
        cases = (
            ("RUCKUS", "ICX 8200-24P", True, "campus_poe"),
            ("RUCKUS", "ICX 8200-48PF2", True, "campus_poe"),
            ("RUCKUS", "ICX 8200-48ZP2", True, "campus_poe"),
            ("RUCKUS", "ICX8100-24P", True, "l2_poe"),
            ("D-Link", "DGS-1210-28", False, "l2_non_poe"),
            ("D-Link", "DIS-210G-06P", True, "industrial_poe"),
            ("Cisco", "C1300-24T-4X", False, "l3_non_poe"),
            ("Reyee", "RG-ES228GS-P", True, "l2_poe"),
        )
        for brand, model, has_poe, expected in cases:
            with self.subTest(model=model):
                self.assertEqual(
                    infer_product_type_code(
                        "managed-switches",
                        model,
                        has_poe=has_poe,
                        brand_name=brand,
                    ),
                    expected,
                )

    def test_feature_text_promotes_unknown_managed_switch_to_l3(self):
        self.assertEqual(
            infer_product_type_code(
                "managed-switches",
                "Example 48T",
                has_poe=False,
                brand_name="Example",
                feature_text="Static routing, OSPF and PBR",
            ),
            "l3_non_poe",
        )

    def test_competitor_model_poe_signal_overrides_copied_family_values(self):
        self.assertIs(infer_managed_switch_poe("D-Link", "DGS-1210-28"), False)
        self.assertIs(infer_managed_switch_poe("D-Link", "DGS-1210-28MP"), True)
        self.assertIs(infer_managed_switch_poe("Cisco", "C9200L-24T-4X"), False)
        self.assertIs(infer_managed_switch_poe("Cisco", "C9200L-24P-4X"), True)
        self.assertIs(infer_managed_switch_poe("Instant On", "JL815A"), True)
        self.assertIs(infer_managed_switch_poe("Instant On", "JL814A"), False)

    @classmethod
    def setUpTestData(cls):
        call_command("initialize_catalog", verbosity=0)
        cls.brand = Brand.objects.get(name="TP-Link")
        cls.category = Category.objects.get(slug="unmanaged-easy-smart-switches")

    def make_product(self, model):
        return Product.objects.create(
            brand=self.brand,
            category=self.category,
            model=model,
            official_url=f"https://www.tp-link.com/en/business-networking/{model.lower()}/",
        )

    def test_tp_link_non_poe_switch_excludes_poe_fields(self):
        product = self.make_product("TL-SG108-M2")

        self.assertIs(switch_poe_state(product), False)
        self.assertFalse(field_is_applicable(product, "poe_budget_w"))
        self.assertFalse(field_is_applicable(product, "management_methods"))

        ensure_product_spec_placeholders(product)
        codes = set(product.specs.values_list("definition__code", flat=True))
        self.assertIn("switching_capacity_gbps", codes)
        self.assertNotIn("poe_standard", codes)
        self.assertNotIn("poe_budget_w", codes)

    def test_tp_link_poe_suffix_keeps_poe_fields(self):
        product = self.make_product("TL-SG1005P")

        self.assertIs(switch_poe_state(product), True)
        self.assertTrue(field_is_applicable(product, "poe_budget_w"))

        ensure_product_spec_placeholders(product)
        codes = set(product.specs.values_list("definition__code", flat=True))
        self.assertIn("poe_standard", codes)
        self.assertIn("poe_budget_w", codes)

    def test_non_tp_link_poe_suffix_keeps_poe_fields(self):
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=self.category,
            model="GS305P",
        )

        self.assertIs(switch_poe_state(product), True)
        self.assertTrue(field_is_applicable(product, "poe_budget_w"))

    def test_plain_unmanaged_switch_excludes_unpublished_config_fields(self):
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=self.category,
            model="GS305",
        )
        management = SpecDefinition.objects.get(code="management_type")
        ProductSpec.objects.create(
            product=product,
            definition=management,
            value_text="Unmanaged, plug-and-play",
            source_url="https://www.netgear.com/business/wired/switches/unmanaged/gs305/",
        )

        for code in (
            "port_isolation",
            "cable_test",
            "igmp_snooping",
            "link_aggregation",
            "loop_prevention",
            "port_mirroring",
            "vlan_support",
        ):
            with self.subTest(code=code):
                self.assertFalse(field_is_applicable(product, code))

    def test_published_unmanaged_switch_feature_remains_applicable(self):
        dlink = Brand.objects.create(name="D-Link", slug="d-link")
        product = Product.objects.create(
            brand=dlink,
            category=self.category,
            model="DES-F1017P-E",
        )
        management = SpecDefinition.objects.get(code="management_type")
        vlan = SpecDefinition.objects.get(code="vlan_support")
        ProductSpec.objects.create(
            product=product,
            definition=management,
            value_text="Unmanaged",
        )
        ProductSpec.objects.create(
            product=product,
            definition=vlan,
            value_text="Port isolation VLAN mode via DIP switch",
        )

        self.assertTrue(field_is_applicable(product, "vlan_support"))
        self.assertFalse(field_is_applicable(product, "link_aggregation"))

    def test_plus_switch_keeps_config_fields_applicable(self):
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=self.category,
            model="GS105E",
        )
        management = SpecDefinition.objects.get(code="management_type")
        ProductSpec.objects.create(
            product=product,
            definition=management,
            value_text="NETGEAR Plus web managed; PC Utility",
        )

        self.assertTrue(field_is_applicable(product, "vlan_support"))
        self.assertTrue(field_is_applicable(product, "link_aggregation"))

    def test_unknown_poe_state_does_not_expose_poe_placeholders(self):
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=self.category,
            model="XS505M",
        )

        self.assertIsNone(switch_poe_state(product))
        self.assertFalse(field_is_applicable(product, "poe_budget_w"))

        ensure_product_spec_placeholders(product)
        codes = set(product.specs.values_list("definition__code", flat=True))
        self.assertNotIn("poe_standard", codes)
        self.assertNotIn("poe_budget_w", codes)

    def test_published_unsupported_stacking_excludes_detail_fields(self):
        managed = Category.objects.get(slug="managed-switches")
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=managed,
            model="M4500-32C",
        )
        definition = SpecDefinition.objects.get(code="stacking")
        ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_text="Traditional switch stacking not supported; MLAG is supported",
        )

        self.assertIs(switch_stacking_state(product), False)
        self.assertFalse(field_is_applicable(product, "stacking_bandwidth_gbps"))
        self.assertFalse(field_is_applicable(product, "stacking_units"))
        self.assertFalse(field_is_applicable(product, "stacking_ports"))

    def test_published_supported_stacking_keeps_detail_fields(self):
        managed = Category.objects.get(slug="managed-switches")
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=managed,
            model="M4300-28G",
        )
        definition = SpecDefinition.objects.get(code="stacking")
        ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_text="Virtual Chassis stacking using any 10G port",
        )

        self.assertIs(switch_stacking_state(product), True)
        self.assertTrue(field_is_applicable(product, "stacking_bandwidth_gbps"))
        self.assertTrue(field_is_applicable(product, "stacking_units"))
        self.assertTrue(field_is_applicable(product, "stacking_ports"))

    def test_published_not_supported_prefix_excludes_stacking_details(self):
        managed = Category.objects.get(slug="managed-switches")
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=managed,
            model="M4200-10MG-PoE+",
        )
        definition = SpecDefinition.objects.get(code="stacking")
        ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_text=(
                "Not supported; stacking commands are supported on M4300 series "
                "switches only"
            ),
        )

        self.assertIs(switch_stacking_state(product), False)
        self.assertFalse(field_is_applicable(product, "stacking_bandwidth_gbps"))
        self.assertFalse(field_is_applicable(product, "stacking_units"))

    def test_copper_transceiver_excludes_optical_wavelength(self):
        accessory = Category.objects.get(slug="accessories")
        product = Product.objects.create(
            brand=self.brand,
            category=accessory,
            model="SFP-COPPER",
        )
        definition = SpecDefinition.objects.get(code="accessory_interface_type")
        ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_text="SFP 1000BASE-T RJ45 copper transceiver",
        )

        self.assertFalse(field_is_applicable(product, "accessory_wavelength_nm"))

    def test_dac_cable_excludes_chassis_dimensions(self):
        accessory = Category.objects.get(slug="accessories")
        product = Product.objects.create(
            brand=self.brand,
            category=accessory,
            model="DAC-1M",
        )
        product.product_type = product.product_model.category.product_types.get(code="dac_cable")
        product.save(update_fields=["product_type", "updated_at"])

        self.assertFalse(field_is_applicable(product, "dimensions_mm"))

    def test_reconcile_uses_published_management_type_for_competitor(self):
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=self.category,
            model="XS505M",
        )
        management = SpecDefinition.objects.get(code="management_type")
        ProductSpec.objects.create(
            product=product,
            definition=management,
            value_text="Unmanaged",
        )

        call_command("reconcile_spec_applicability", verbosity=0)

        product.refresh_from_db()
        self.assertEqual(product.product_type.code, "unmanaged_non_poe")

    def test_switch_consistency_audit_detects_and_clears_type_mismatch(self):
        netgear = Brand.objects.create(name="NETGEAR", slug="netgear")
        product = Product.objects.create(
            brand=netgear,
            category=self.category,
            model="XS505M",
        )
        management = SpecDefinition.objects.get(code="management_type")
        ProductSpec.objects.create(
            product=product,
            definition=management,
            value_text="Unmanaged",
        )

        with self.assertRaises(CommandError):
            call_command(
                "audit_switch_consistency",
                fail_on_issues=True,
                stdout=StringIO(),
            )

        call_command("reconcile_spec_applicability", verbosity=0)
        call_command(
            "audit_switch_consistency",
            fail_on_issues=True,
            stdout=StringIO(),
        )

    def test_reconcile_deletes_non_poe_poe_rows(self):
        product = self.make_product("TL-SG108-M2")
        definition = SpecDefinition.objects.get(code="poe_budget_w")
        ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_number=0,
        )

        call_command("reconcile_spec_applicability", verbosity=0)

        self.assertFalse(
            ProductSpec.objects.filter(
                product=product,
                definition__code="poe_budget_w",
            ).exists()
        )

    def test_reconcile_reclassifies_optical_accessory(self):
        accessory = Category.objects.get(slug="accessories")
        product = Product.objects.create(
            brand=self.brand,
            category=accessory,
            model="SFP10G-LR",
        )

        call_command("reconcile_spec_applicability", verbosity=0)

        product.refresh_from_db()
        self.assertEqual(product.product_type.code, "optical_module")

    def test_derives_switch_line_rate_and_optical_model_specs(self):
        switch = self.make_product("TL-SG108-M2")
        forwarding = SpecDefinition.objects.get(code="packet_forwarding_rate_mpps")
        ProductSpec.objects.create(
            product=switch,
            definition=forwarding,
            value_number=Decimal("7.440"),
        )
        accessory = Category.objects.get(slug="accessories")
        module = Product.objects.create(
            brand=self.brand,
            category=accessory,
            model="SM5110-LR",
        )
        call_command("reconcile_spec_applicability", verbosity=0)

        call_command("derive_product_specs", verbosity=0)

        capacity = ProductSpec.objects.get(
            product=switch,
            definition__code="switching_capacity_gbps",
        )
        self.assertEqual(float(capacity.value_number), 10)
        module_specs = {
            spec.definition.code: spec.display_value
            for spec in module.specs.select_related("definition")
        }
        self.assertEqual(module_specs["accessory_interface_type"], "SFP+")
        self.assertEqual(module_specs["accessory_fiber_mode"], "Single-mode")
        self.assertEqual(module_specs["accessory_max_distance_km"], "10 km")

    def test_derives_fast_ethernet_switch_with_letter_suffix(self):
        switch = self.make_product("TL-SF1016D")
        call_command("reconcile_spec_applicability", verbosity=0)

        call_command("derive_product_specs", verbosity=0)

        specs = {
            spec.definition.code: spec
            for spec in switch.specs.select_related("definition")
        }
        self.assertEqual(specs["ethernet_interfaces"].value_text, "16 x 10/100 Mbps Ethernet ports")
        self.assertEqual(float(specs["switching_capacity_gbps"].value_number), 3.2)
        self.assertEqual(float(specs["packet_forwarding_rate_mpps"].value_number), 2.381)
