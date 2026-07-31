from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from catalog.models import (
    Brand,
    Category,
    Product,
    ProductModel,
    ProductSpec,
    ProductType,
    SpecDefinition,
)


class CatalogModelTests(TestCase):
    def setUp(self):
        self.brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.user = get_user_model().objects.create_user(username="admin-test")

    def make_product(self, **overrides):
        values = {
            "brand": self.brand,
            "category": self.category,
            "model": "U7-Pro-Outdoor",
            "region": "US",
            "hardware_version": "V1",
            "ap_type": Product.APType.OUTDOOR,
            "created_by": self.user,
            "updated_by": self.user,
        }
        values.update(overrides)
        return Product.objects.create(**values)

    def test_product_normalizes_model_key(self):
        product = self.make_product()
        self.assertEqual(product.model_key, "U7PROOUTDOOR")

    def test_product_automatically_creates_canonical_model(self):
        product = self.make_product()
        self.assertIsNotNone(product.product_model_id)
        self.assertEqual(ProductModel.objects.count(), 1)
        self.assertEqual(product.product_model.model_key, product.model_key)

    def test_product_type_must_belong_to_product_category(self):
        other_category = Category.objects.create(name="Accessories", slug="accessories")
        wrong_type = ProductType.objects.create(
            category=other_category,
            code="poe_injector",
            name="PoE Injector",
        )
        with self.assertRaises(ValidationError):
            self.make_product(product_type=wrong_type)

    def test_product_version_is_unique_by_normalized_model(self):
        self.make_product()
        with self.assertRaises(ValidationError):
            self.make_product(model="U7 Pro Outdoor")

    def test_database_unique_constraint_is_present(self):
        product = self.make_product()
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.bulk_create(
                [
                    Product(
                        brand=product.brand,
                        category=product.category,
                        model="duplicate",
                        model_key=product.model_key,
                        region=product.region,
                        hardware_version=product.hardware_version,
                        ap_type=Product.APType.OUTDOOR,
                    )
                ]
            )

    def test_product_spec_rejects_text_and_number_together(self):
        product = self.make_product()
        definition = SpecDefinition.objects.create(
            code="rate_5g_mbps",
            display_name="5 GHz Max Rate",
            group="Performance",
            data_type=SpecDefinition.DataType.INTEGER,
            unit="Mbps",
        )
        with self.assertRaises(ValidationError):
            ProductSpec.objects.create(
                product=product,
                definition=definition,
                value_text="4324",
                value_number=Decimal("4324"),
            )

    def test_product_spec_uses_product_source_as_fallback(self):
        product = self.make_product(official_url="https://example.com/product")
        definition = SpecDefinition.objects.create(
            code="supported_bands",
            display_name="Supported Wireless Bands",
            group="Wireless",
            data_type=SpecDefinition.DataType.TEXT,
        )
        spec = ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_text="2.4 / 5 / 6 GHz",
        )
        self.assertEqual(spec.effective_source_url, product.official_url)

    def test_numeric_zero_is_not_displayed_as_missing(self):
        product = self.make_product()
        definition = SpecDefinition.objects.create(
            code="rate_6g_mbps",
            display_name="6 GHz Max Rate",
            group="Performance",
            data_type=SpecDefinition.DataType.INTEGER,
            unit="Mbps",
        )
        spec = ProductSpec.objects.create(
            product=product,
            definition=definition,
            value_number=Decimal("0.000"),
        )
        self.assertEqual(spec.display_value, "0 Mbps")

    def test_non_published_status_rejects_typed_value(self):
        product = self.make_product()
        definition = SpecDefinition.objects.create(
            code="ip_rating",
            display_name="IP Rating",
            group="Physical",
            data_type=SpecDefinition.DataType.TEXT,
        )
        with self.assertRaises(ValidationError):
            ProductSpec.objects.create(
                product=product,
                definition=definition,
                value_status=ProductSpec.ValueStatus.NOT_PUBLISHED,
                value_text="Not Published",
            )
