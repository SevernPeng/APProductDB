from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from catalog.models import (
    Brand,
    Category,
    ComparisonTemplate,
    DatasheetIngestion,
    Product,
    ProductSpec,
    SpecDefinition,
    TemplateField,
)
from comparison.models import ProductMatch


class HomeTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer", password="a-strong-test-password"
        )
        self.user.groups.add(Group.objects.get_or_create(name="Viewer")[0])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("home")}')

    def test_authenticated_user_can_open_home(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "网络产品竞品数据库")
        self.assertContains(response, reverse("product-list"))
        self.assertContains(response, 'name="q"')
        self.assertNotContains(response, "全站待审核")

    def test_superuser_sees_sitewide_pending_review_metric(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "全站待审核")

    def test_home_counts_published_own_and_competitor_products(self):
        category = Category.objects.create(name="Access Point", slug="access-point")
        own_brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        competitor_brand = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        Product.objects.create(
            brand=own_brand,
            category=category,
            model="EAP772",
            ap_type=Product.APType.CEILING,
        )
        Product.objects.create(
            brand=competitor_brand,
            category=category,
            model="U7-Pro",
            ap_type=Product.APType.CEILING,
        )
        Product.objects.create(
            brand=competitor_brand,
            category=category,
            model="Hidden-U7",
            ap_type=Product.APType.CEILING,
            is_published=False,
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))

        self.assertEqual(response.context["product_count"], 2)
        self.assertEqual(response.context["own_brand_count"], 1)
        self.assertEqual(response.context["competitor_count"], 1)
        self.assertEqual(list(response.context["recent_products"])[0].model, "U7-Pro")

    def test_home_global_search_has_no_category_filter(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))

        self.assertContains(response, 'name="q"')
        self.assertNotContains(response, 'name="category"')


class ProductListTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="product-viewer")
        self.user.groups.add(Group.objects.get_or_create(name="Viewer")[0])
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.tp_link = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.ubiquiti = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.bands_definition = SpecDefinition.objects.create(
            code="supported_bands",
            display_name="Supported Wireless Bands",
            group="Wireless",
            data_type=SpecDefinition.DataType.TEXT,
        )
        self.streams_definition = SpecDefinition.objects.create(
            code="total_spatial_streams",
            display_name="Total Spatial Streams",
            group="Wireless",
            data_type=SpecDefinition.DataType.INTEGER,
        )
        self.ethernet_definition = SpecDefinition.objects.create(
            code="ethernet_interfaces",
            display_name="Ethernet Interfaces",
            group="Interfaces",
            data_type=SpecDefinition.DataType.TEXT,
        )

    def make_product(
        self,
        model,
        brand=None,
        ap_type=Product.APType.CEILING,
        bands="2.4 / 5 / 6 GHz",
        streams=6,
        ethernet="1× 2.5 GbE RJ45",
        published=True,
    ):
        product = Product.objects.create(
            brand=brand or self.tp_link,
            category=self.category,
            model=model,
            ap_type=ap_type,
            is_published=published,
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.bands_definition,
            value_text=bands,
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.streams_definition,
            value_number=streams,
        )
        ProductSpec.objects.create(
            product=product,
            definition=self.ethernet_definition,
            value_text=ethernet,
        )
        return product

    def get_products(self, params=None):
        self.client.force_login(self.user)
        response = self.client.get(reverse("product-list"), params or {})
        self.assertEqual(response.status_code, 200)
        return response, list(response.context["page_obj"].object_list)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("product-list"))
        self.assertRedirects(
            response,
            f'{reverse("login")}?next={reverse("product-list")}',
        )

    def test_model_search_is_the_only_query_control(self):
        self.make_product("EAP772")
        response, _ = self.get_products()

        self.assertContains(response, 'name="q"')
        self.assertContains(response, '<button class="btn btn-primary w-100" type="submit">搜索</button>', html=True)
        for obsolete_name in ("category", "brand", "ap_type", "bands", "streams", "lan_rate"):
            self.assertNotContains(response, f'name="{obsolete_name}"')

    def test_model_search_ignores_case_spaces_and_hyphens(self):
        expected = self.make_product("EAP772-Outdoor")
        self.make_product("U7-Pro", brand=self.ubiquiti)

        _, products = self.get_products({"q": "eap 772 outdoor"})

        self.assertEqual(products, [expected])

    def test_legacy_filter_parameters_do_not_filter_products(self):
        first = self.make_product("EAP725-Outdoor", ap_type=Product.APType.OUTDOOR)
        second = self.make_product("EAP787", bands="2.4 / 5 / 6 GHz", streams=8)

        _, products = self.get_products(
            {
                "brand": "missing",
                "category": "managed-switches",
                "ap_type": Product.APType.WALL_PLATE,
                "bands": "dual",
                "streams": "999",
                "lan_rate": "10",
            }
        )

        self.assertEqual(products, [first, second])

    def test_unpublished_products_are_not_listed(self):
        visible = self.make_product("VISIBLE")
        self.make_product("HIDDEN", published=False)
        response, products = self.get_products()
        self.assertEqual(products, [visible])
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_product_list_paginates_at_twenty_five(self):
        for number in range(26):
            self.make_product(f"MODEL-{number:02d}")
        response, products = self.get_products()
        self.assertEqual(len(products), 25)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        second_response, second_products = self.get_products({"page": "2"})
        self.assertEqual(len(second_products), 1)
        self.assertEqual(second_response.context["page_obj"].number, 2)

    def test_product_list_searches_across_categories_and_displays_product_type(self):
        managed = Category.objects.create(name="Managed Switch", slug="managed-switches")
        capacity = SpecDefinition.objects.create(
            code="switching_capacity_gbps",
            display_name="Switching Capacity",
            group="Performance",
            data_type=SpecDefinition.DataType.DECIMAL,
            unit="Gbps",
        )
        poe_budget = SpecDefinition.objects.create(
            code="poe_budget_w",
            display_name="Total PoE Budget",
            group="PoE",
            data_type=SpecDefinition.DataType.DECIMAL,
            unit="W",
        )
        switch = Product.objects.create(
            brand=self.tp_link,
            category=managed,
            model="SG3428XMP",
        )
        ProductSpec.objects.create(
            product=switch,
            definition=self.ethernet_definition,
            value_text="24× Gigabit RJ45 + 4× 10G SFP+",
        )
        ProductSpec.objects.create(product=switch, definition=capacity, value_number=128)
        ProductSpec.objects.create(product=switch, definition=poe_budget, value_number=384)

        response, products = self.get_products({"q": "SG3428XMP"})

        self.assertEqual(products, [switch])
        self.assertContains(response, "Managed Switch")
        self.assertContains(response, "产品类型")
        self.assertNotContains(response, "Switching Capacity")
        self.assertNotContains(response, "Total PoE Budget")
        self.assertNotContains(response, '<th>AP Type</th>', html=False)


