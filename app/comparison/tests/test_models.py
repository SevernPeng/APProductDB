from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from catalog.models import Brand, Category, Product
from comparison.models import BenchmarkCase, ProductMatch


class ProductMatchTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.own_brand = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.competitor_brand = Brand.objects.create(
            name="Ubiquiti", slug="ubiquiti"
        )
        self.our_product = Product.objects.create(
            brand=self.own_brand,
            category=self.category,
            model="EAP772",
            ap_type=Product.APType.CEILING,
        )
        self.competitor = Product.objects.create(
            brand=self.competitor_brand,
            category=self.category,
            model="U7-Pro",
            ap_type=Product.APType.CEILING,
        )

    def test_match_can_be_created(self):
        match = ProductMatch.objects.create(
            our_product=self.our_product,
            competitor_product=self.competitor,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
        )
        self.assertEqual(match.region, "US")

    def test_self_match_is_rejected_by_model(self):
        with self.assertRaises(ValidationError):
            ProductMatch.objects.create(
                our_product=self.our_product,
                competitor_product=self.our_product,
                match_type=ProductMatch.MatchType.DIRECT,
            )

    def test_non_own_product_cannot_be_our_product(self):
        with self.assertRaises(ValidationError):
            ProductMatch.objects.create(
                our_product=self.competitor,
                competitor_product=self.our_product,
                match_type=ProductMatch.MatchType.DIRECT,
            )

    def test_database_constraint_prevents_self_match(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ProductMatch.objects.bulk_create(
                [
                    ProductMatch(
                        our_product=self.our_product,
                        competitor_product=self.our_product,
                        match_type=ProductMatch.MatchType.DIRECT,
                    )
                ]
            )

    def test_case_requires_matching_anchor_and_region(self):
        case = BenchmarkCase.objects.create(
            anchor_product=self.our_product,
            name="EAP772 direct competitors",
            region="US",
        )
        with self.assertRaises(ValidationError):
            ProductMatch.objects.create(
                benchmark_case=case,
                our_product=self.our_product,
                competitor_product=self.competitor,
                region="EU",
                match_type=ProductMatch.MatchType.DIRECT,
            )
