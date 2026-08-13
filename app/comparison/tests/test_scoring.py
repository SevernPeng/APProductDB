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
from comparison.scoring import calculate_benchmark_index


class BenchmarkIndexTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Routers", slug="routers")
        own_brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        competitor_brand = Brand.objects.create(name="Other", slug="other")
        self.ours = Product.objects.create(brand=own_brand, category=category, model="OURS")
        self.competitor = Product.objects.create(
            brand=competitor_brand, category=category, model="THEIRS"
        )
        template = ComparisonTemplate.objects.create(category=category, name="Router")
        self.speed = SpecDefinition.objects.create(
            code="speed", display_name="Speed", group="Performance",
            data_type=SpecDefinition.DataType.INTEGER,
        )
        self.feature = SpecDefinition.objects.create(
            code="feature", display_name="Feature", group="Features",
            data_type=SpecDefinition.DataType.BOOLEAN,
        )
        TemplateField.objects.create(
            template=template, spec_definition=self.speed,
            priority=TemplateField.Priority.P0, display_order=1,
        )
        TemplateField.objects.create(
            template=template, spec_definition=self.feature,
            priority=TemplateField.Priority.P1, display_order=2,
        )

    def add_spec(self, product, definition, *, number=None, boolean=None):
        return ProductSpec.objects.create(
            product=product, definition=definition,
            value_number=number, value_boolean=boolean,
        )

    def test_index_weights_core_numeric_closeness_and_boolean_equality(self):
        self.add_spec(self.ours, self.speed, number=Decimal("1000"))
        self.add_spec(self.competitor, self.speed, number=Decimal("800"))
        self.add_spec(self.ours, self.feature, boolean=True)
        self.add_spec(self.competitor, self.feature, boolean=True)

        self.assertEqual(calculate_benchmark_index(self.ours, self.competitor), 88)

    def test_manual_score_is_fallback_when_no_specs_are_comparable(self):
        self.assertEqual(
            calculate_benchmark_index(self.ours, self.competitor, manual_score=73),
            73,
        )