class ProductDetailAndPermissionTests(TestCase):
    def setUp(self):
        viewer_group = Group.objects.get_or_create(name="Viewer")[0]
        contributor_group = Group.objects.get_or_create(name="Contributor")[0]
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(username="detail-viewer")
        self.viewer.groups.add(viewer_group)
        self.contributor = user_model.objects.create_user(username="detail-contributor")
        self.contributor.groups.add(contributor_group)
        self.no_role_user = user_model.objects.create_user(username="no-role")
        self.superuser = user_model.objects.create_superuser(username="detail-admin")
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.tp_link = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.ubiquiti = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.definitions = {}
        definition_data = (
            ("supported_bands", "Supported Wireless Bands", "Wireless", "text", ""),
            ("mimo_6g", "6 GHz MIMO", "Wireless", "text", ""),
            ("rate_2g_mbps", "2.4 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("rate_5g_mbps", "5 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("rate_6g_mbps", "6 GHz Max Rate", "Performance", "integer", "Mbps"),
            ("max_channel_width_mhz", "Max Channel Width", "Wireless", "integer", "MHz"),
            ("ethernet_interfaces", "Ethernet Interfaces", "Interfaces", "text", ""),
        )
        for order, (code, name, group, data_type, unit) in enumerate(
            definition_data, start=1
        ):
            self.definitions[code] = SpecDefinition.objects.create(
                code=code,
                display_name=name,
                group=group,
                data_type=data_type,
                unit=unit,
                is_core=True,
                display_order=order,
            )
        self.product = Product.objects.create(
            brand=self.tp_link,
            category=self.category,
            model="EAP-ZERO",
            region="US",
            hardware_version="V1",
            ap_type=Product.APType.CEILING,
            official_url="https://example.com/eap-zero",
        )
        ProductSpec.objects.create(
            product=self.product,
            definition=self.definitions["supported_bands"],
            value_text="2.4 / 5 GHz",
            verified_date=date(2026, 7, 18),
        )
        ProductSpec.objects.create(
            product=self.product,
            definition=self.definitions["rate_2g_mbps"],
            value_number=Decimal("0"),
            verified_date=date(2026, 7, 18),
        )
        ProductSpec.objects.create(
            product=self.product,
            definition=self.definitions["rate_5g_mbps"],
            value_number=Decimal("4324"),
            verified_date=date(2026, 7, 18),
        )

    def detail_url(self, product=None):
        return reverse("product-detail", args=((product or self.product).pk,))

    def test_anonymous_user_is_redirected_and_unassigned_user_gets_403(self):
        response = self.client.get(self.detail_url())
        self.assertRedirects(response, f'{reverse("login")}?next={self.detail_url()}')
        self.client.force_login(self.no_role_user)
        self.assertEqual(self.client.get(self.detail_url()).status_code, 403)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("home")).status_code, 403)

    def test_viewer_contributor_and_superuser_can_view_published_product(self):
        for user in (self.viewer, self.contributor, self.superuser):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.detail_url()).status_code, 200)

    def test_detail_distinguishes_zero_and_missing_states_and_calculates_rate(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        self.assertContains(response, "0 Mbps")
        self.assertContains(response, "Not Applicable")
        self.assertContains(response, "Not Published")
        self.assertContains(response, "Unknown")
        self.assertContains(response, "4324 Mbps")

    def test_detail_displays_field_source_and_verification_date(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        self.assertContains(response, "https://example.com/eap-zero")
        self.assertContains(response, "2026-07-18")
        self.assertContains(response, "系统计算（各频段最大速率之和）")

    def test_detail_separates_p0_p1_and_collapsible_p2_fields(self):
        template = ComparisonTemplate.objects.create(
            category=self.category,
            form_factor=Product.APType.CEILING,
            name="Ceiling AP",
        )
        priorities = (
            ("supported_bands", TemplateField.Priority.P0),
            ("ethernet_interfaces", TemplateField.Priority.P1),
            ("max_channel_width_mhz", TemplateField.Priority.P2),
        )
        for order, (code, priority) in enumerate(priorities, start=1):
            TemplateField.objects.create(
                template=template,
                spec_definition=self.definitions[code],
                priority=priority,
                display_group=f"Group {priority.upper()}",
                display_order=order * 10,
            )

        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())

        self.assertContains(response, "P0 · 核心对标规格")
        self.assertContains(response, "P1 · 重要规格")
        self.assertContains(response, "更多规格（P2）")
        self.assertContains(response, "Group P1")
        self.assertEqual(len(response.context["p0_spec_rows"]), 1)
        self.assertEqual(len(response.context["p1_spec_rows"]), 1)
        self.assertEqual(len(response.context["p2_spec_rows"]), 1)

    def test_detail_displays_current_match_in_both_directions(self):
        competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-TEST",
            ap_type=Product.APType.CEILING,
        )
        hidden_competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-HIDDEN",
            ap_type=Product.APType.CEILING,
            is_published=False,
        )
        ProductMatch.objects.create(
            our_product=self.product,
            competitor_product=competitor,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
        )
        ProductMatch.objects.create(
            our_product=self.product,
            competitor_product=hidden_competitor,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
        )
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        self.assertContains(response, "Ubiquiti U7-TEST")
        self.assertNotContains(response, "U7-HIDDEN")
        self.assertContains(self.client.get(self.detail_url(competitor)), "TP-Link EAP-ZERO")

    def test_unpublished_product_is_not_exposed_and_query_routes_are_read_only(self):
        hidden = Product.objects.create(
            brand=self.tp_link,
            category=self.category,
            model="HIDDEN-DETAIL",
            ap_type=Product.APType.CEILING,
            is_published=False,
        )
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(self.detail_url(hidden)).status_code, 404)
        self.assertEqual(self.client.post(self.detail_url()).status_code, 405)
        self.assertEqual(self.client.post(reverse("product-list")).status_code, 405)

    def test_detail_uses_datasheet_button_instead_of_embedded_forms(self):
        self.client.force_login(self.contributor)
        response = self.client.get(self.detail_url())

        self.assertContains(response, "Datasheet 识别")
        self.assertContains(
            response,
            reverse("product-datasheet", args=(self.product.pk,)),
        )
        self.assertNotContains(response, 'type="file"')
        self.assertNotContains(response, "最近识别记录")

    def test_datasheet_page_offers_pdf_and_url_inputs(self):
        self.client.force_login(self.contributor)
        response = self.client.get(
            reverse("product-datasheet", args=(self.product.pk,))
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "上传 Datasheet PDF")
        self.assertContains(response, "添加 Datasheet URL")
        self.assertContains(response, 'type="file"')
        self.assertContains(response, 'name="datasheet_url"')

    @patch("core.views.schedule_datasheet_ingestion")
    def test_datasheet_url_is_queued_without_saving_before_validation(
        self, schedule_ingestion
    ):
        self.client.force_login(self.contributor)
        submitted_url = "https://example.com/eap-zero-datasheet.pdf"

        response = self.client.post(
            reverse("product-datasheet-url", args=(self.product.pk,)),
            {"datasheet_url": submitted_url},
        )

        self.assertRedirects(
            response,
            reverse("product-datasheet", args=(self.product.pk,)),
        )
        self.product.refresh_from_db()
        self.assertEqual(self.product.datasheet_url, "")
        ingestion = DatasheetIngestion.objects.get()
        self.assertEqual(ingestion.source_url, submitted_url)
        schedule_ingestion.assert_called_once_with(ingestion.pk)

    @patch("core.views.schedule_datasheet_ingestion")
    def test_submitted_datasheet_url_stays_pending(self, schedule_ingestion):
        self.client.force_login(self.contributor)

        self.client.post(
            reverse("product-datasheet-url", args=(self.product.pk,)),
            {"datasheet_url": "https://example.com/wrong-model.pdf"},
        )

        self.product.refresh_from_db()
        self.assertEqual(self.product.datasheet_url, "")
        self.assertEqual(
            DatasheetIngestion.objects.get().status,
            DatasheetIngestion.Status.PENDING,
        )

    def test_invalid_datasheet_url_returns_form_error(self):
        self.client.force_login(self.contributor)
        response = self.client.post(
            reverse("product-datasheet-url", args=(self.product.pk,)),
            {"datasheet_url": "not-a-url"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "输入一个有效的 URL", status_code=400)
        self.assertFalse(DatasheetIngestion.objects.exists())


class HealthTests(TestCase):
    def test_health_reports_database_ok(self):
        response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ok", "database": "ok"})

    def test_health_does_not_disclose_internal_error_details(self):
        with patch.object(connection, "cursor", side_effect=RuntimeError("secret path")):
            response = self.client.get(reverse("health"))
        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "error", "database": "error"})
        self.assertNotIn(b"secret path", response.content)
