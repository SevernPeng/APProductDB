from datetime import date
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from openpyxl import load_workbook

from catalog.models import (
    Brand,
    Category,
    ComparisonTemplate,
    Product,
    ProductSpec,
    SpecDefinition,
    TemplateField,
)
from comparison.models import ProductMatch


class ComparisonViewTests(TestCase):
    def setUp(self):
        viewer_group = Group.objects.get_or_create(name="Viewer")[0]
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(username="comparison-viewer")
        self.viewer.groups.add(viewer_group)
        self.no_role_user = user_model.objects.create_user(username="comparison-no-role")
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.tp_link = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.ubiquiti = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.ruijie = Brand.objects.create(name="Ruijie", slug="ruijie")
        self.definitions = {}
        definitions = (
            ("supported_bands", "Supported Wireless Bands", "Wireless", "text", ""),
            ("rate_2g_mbps", "2.4 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("rate_5g_mbps", "5 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("rate_6g_mbps", "6 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("max_channel_width_mhz", "Max Channel Width", "Wireless", "integer", "MHz"),
            ("poe_output", "PoE Output", "Power", "text", ""),
        )
        for order, (code, name, group, data_type, unit) in enumerate(definitions, 1):
            self.definitions[code] = SpecDefinition.objects.create(
                code=code,
                display_name=name,
                group=group,
                data_type=data_type,
                unit=unit,
                is_core=True,
                display_order=order,
            )

        self.eap772 = self.create_product(
            self.tp_link, "EAP772", "https://example.com/eap772"
        )
        self.u7_pro = self.create_product(
            self.ubiquiti, "U7-Pro", "https://example.com/u7-pro"
        )
        self.rg_ap = self.create_product(
            self.ruijie, "RG-AP7136-R", "https://example.com/rg-ap7136-r"
        )
        self.add_text_spec(self.eap772, "supported_bands", "2.4 / 5 / 6 GHz")
        self.add_text_spec(self.u7_pro, "supported_bands", "2.4 / 5 / 6 GHz")
        self.add_text_spec(self.rg_ap, "supported_bands", "2.4 / 5 GHz")
        self.add_number_spec(self.eap772, "rate_2g_mbps", "574")
        self.add_number_spec(self.eap772, "rate_5g_mbps", "2882")
        self.add_number_spec(self.eap772, "rate_6g_mbps", "5764")
        self.add_number_spec(self.eap772, "max_channel_width_mhz", "320")
        self.add_number_spec(self.u7_pro, "rate_2g_mbps", "688")
        self.add_number_spec(self.u7_pro, "rate_5g_mbps", "2882")
        self.add_number_spec(self.u7_pro, "rate_6g_mbps", "5764")
        self.add_number_spec(self.rg_ap, "rate_2g_mbps", "0")
        self.add_number_spec(self.rg_ap, "rate_5g_mbps", "2882")
        self.add_text_spec(self.eap772, "poe_output", '=HYPERLINK("unsafe")')

        self.u7_match = ProductMatch.objects.create(
            our_product=self.eap772,
            competitor_product=self.u7_pro,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
            match_score=95,
            reason="同级三频吸顶 AP",
            advantages="更高聚合速率",
            disadvantages="功耗依赖部署条件",
        )
        self.rg_match = ProductMatch.objects.create(
            our_product=self.eap772,
            competitor_product=self.rg_ap,
            match_type=ProductMatch.MatchType.PERFORMANCE,
            status=ProductMatch.Status.CONFIRMED,
        )

    def create_product(self, brand, model, official_url, **kwargs):
        return Product.objects.create(
            brand=brand,
            category=self.category,
            model=model,
            ap_type=Product.APType.CEILING,
            official_url=official_url,
            **kwargs,
        )

    def add_text_spec(self, product, code, value):
        return ProductSpec.objects.create(
            product=product,
            definition=self.definitions[code],
            value_text=value,
            source_url=product.official_url,
            verified_date=date(2026, 7, 18),
        )

    def add_number_spec(self, product, code, value):
        return ProductSpec.objects.create(
            product=product,
            definition=self.definitions[code],
            value_number=Decimal(value),
            source_url=product.official_url,
            verified_date=date(2026, 7, 18),
        )

    def comparison_url(self, *products, **options):
        query = "&".join(f"products={product.pk}" for product in products)
        for name, value in options.items():
            query += f"&{name}={value}"
        return reverse("comparison:compare") + "?" + query

    def test_pages_require_login_and_catalog_role(self):
        urls = (
            reverse("comparison:benchmark"),
            reverse("comparison:compare"),
            self.comparison_url(self.eap772, self.u7_pro),
        )
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.no_role_user)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.viewer)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_benchmark_defaults_to_eap772_and_links_three_product_comparison(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("comparison:benchmark"))
        self.assertContains(response, "EAP772")
        self.assertContains(response, "U7-Pro")
        self.assertContains(response, "RG-AP7136-R")
        self.assertContains(response, "同级三频吸顶 AP")
        self.assertContains(response, "比较当前全部产品")
        self.assertContains(response, f"products={self.eap772.pk}")
        self.assertContains(response, f"products={self.u7_pro.pk}")
        self.assertContains(response, f"products={self.rg_ap.pk}")

    def test_benchmark_uses_normalized_fuzzy_search_instead_of_full_dropdown(self):
        outdoor = self.create_product(
            self.tp_link,
            "EAP772-Outdoor",
            "https://example.com/eap772-outdoor",
        )
        self.client.force_login(self.viewer)
        response = self.client.get(
            reverse("comparison:benchmark"), {"q": "eap 772-out"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, outdoor.model)
        self.assertContains(response, "找到 1 个型号")
        self.assertNotContains(response, '<select class="form-select"')
        self.assertNotContains(response, "U7-Pro")

    def test_compare_displays_two_to_four_products_and_missing_states(self):
        self.client.force_login(self.viewer)
        response = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro, self.rg_ap)
        )
        self.assertContains(response, "TP-Link")
        self.assertContains(response, "U7-Pro")
        self.assertContains(response, "RG-AP7136-R")
        self.assertContains(response, "0 Mbps")
        self.assertContains(response, "Not Applicable")
        self.assertContains(response, "Not Published")
        self.assertContains(response, "Unknown")
        self.assertContains(response, "9220 Mbps")

    def test_compare_product_selectors_are_searchable_autocomplete_fields(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.comparison_url(self.eap772, self.u7_pro))
        self.assertContains(response, 'data-product-autocomplete')
        self.assertContains(response, 'type="search"')
        self.assertContains(response, 'name="products"')
        self.assertContains(response, f'data-value="{self.eap772.pk}"')
        self.assertNotContains(response, '<select class="form-select" id="compare-product-')

    def test_compare_rejects_invalid_counts_and_unpublished_product(self):
        hidden = self.create_product(
            self.ubiquiti,
            "U7-HIDDEN",
            "https://example.com/hidden",
            is_published=False,
        )
        extra_one = self.create_product(self.ubiquiti, "U7-ONE", "")
        extra_two = self.create_product(self.ubiquiti, "U7-TWO", "")
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.comparison_url(self.eap772)).status_code, 400)
        self.assertEqual(
            self.client.get(
                self.comparison_url(
                    self.eap772,
                    self.u7_pro,
                    self.rg_ap,
                    extra_one,
                    extra_two,
                )
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(self.comparison_url(self.eap772, hidden)).status_code,
            400,
        )

    def test_compare_rejects_products_from_different_categories(self):
        switch_category = Category.objects.create(
            name="Managed",
            slug="managed-switches",
        )
        switch = Product.objects.create(
            brand=self.tp_link,
            category=switch_category,
            model="SG3428X",
        )
        self.client.force_login(self.viewer)

        response = self.client.get(self.comparison_url(self.eap772, switch))

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "只能比较同一产品类型", status_code=400)

    def test_only_differences_hides_equal_rows_and_sources_are_optional(self):
        self.client.force_login(self.viewer)
        difference_response = self.client.get(
            self.comparison_url(
                self.eap772, self.u7_pro, self.rg_ap, differences="1"
            )
        )
        self.assertNotContains(difference_response, "Wi-Fi Standard")
        self.assertContains(difference_response, "Supported Wireless Bands")
        without_sources = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro)
        )
        self.assertNotContains(without_sources, ">官方来源</a>", html=False)
        with_sources = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro, sources="1")
        )
        self.assertContains(with_sources, ">官方来源</a>", html=False)

    def test_compare_extended_toggle_controls_p2_rows(self):
        template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor=Product.APType.CEILING,
            name="Comparison priorities",
        )
        TemplateField.objects.create(
            template=template,
            spec_definition=self.definitions["supported_bands"],
            priority=TemplateField.Priority.P0,
            display_group="Wireless",
            display_order=10,
        )
        TemplateField.objects.create(
            template=template,
            spec_definition=self.definitions["poe_output"],
            priority=TemplateField.Priority.P2,
            display_group="Power",
            display_order=20,
        )
        self.client.force_login(self.viewer)

        default_response = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro)
        )
        extended_response = self.client.get(
            self.comparison_url(self.eap772, self.u7_pro, extended="1")
        )

        self.assertNotContains(default_response, "PoE Output")
        self.assertContains(extended_response, "PoE Output")
        self.assertContains(extended_response, "P2 · Power")
        self.assertContains(extended_response, 'id="include-extended"')

    def test_export_contains_current_products_rows_and_sources(self):
        self.client.force_login(self.viewer)
        url = reverse("comparison:export") + "?" + "&".join(
            (
                f"products={self.eap772.pk}",
                f"products={self.u7_pro.pk}",
                "sources=1",
            )
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        workbook = load_workbook(BytesIO(response.content), read_only=True)
        worksheet = workbook["Comparison"]
        values = list(worksheet.values)
        self.assertEqual(values[0][0], "Specification")
        self.assertIn("TP-Link EAP772", values[0])
        self.assertIn("Ubiquiti U7-Pro Source", values[0])
        self.assertIn("Aggregate Rate", [row[0] for row in values])
        poe_row = next(row for row in values if row[0] == "PoE Output")
        self.assertEqual(poe_row[1], '\'=HYPERLINK("unsafe")')

    def test_product_detail_has_one_click_three_product_comparison(self):
        self.client.force_login(self.viewer)
        response = self.client.get(reverse("product-detail", args=[self.eap772.pk]))
        self.assertContains(response, "比较当前全部产品")
        self.assertContains(response, f"products={self.eap772.pk}")
        self.assertContains(response, f"products={self.u7_pro.pk}")
        self.assertContains(response, f"products={self.rg_ap.pk}")
