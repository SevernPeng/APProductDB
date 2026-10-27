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
    PriceSource,
    Product,
    ProductPriceSnapshot,
    ProductType,
    ProductSpec,
    SpecDefinition,
    TemplateField,
)
from comparison.models import ProductMatch


class RootRouteTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer", password="a-strong-test-password"
        )
        self.user.groups.add(Group.objects.get_or_create(name="Viewer")[0])

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("home"))
        self.assertRedirects(response, f'{reverse("login")}?next={reverse("home")}')

    def test_authenticated_user_sees_product_catalog_at_root(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/product_list.html")
        self.assertContains(response, "Products")
        self.assertContains(response, reverse("product-list"))
        self.assertContains(response, 'name="q"')

    def test_non_root_cannot_become_superuser(self):
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_staff)
        self.assertFalse(self.user.is_superuser)
        self.assertEqual(self.user.account_profile.role, "user")

    def test_root_uses_product_catalog_visibility_rules(self):
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

        self.assertEqual(response.context["tp_link_count"], 1)
        self.assertEqual([product.model for product in response.context["page_obj"]], ["EAP772"])

    def test_root_global_search_has_no_category_filter(self):
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
        wifi_standard="",
        published=True,
    ):
        product = Product.objects.create(
            brand=brand or self.tp_link,
            category=self.category,
            model=model,
            ap_type=ap_type,
            wifi_standard=wifi_standard,
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

    def test_product_portfolio_has_search_family_and_category_navigation(self):
        self.make_product("EAP772")
        response, _ = self.get_products()

        self.assertContains(response, 'name="q"')
        self.assertContains(response, "Search products")
        self.assertContains(response, "TP-Link product database")
        self.assertContains(response, "Explore the portfolio")
        self.assertContains(response, reverse("product-family", args=["wireless"]))
        wireless_response = self.client.get(
            reverse("product-family", args=["wireless"])
        )
        self.assertEqual(wireless_response.status_code, 200)
        self.assertContains(wireless_response, "Browse by product type")
        self.assertContains(
            wireless_response,
            reverse("product-subcategory", args=["wireless", "wifi-7"]),
        )
        self.assertContains(wireless_response, "Wireless Bridge")
        for obsolete_name in ("brand", "ap_type", "bands", "streams", "lan_rate"):
            self.assertNotContains(response, f'name="{obsolete_name}"')

    def test_official_style_subcategory_filters_the_selected_family(self):
        wifi_7 = self.make_product("EAP772", wifi_standard="Wi-Fi 7")
        self.make_product("EAP225", wifi_standard="Wi-Fi 5")

        self.client.force_login(self.user)
        response = self.client.get(
            reverse("product-subcategory", args=["wireless", "wifi-7"])
        )
        self.assertEqual(response.status_code, 200)
        products = list(response.context["page_obj"].object_list)

        self.assertEqual(products, [wifi_7])
        self.assertEqual(response.context["active_subcategory"]["title"], "WiFi 7")
        self.assertContains(response, "<h2>WiFi 7</h2>", html=True)

    def test_unknown_family_page_returns_not_found(self):
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("product-family", args=["not-a-family"])
        )
        self.assertEqual(response.status_code, 404)

    def test_switch_navigation_matches_omada_families(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("product-family", args=["switching"]))
        self.assertEqual([card["title"] for card in response.context["category_cards"]], [
            "Campus", "Aggregation", "Access Max", "Access Pro", "Access Plus",
            "Access", "Agile", "Unmanaged", "Industrial", "Easy Smart",
        ])

    def test_official_switch_models_override_old_technical_categories(self):
        category = Category.objects.create(name="Managed Switch", slug="managed-switches")
        l3 = ProductType.objects.create(category=category, code="l3_non_poe", name="L3")
        l2 = ProductType.objects.create(category=category, code="l2_non_poe", name="L2")
        cases = [
            ("SG5428XF", l3, "aggregation"), ("SX6632YF", l3, "aggregation"),
            ("SG5428X", l3, "access-plus"), ("SX3832", l2, "access-max"),
            ("SG3210X-M2", l2, "access-pro"), ("SG2008", l2, "access"),
        ]
        for model, product_type, _ in cases:
            Product.objects.create(brand=self.tp_link, category=category,
                                   model=model, product_type=product_type)
        Product.objects.create(brand=self.ubiquiti, category=category, model="SG2008")
        self.client.force_login(self.user)
        for key in {key for _, _, key in cases}:
            with self.subTest(key=key):
                response = self.client.get(reverse("product-subcategory", args=["switching", key]))
                actual = {p.model for p in response.context["page_obj"]}
                self.assertEqual(actual, {model for model, _, group in cases if group == key})
                card = next(c for c in response.context["category_cards"] if c["key"] == key)
                self.assertEqual(card["product_count"], len(actual))
        legacy = self.client.get(reverse("product-subcategory", args=["switching", "layer-3"]))
        self.assertEqual(legacy.status_code, 200)
        self.assertEqual(legacy.context["page_obj"].paginator.count, 3)

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

        self.assertEqual(products, [second, first])

    def test_unpublished_products_are_not_listed(self):
        visible = self.make_product("VISIBLE")
        self.make_product("HIDDEN", published=False)
        response, products = self.get_products()
        self.assertEqual(products, [visible])
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_product_list_paginates_at_twenty_four(self):
        for number in range(26):
            self.make_product(f"MODEL-{number:02d}")
        response, products = self.get_products()
        self.assertEqual(len(products), 24)
        self.assertEqual(response.context["page_obj"].paginator.num_pages, 2)
        second_response, second_products = self.get_products({"page": "2"})
        self.assertEqual(len(second_products), 2)
        self.assertEqual(second_response.context["page_obj"].number, 2)
        self.assertContains(response, 'aria-disabled="true">First</span>')
        self.assertContains(response, 'aria-label="Last page" href="?page=2#catalog"')
        self.assertContains(second_response, 'aria-label="First page" href="?page=1#catalog"')
        self.assertContains(second_response, 'aria-disabled="true">Last</span>')
        filtered_response, _ = self.get_products({"q": "MODEL", "page": "2"})
        self.assertContains(filtered_response, 'aria-label="First page" href="?q=MODEL&amp;page=1#catalog"')

    def test_catalog_filters_match_official_wireless_dimensions(self):
        wifi7 = self.make_product(
            "EAP772", ap_type=Product.APType.CEILING,
            wifi_standard="Wi-Fi 7", ethernet="1× 10G RJ45",
        )
        self.make_product(
            "EAP650-Outdoor", ap_type=Product.APType.OUTDOOR,
            wifi_standard="Wi-Fi 6", ethernet="1× Gigabit RJ45",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("product-family", args=["wireless"]),
            {"wifi_standard": "wifi-7", "form_factor": "ceiling", "port_speed": "10g"},
        )

        self.assertEqual(list(response.context["page_obj"]), [wifi7])
        self.assertContains(response, "Wi-Fi Standard")
        self.assertContains(response, "Form Factor")
        self.assertContains(response, "Port Speed")
        self.assertContains(response, '<option value="wifi-7" selected>Wi-Fi 7</option>', html=True)

    def test_catalog_filters_submit_immediately_when_selection_changes(self):
        self.make_product("EAP772", wifi_standard="Wi-Fi 7")

        response, _ = self.get_products()

        self.assertContains(response, 'id="catalog-filters"')
        self.assertContains(response, 'select.addEventListener("change"')
        self.assertContains(response, "form.requestSubmit()")
        self.assertNotContains(response, "Apply filters")

    def test_nom_filter_distinguishes_current_certification(self):
        certified = self.make_product("EAP-CERTIFIED")
        certified.nom_records = [{
            "ready": True,
            "certificates": [{"number": "NOM-123", "permanent": True, "expires_on": None}],
        }]
        certified.save(update_fields=("nom_records",))
        uncertified = self.make_product("EAP-NO-NOM")

        with_nom_response, with_nom = self.get_products({"nom": "yes"})
        _, without_nom = self.get_products({"nom": "no"})

        self.assertEqual(with_nom, [certified])
        self.assertEqual(without_nom, [uncertified])
        self.assertContains(with_nom_response, "NOM Certification")
        self.assertContains(with_nom_response, '<option value="yes" selected>With NOM</option>', html=True)

    def test_poe_filter_does_not_treat_non_poe_type_as_poe(self):
        switch_category = Category.objects.create(name="Managed Switch", slug="managed-switches")
        poe_type = ProductType.objects.create(category=switch_category, code="l2_poe", name="Layer 2 PoE")
        non_poe_type = ProductType.objects.create(category=switch_category, code="l2_non_poe", name="Layer 2 Non-PoE")
        poe_switch = Product.objects.create(
            brand=self.tp_link, category=switch_category, product_type=poe_type, model="SG-POE",
        )
        non_poe_switch = Product.objects.create(
            brand=self.tp_link, category=switch_category, product_type=non_poe_type, model="SG-NON-POE",
        )
        self.client.force_login(self.user)

        poe_response = self.client.get(reverse("product-family", args=["switching"]), {"poe": "yes"})
        non_poe_response = self.client.get(reverse("product-family", args=["switching"]), {"poe": "no"})

        self.assertEqual(list(poe_response.context["page_obj"]), [poe_switch])
        self.assertEqual(list(non_poe_response.context["page_obj"]), [non_poe_switch])

    def test_filters_are_preserved_in_pagination_links(self):
        for number in range(25):
            product = self.make_product(f"NOM-{number:02d}")
            product.nom_records = [{
                "ready": True,
                "certificates": [{"number": str(number), "permanent": True, "expires_on": None}],
            }]
            product.save(update_fields=("nom_records",))

        response, _ = self.get_products({"nom": "yes"})

        self.assertContains(response, 'aria-label="Last page" href="?nom=yes&amp;page=2#catalog"')

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
        self.assertContains(response, "SG3428XMP")
        self.assertNotContains(response, "Switching Capacity")
        self.assertNotContains(response, "Total PoE Budget")
        self.assertNotContains(response, '<th>AP Type</th>', html=False)

    def test_default_portfolio_shows_tp_link_and_search_can_find_competitors(self):
        own = self.make_product("EAP772")
        competitor = self.make_product("U7-Pro", brand=self.ubiquiti)

        _, default_products = self.get_products()
        _, search_products = self.get_products({"q": "u7 pro"})

        self.assertEqual(default_products, [own])
        self.assertEqual(search_products, [competitor])


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

    def test_anonymous_user_is_redirected_and_any_account_gets_access(self):
        response = self.client.get(self.detail_url())
        self.assertRedirects(response, f'{reverse("login")}?next={self.detail_url()}')
        self.client.force_login(self.no_role_user)
        self.assertEqual(self.client.get(self.detail_url()).status_code, 200)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 200)
        self.assertEqual(self.client.get(reverse("home")).status_code, 200)

    def test_viewer_contributor_and_superuser_can_view_published_product(self):
        for user in (self.viewer, self.contributor, self.superuser):
            self.client.force_login(user)
            self.assertEqual(self.client.get(self.detail_url()).status_code, 200)

    def test_detail_distinguishes_zero_and_missing_states_and_calculates_rate(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        self.assertContains(response, "0 Mbps")
        self.assertNotContains(response, "6 GHz MIMO")
        self.assertContains(response, "Not Published")
        self.assertContains(response, "Unknown")
        self.assertContains(response, "4324 Mbps")

    def test_detail_does_not_display_per_field_source_metadata(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        self.assertNotContains(response, "Official source")
        self.assertNotContains(response, "Verified 2026-07-18")
        self.assertNotContains(response, "Calculated from maximum band rates")

    def test_detail_uses_two_columns_for_long_multiline_specifications(self):
        ProductSpec.objects.create(
            product=self.product,
            definition=self.definitions["ethernet_interfaces"],
            value_text="Port one\nPort two\nPort three\nPort four",
        )
        self.client.force_login(self.viewer)

        response = self.client.get(self.detail_url())

        self.assertContains(response, "spec-value-columns")
        self.assertContains(response, "<li>Port one</li>", html=True)
        self.assertContains(response, "<li>Port four</li>", html=True)

    def test_detail_groups_specifications_in_template_order(self):
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

        self.assertContains(response, "Specifications")
        self.assertContains(response, "Group P0")
        self.assertContains(response, "Group P1")
        self.assertContains(response, "Group P2")
        self.assertEqual(
            [group["name"] for group in response.context["spec_groups"]],
            ["WIRELESS FEATURES", "Group P0", "Group P1", "Group P2"],
        )
        self.assertEqual(len(response.context["p0_spec_rows"]), 1)
        self.assertEqual(len(response.context["p1_spec_rows"]), 1)
        self.assertEqual(len(response.context["p2_spec_rows"]), 1)

    def test_detail_displays_product_image_or_clear_placeholder(self):
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        self.assertContains(response, "Product image unavailable")

        self.product.image.name = "products/eap-zero.png"
        self.product.save(update_fields=("image", "updated_at"))
        response = self.client.get(self.detail_url())
        self.assertContains(response, 'class="product-image"')
        self.assertContains(response, reverse("product-image", args=(self.product.pk,)))
        self.assertNotContains(response, "Product image unavailable")

    def test_detail_places_latest_syscom_price_in_header_and_uses_chart_for_history(self):
        source = PriceSource.objects.create(
            code="syscom",
            name="SYSCOM México",
            base_url="https://www.syscom.mx",
        )
        for external_id, price in (("old", "130.00"), ("new", "120.00")):
            ProductPriceSnapshot.objects.create(
                source=source,
                product=self.product,
                external_id=external_id,
                external_model=self.product.model,
                product_url=f"https://www.syscom.mx/products/{external_id}",
                currency="USD",
                unit_price=Decimal(price),
            )

        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())

        self.assertEqual(response.context["current_price"].unit_price, Decimal("120.00"))
        self.assertEqual(
            [point["price"] for point in response.context["price_chart_points"]],
            [130.0, 120.0],
        )
        self.assertContains(response, 'class="syscom-price-summary"')
        self.assertContains(response, "USD")
        self.assertContains(response, "$120.00")
        self.assertContains(response, "data-price-history-open")
        self.assertContains(response, 'class="syscom-price-chart"')
        self.assertNotContains(response, "SYSCOM Price Trend")

    def test_product_image_endpoint_requires_access_and_streams_existing_file(self):
        from django.core.files.base import ContentFile
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as directory, self.settings(MEDIA_ROOT=directory):
            self.product.image.save(
                "eap-zero.png", ContentFile(b"test-image"), save=True
            )
            image_url = reverse("product-image", args=(self.product.pk,))
            anonymous_response = self.client.get(image_url)
            self.assertEqual(anonymous_response.status_code, 302)

            self.client.force_login(self.viewer)
            response = self.client.get(image_url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response["Content-Type"], "image/png")
            self.assertEqual(response["Cache-Control"], "private, max-age=86400")
            self.assertEqual(b"".join(response.streaming_content), b"test-image")

    def test_detail_hides_poe_fields_for_confirmed_non_poe_switch(self):
        switch_category = Category.objects.create(
            name="Unmanaged Switch", slug="unmanaged-easy-smart-switches"
        )
        unmanaged = ProductType.objects.create(
            category=switch_category, code="unmanaged", name="Unmanaged"
        )
        ethernet = self.definitions["ethernet_interfaces"]
        poe_budget = SpecDefinition.objects.create(
            code="poe_budget_w",
            display_name="Total PoE Budget",
            group="PoE",
            data_type=SpecDefinition.DataType.DECIMAL,
            unit="W",
            category=switch_category,
        )
        template = ComparisonTemplate.objects.create(
            category=switch_category,
            form_factor="unmanaged",
            name="Unmanaged Switch",
        )
        TemplateField.objects.create(
            template=template,
            spec_definition=ethernet,
            priority=TemplateField.Priority.P0,
            display_order=10,
        )
        TemplateField.objects.create(
            template=template,
            spec_definition=poe_budget,
            priority=TemplateField.Priority.P1,
            display_order=20,
        )
        switch = Product.objects.create(
            brand=self.tp_link,
            category=switch_category,
            product_type=unmanaged,
            model="TL-SX105",
            official_url="https://www.tp-link.com/en/home-networking/soho-switch/tl-sx105/",
        )
        ProductSpec.objects.create(
            product=switch,
            definition=ethernet,
            value_text="5 x 10G RJ45",
            value_status=ProductSpec.ValueStatus.PUBLISHED,
        )

        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url(switch))

        self.assertContains(response, "Ethernet Interfaces")
        self.assertContains(response, "Unmanaged")
        self.assertNotContains(response, "Unknown Management Type")
        self.assertNotContains(response, "Total PoE Budget")

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
        self.assertContains(response, "spec-card")
        self.assertContains(response, "benchmark-card")
        self.assertContains(self.client.get(self.detail_url(competitor)), "TP-Link EAP-ZERO")

    def test_detail_shows_top_three_benchmark_indexes_and_collapses_the_rest(self):
        competitors = []
        for index, score in enumerate((20, 90, 40, 80, 70), start=1):
            competitor = Product.objects.create(
                brand=self.ubiquiti,
                category=self.category,
                model=f"RANK-{index}",
                ap_type=Product.APType.CEILING,
            )
            ProductMatch.objects.create(
                our_product=self.product,
                competitor_product=competitor,
                match_type=ProductMatch.MatchType.DIRECT,
                status=ProductMatch.Status.CONFIRMED,
                match_score=score,
            )
            competitors.append(competitor)

        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())

        self.assertEqual(
            [item["benchmark_index"] for item in response.context["visible_matches"]],
            [90, 80, 70],
        )
        self.assertEqual(
            [item["benchmark_index"] for item in response.context["collapsed_matches"]],
            [40, 20],
        )
        self.assertContains(response, "Show 2 more benchmarks")
        self.assertContains(response, "Benchmark Index 90")

    def test_benchmark_card_deduplicates_legacy_and_case_matches_in_both_directions(self):
        from urllib.parse import parse_qs, urlparse
        from comparison.models import BenchmarkCase

        case = BenchmarkCase.objects.create(anchor_product=self.product, name="Imported benchmark", region="US")
        competitors = []
        for index in range(4):
            competitor = Product.objects.create(brand=self.ubiquiti, category=self.category,
                model=f"DEDUP-{index}", ap_type=Product.APType.CEILING)
            competitors.append(competitor)
            for benchmark_case in (None, case):
                ProductMatch.objects.create(our_product=self.product, competitor_product=competitor,
                    benchmark_case=benchmark_case, region="US", match_type="direct", status="confirmed", match_score=90-index)
        self.client.force_login(self.viewer)
        response = self.client.get(self.detail_url())
        items = response.context["visible_matches"] + response.context["collapsed_matches"]
        self.assertEqual(len(items), 4)
        self.assertEqual(len({item["product"].pk for item in items}), 4)
        self.assertTrue(all(item["match"].benchmark_case_id == case.pk for item in items))
        self.assertContains(response, "Show 1 more benchmarks")
        ids = parse_qs(urlparse(response.context["compare_matches_url"]).query)["products"]
        self.assertEqual(len(ids), 4)
        self.assertEqual(len(set(ids)), 4)
        reverse_response = self.client.get(self.detail_url(competitors[0]))
        self.assertEqual(len(reverse_response.context["visible_matches"]), 1)
        self.assertEqual(ProductMatch.objects.filter(our_product=self.product).count(), 8)

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

    def test_detail_has_no_datasheet_processing_controls(self):
        self.client.force_login(self.contributor)
        response = self.client.get(self.detail_url())

        self.assertNotContains(response, "Datasheet")
        self.assertContains(
            response,
            f'{self.detail_url()}?edit=1',
        )
        self.assertContains(response, ">Edit</a>", html=False)
        self.assertNotContains(response, "Suggest a Change")

    def test_detail_displays_active_lifecycle_badge_by_default(self):
        self.client.force_login(self.viewer)

        response = self.client.get(self.detail_url())

        self.assertContains(response, "lifecycle-active")
        self.assertContains(response, ">Active</span>", html=False)


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
