from decimal import Decimal

from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    ComparisonTemplate,
    Product,
    ProductSpec,
    SpecDefinition,
    TemplateField,
)
from comparison.services import build_comparison_rows


class AdaptiveManagedSwitchComparisonTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            name="Managed Switch", slug="managed-switches"
        )
        self.brand = Brand.objects.create(name="TP-Link", slug="tp-link")
        self.template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor="",
            name="Managed General",
        )
        definitions = (
            ("ethernet_interfaces", "Ethernet Interfaces", "Interfaces", "text"),
            ("packet_buffer_mb", "Packet Buffer", "Capacity", "decimal"),
            ("poe_configuration", "PoE Configuration", "PoE", "text"),
            ("poe_standard", "Supported PoE Standards", "PoE", "text"),
            ("poe_ports", "PoE-Capable Ports", "PoE", "integer"),
            ("poe_budget_w", "Total PoE Budget", "PoE", "decimal"),
            ("max_poe_per_port_w", "Maximum PoE per Port", "PoE", "decimal"),
        )
        self.definitions = {}
        for order, (code, name, group, data_type) in enumerate(definitions, start=1):
            definition = SpecDefinition.objects.create(
                code=code,
                display_name=name,
                group=group,
                data_type=data_type,
                category=self.category,
                display_order=order,
            )
            self.definitions[code] = definition
            TemplateField.objects.create(
                template=self.template,
                spec_definition=definition,
                priority=TemplateField.Priority.P0,
                display_group=group,
                display_order=order,
            )

    def product(self, model):
        product = Product.objects.create(
            brand=self.brand,
            category=self.category,
            model=model,
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.definitions["ethernet_interfaces"],
            value_text="24× GE + 4× 10G SFP+",
            source_note="Imported from Omada managed Switch comparison.",
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.definitions["packet_buffer_mb"],
            value_number=Decimal("4"),
            source_note="Imported from Omada managed Switch comparison.",
        )
        return product

    def test_non_poe_comparison_hides_entire_poe_group_and_unknown_rows(self):
        first = self.product("SG3428X")
        second = self.product("SG3452X")

        rows = build_comparison_rows([first, second])

        self.assertFalse({row["code"] for row in rows} & {
            "poe_configuration",
            "poe_standard",
            "poe_ports",
            "poe_budget_w",
            "max_poe_per_port_w",
        })
        self.assertTrue(rows)
        self.assertFalse(
            any(
                value["display"] == "Unknown"
                for row in rows
                for value in row["values"]
            )
        )

    def test_mixed_comparison_marks_non_poe_product_not_applicable(self):
        poe_switch = self.product("SG3428XMP")
        non_poe_switch = self.product("SG3428X")
        ProductSpec.objects.create(
            product=poe_switch,
            definition=self.definitions["poe_budget_w"],
            value_number=Decimal("384"),
            unit="W",
            source_note="Imported from Omada managed Switch comparison.",
        )

        rows = build_comparison_rows([poe_switch, non_poe_switch])
        poe_budget = next(row for row in rows if row["code"] == "poe_budget_w")

        self.assertEqual(poe_budget["values"][0]["display"], "384 W")
        self.assertEqual(poe_budget["values"][1]["display"], "Not Applicable")
