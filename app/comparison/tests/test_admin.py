from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Brand, Category, Product
from comparison.models import ProductMatch


class ProductMatchAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="match-admin",
            email="admin@example.com",
            password="admin-test-password",
        )
        self.client.force_login(self.admin)
        category = Category.objects.create(name="Access Point", slug="access-point")
        own_brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        competitor_brand = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.our_product = Product.objects.create(
            brand=own_brand,
            category=category,
            model="EAP772",
            ap_type=Product.APType.CEILING,
        )
        self.competitor = Product.objects.create(
            brand=competitor_brand,
            category=category,
            model="U7-Pro",
            ap_type=Product.APType.CEILING,
        )

    def test_admin_can_create_match_and_tracks_actor(self):
        response = self.client.post(
            reverse("admin:comparison_productmatch_add"),
            {
                "our_product": self.our_product.pk,
                "competitor_product": self.competitor.pk,
                "match_type": ProductMatch.MatchType.DIRECT,
                "match_level": ProductMatch.MatchLevel.CORE,
                "status": ProductMatch.Status.CONFIRMED,
                "region": "US",
                "match_score": "",
                "rank": "0",
                "reason": "Comparable deployment role",
                "advantages": "",
                "disadvantages": "",
                "source_url": "",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        match = ProductMatch.objects.get()
        self.assertEqual(match.created_by, self.admin)
        self.assertEqual(match.updated_by, self.admin)
