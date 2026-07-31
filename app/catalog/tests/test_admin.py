from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition


class CatalogAdminTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="catalog-admin",
            email="admin@example.com",
            password="admin-test-password",
        )
        self.client.force_login(self.admin)
        self.brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.definition = SpecDefinition.objects.create(
            code="supported_bands",
            display_name="Supported Wireless Bands",
            group="Wireless",
            data_type=SpecDefinition.DataType.TEXT,
        )

    def test_catalog_admin_changelists_are_available(self):
        for url_name in (
            "admin:catalog_brand_changelist",
            "admin:catalog_category_changelist",
            "admin:catalog_producttype_changelist",
            "admin:catalog_product_changelist",
            "admin:catalog_specdefinition_changelist",
            "admin:catalog_productspec_changelist",
        ):
            with self.subTest(url_name=url_name):
                self.assertEqual(self.client.get(reverse(url_name)).status_code, 200)

    def test_admin_can_create_product_and_tracks_actor(self):
        response = self.client.post(
            reverse("admin:catalog_product_add"),
            {
                "brand": self.brand.pk,
                "category": self.category.pk,
                "model": "EAP772",
                "region": "US",
                "hardware_version": "V2.20",
                "ap_type": Product.APType.CEILING,
                "wifi_standard": "Wi-Fi 7",
                "lifecycle_status": Product.LifecycleStatus.ACTIVE,
                "is_published": "on",
                "specs-TOTAL_FORMS": "1",
                "specs-INITIAL_FORMS": "0",
                "specs-MIN_NUM_FORMS": "0",
                "specs-MAX_NUM_FORMS": "1000",
                "specs-0-definition": self.definition.pk,
                "specs-0-value_status": ProductSpec.ValueStatus.PUBLISHED,
                "specs-0-value_text": "2.4 / 5 / 6 GHz",
                "specs-0-value_number": "",
                "specs-0-raw_value": "2.4 / 5 / 6 GHz",
                "specs-0-source_url": "https://example.com/eap772",
                "specs-0-verified_date": "2026-07-18",
                "_save": "Save",
            },
        )
        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(model="EAP772")
        self.assertEqual(product.created_by, self.admin)
        self.assertEqual(product.updated_by, self.admin)
        self.assertEqual(ProductSpec.objects.get(product=product).updated_by, self.admin)
