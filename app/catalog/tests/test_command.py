from django.core.management import call_command
from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    ComparisonTemplate,
    ProductType,
    SpecDefinition,
    TemplateField,
)
from catalog.product_types import PRODUCT_TYPE_DEFINITIONS
from catalog.spec_templates import SPEC_DEFINITIONS, TEMPLATES


class InitializeCatalogCommandTests(TestCase):
    def test_command_is_idempotent_and_creates_required_data(self):
        call_command("initialize_catalog", verbosity=0)
        call_command("initialize_catalog", verbosity=0)

        self.assertEqual(Brand.objects.count(), 4)
        self.assertTrue(Brand.objects.get(name="TP-Link").is_own_brand)
        self.assertTrue(Brand.objects.filter(name="Ruijie").exists())
        self.assertTrue(Brand.objects.filter(name="Reyee").exists())
        self.assertEqual(Category.objects.count(), 9)
        self.assertEqual(
            Category.objects.get(name="Access Point").parent.name,
            "Wireless",
        )
        self.assertEqual(SpecDefinition.objects.count(), len(SPEC_DEFINITIONS))
        self.assertEqual(
            ProductType.objects.count(),
            sum(len(items) for items in PRODUCT_TYPE_DEFINITIONS.values()),
        )
        self.assertTrue(SpecDefinition.objects.get(code="supported_bands").is_core)
        self.assertEqual(
            Category.objects.get(name="Managed Switch").parent.name,
            "Switching",
        )
        self.assertEqual(
            Category.objects.get(name="Unmanaged / Easy Smart Switch").parent.name,
            "Switching",
        )
        self.assertEqual(
            ComparisonTemplate.objects.filter(active=True).count(),
            len(TEMPLATES),
        )
        self.assertTrue(
            TemplateField.objects.filter(
                template__category__slug="managed-switches",
                spec_definition__code="poe_budget_w",
            ).exists()
        )
        self.assertTrue(
            TemplateField.objects.filter(
                template__category__slug="gateway",
                spec_definition__code="vpn_throughput_mbps",
            ).exists()
        )
        self.assertFalse(
            TemplateField.objects.filter(
                template__category__slug="gateway",
                spec_definition__code="rate_5g_mbps",
            ).exists()
        )
        self.assertTrue(
            ComparisonTemplate.objects.filter(
                category__slug="accessories",
                form_factor="optical_module",
                active=True,
            ).exists()
        )
