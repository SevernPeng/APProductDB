from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import AccountProfile
from audit.models import AuditLog
from catalog.models import Brand, Category, Product, ProductSpec, SpecDefinition
from changes.models import ChangeRequest
from changes.services import build_target_options, resolve_target
from changes.validators import MAX_ATTACHMENT_SIZE, validate_change_attachment
from comparison.models import ProductMatch


class ChangeWorkflowTests(TestCase):
    def setUp(self):
        self.media_directory = TemporaryDirectory()
        self.media_override = override_settings(MEDIA_ROOT=self.media_directory.name)
        self.media_override.enable()
        viewer_group = Group.objects.get_or_create(name="Viewer")[0]
        contributor_group = Group.objects.get_or_create(name="Contributor")[0]
        user_model = get_user_model()
        self.viewer = user_model.objects.create_user(username="change-viewer")
        self.viewer.groups.add(viewer_group)
        self.contributor = user_model.objects.create_user(username="change-contributor")
        self.contributor.groups.add(contributor_group)
        self.other_contributor = user_model.objects.create_user(username="change-other")
        self.other_contributor.groups.add(contributor_group)
        self.admin = user_model.objects.create_superuser(username="change-admin")
        self.category = Category.objects.create(name="Access Point", slug="access-point")
        self.tp_link = Brand.objects.create(
            name="TP-Link", slug="tp-link", is_own_brand=True
        )
        self.ubiquiti = Brand.objects.create(name="Ubiquiti", slug="ubiquiti")
        self.product = Product.objects.create(
            brand=self.tp_link,
            category=self.category,
            model="EAP772",
            ap_type=Product.APType.CEILING,
            notes="Original notes",
            official_url="https://example.com/eap772",
        )
        self.competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-Pro",
            ap_type=Product.APType.CEILING,
        )
        self.definition = SpecDefinition.objects.create(
            code="max_clients",
            display_name="Max Clients",
            group="Capacity",
            data_type=SpecDefinition.DataType.INTEGER,
            unit="",
            is_core=True,
        )
        self.spec = ProductSpec.objects.create(
            product=self.product,
            definition=self.definition,
            value_number=100,
            source_url="https://example.com/old",
        )
        self.match = ProductMatch.objects.create(
            our_product=self.product,
            competitor_product=self.competitor,
            match_type=ProductMatch.MatchType.DIRECT,
            status=ProductMatch.Status.CONFIRMED,
            reason="Original reason",
        )

    def tearDown(self):
        self.media_override.disable()
        self.media_directory.cleanup()

    def create_spec_change(self, **overrides):
        values = {
            "request_type": ChangeRequest.RequestType.SPEC,
            "target_product": self.product,
            "target_spec": self.spec,
            "field_name": self.definition.code,
            "old_value": {"value_text": "", "value_number": "100"},
            "proposed_value": {"value_text": "", "value_number": "200"},
            "reason": "Official specification correction",
            "source_url": "https://example.com/new",
            "submitted_by": self.contributor,
        }
        values.update(overrides)
        return ChangeRequest.objects.create(**values)

    def test_permissions_separate_viewer_contributor_owner_and_admin(self):
        suggest_url = reverse("changes:suggest", args=[self.product.pk])
        review_url = reverse("reviews:list")
        self.assertEqual(self.client.get(suggest_url).status_code, 302)
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.get(suggest_url).status_code, 403)
        self.client.force_login(self.contributor)
        self.assertEqual(self.client.get(suggest_url).status_code, 200)
        self.assertEqual(self.client.get(review_url).status_code, 403)
        change = self.create_spec_change()
        self.client.force_login(self.other_contributor)
        self.assertEqual(
            self.client.get(reverse("changes:detail", args=[change.pk])).status_code,
            403,
        )
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(review_url).status_code, 200)

    def test_editable_fields_follow_product_category_and_actual_specs(self):
        secondary_definition = SpecDefinition.objects.create(
            code="secondary_feature",
            display_name="Secondary Feature",
            group="Features",
            data_type=SpecDefinition.DataType.TEXT,
            is_core=False,
            display_order=50,
        )
        secondary_spec = ProductSpec.objects.create(
            product=self.product,
            definition=secondary_definition,
            value_text="Supported",
        )
        inactive_definition = SpecDefinition.objects.create(
            code="inactive_feature",
            display_name="Inactive Feature",
            group="Features",
            data_type=SpecDefinition.DataType.TEXT,
            is_core=False,
            active=False,
        )
        inactive_spec = ProductSpec.objects.create(
            product=self.product,
            definition=inactive_definition,
            value_text="Legacy",
        )

        option_keys = {
            option["key"] for option in build_target_options(self.product)
        }
        self.assertIn("product:sku", option_keys)
        self.assertIn("product:datasheet_url", option_keys)
        self.assertIn("product:launch_date", option_keys)
        self.assertIn("product:ap_type", option_keys)
        self.assertIn(f"spec:{secondary_spec.pk}", option_keys)
        self.assertNotIn(f"spec:{inactive_spec.pk}", option_keys)
        self.assertIn(f"match:{self.match.pk}:reason", option_keys)
        self.assertIn(f"match:{self.match.pk}:__delete__", option_keys)
        self.assertEqual(
            resolve_target(self.product, f"spec:{secondary_spec.pk}")["target"],
            secondary_spec,
        )
        self.assertEqual(
            resolve_target(
                self.product,
                f"match:{self.match.pk}:reason",
            )["target"],
            self.match,
        )

        switch_category = Category.objects.create(
            name="Managed Switch",
            slug="managed-switches",
        )
        switch = Product.objects.create(
            brand=self.tp_link,
            category=switch_category,
            model="SG2008",
        )
        switch_keys = {
            option["key"] for option in build_target_options(switch)
        }
        self.assertNotIn("product:ap_type", switch_keys)
        self.assertNotIn("product:wifi_standard", switch_keys)
        with self.assertRaises(ValidationError):
            resolve_target(switch, "product:ap_type")

        self.client.force_login(self.contributor)
        response = self.client.get(
            reverse("changes:suggest", args=[self.product.pk])
        )
        self.assertContains(response, "<optgroup", html=False)
        self.assertContains(response, "Secondary Feature")

    def test_non_core_boolean_spec_can_be_changed(self):
        definition = SpecDefinition.objects.create(
            code="mesh_support",
            display_name="Mesh Support",
            group="Features",
            data_type=SpecDefinition.DataType.BOOLEAN,
            is_core=False,
        )
        spec = ProductSpec.objects.create(
            product=self.product,
            definition=definition,
            value_boolean=False,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"spec:{spec.pk}",
                "proposed_value": "Yes",
                "reason": "Official correction",
                "source_url": "https://example.com/mesh",
            },
        )
        self.assertEqual(response.status_code, 302)
        spec.refresh_from_db()
        change = ChangeRequest.objects.get(target_spec=spec)
        self.assertTrue(spec.value_boolean)
        self.assertEqual(change.old_value, {"value_boolean": False})
        self.assertEqual(change.proposed_value, {"value_boolean": True})

    def test_missing_category_specs_are_created_as_editable_unknown_fields(self):
        category_definition = SpecDefinition.objects.create(
            code="poe_budget",
            display_name="PoE Budget",
            group="Power",
            category=self.category,
            data_type=SpecDefinition.DataType.INTEGER,
            unit="W",
            is_core=False,
        )
        other_category = Category.objects.create(
            name="Gateway",
            slug="gateway",
        )
        unrelated_definition = SpecDefinition.objects.create(
            code="wan_ports",
            display_name="WAN Ports",
            group="Interfaces",
            category=other_category,
            data_type=SpecDefinition.DataType.INTEGER,
        )
        self.assertFalse(self.competitor.specs.exists())

        self.client.force_login(self.contributor)
        response = self.client.get(
            reverse("changes:suggest", args=[self.competitor.pk])
        )
        self.assertEqual(response.status_code, 200)
        placeholder = ProductSpec.objects.get(
            product=self.competitor,
            definition=category_definition,
        )
        self.assertEqual(
            placeholder.value_status,
            ProductSpec.ValueStatus.UNKNOWN,
        )
        self.assertContains(response, f'value="spec:{placeholder.pk}"')
        self.assertFalse(
            ProductSpec.objects.filter(
                product=self.competitor,
                definition=unrelated_definition,
            ).exists()
        )

    def test_competitor_page_can_modify_and_delete_incoming_match(self):
        option_keys = {
            option["key"] for option in build_target_options(self.competitor)
        }
        self.assertIn(f"match:{self.match.pk}:reason", option_keys)
        self.assertIn(f"match:{self.match.pk}:__delete__", option_keys)
        self.assertEqual(
            resolve_target(
                self.competitor,
                f"match:{self.match.pk}:reason",
            )["target"],
            self.match,
        )

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.competitor.pk]),
            {
                "target": f"match:{self.match.pk}:__delete__",
                "reason": "Remove incorrect reverse association",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, ProductMatch.Status.REJECTED)

    def test_admin_can_add_and_delete_competitor_relationships(self):
        second_competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-Pro-XG",
            ap_type=Product.APType.CEILING,
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "action": "add_match",
                "competitor_product": second_competitor.pk,
                "match_type": ProductMatch.MatchType.PERFORMANCE,
                "match_level": ProductMatch.MatchLevel.SECONDARY,
                "rank": 3,
                "match_score": 88,
                "confidence": 90,
                "relation_reason": "Comparable Wi-Fi 7 model",
                "source_url": "https://example.com/comparison",
                "request_reason": "Add the missing competitor",
            },
        )
        self.assertEqual(response.status_code, 302)
        added = ProductMatch.objects.get(
            our_product=self.product,
            competitor_product=second_competitor,
        )
        self.assertEqual(added.match_type, ProductMatch.MatchType.PERFORMANCE)
        self.assertEqual(added.match_level, ProductMatch.MatchLevel.SECONDARY)
        self.assertEqual(added.match_score, 88)
        self.assertEqual(added.status, ProductMatch.Status.CONFIRMED)
        add_change = ChangeRequest.objects.get(field_name="__add__")
        self.assertEqual(add_change.status, ChangeRequest.Status.APPROVED)

        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"match:{added.pk}:__delete__",
                "reason": "This model is no longer a valid competitor",
            },
        )
        self.assertEqual(response.status_code, 302)
        added.refresh_from_db()
        self.assertEqual(added.status, ProductMatch.Status.REJECTED)
        delete_change = ChangeRequest.objects.get(
            target_match=added,
            field_name="__delete__",
        )
        self.assertEqual(delete_change.status, ChangeRequest.Status.APPROVED)

    def test_contributor_match_add_waits_for_review_and_can_be_approved(self):
        second_competitor = Product.objects.create(
            brand=self.ubiquiti,
            category=self.category,
            model="U7-Lite",
            ap_type=Product.APType.CEILING,
        )
        self.client.force_login(self.contributor)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "action": "add_match",
                "competitor_product": second_competitor.pk,
                "match_type": ProductMatch.MatchType.DIRECT,
                "match_level": ProductMatch.MatchLevel.CORE,
                "relation_reason": "Same market segment",
                "source_url": "https://example.com/u7-lite",
                "request_reason": "Missing competitor",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            ProductMatch.objects.filter(
                our_product=self.product,
                competitor_product=second_competitor,
            ).exists()
        )
        change = ChangeRequest.objects.get(field_name="__add__")
        self.assertEqual(change.status, ChangeRequest.Status.PENDING)

        self.client.force_login(self.admin)
        review_response = self.client.get(
            reverse("reviews:detail", args=[change.pk])
        )
        self.assertEqual(review_response.status_code, 200)
        self.client.post(reverse("reviews:approve", args=[change.pk]))
        self.assertTrue(
            ProductMatch.objects.filter(
                our_product=self.product,
                competitor_product=second_competitor,
                status=ProductMatch.Status.CONFIRMED,
            ).exists()
        )

    def test_spec_submission_requires_evidence_and_rejects_same_value(self):
        self.client.force_login(self.contributor)
        url = reverse("changes:suggest", args=[self.product.pk])
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
            },
        )
        self.assertContains(response, "规格修改必须提供官方来源 URL 或证据附件")
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "100",
                "reason": "Correction",
                "source_url": "https://example.com/source",
            },
        )
        self.assertContains(response, "建议值不能与当前值相同")
        self.assertFalse(ChangeRequest.objects.exists())

    def test_valid_submission_uses_server_side_actor_and_keeps_formal_value(self):
        self.client.force_login(self.contributor)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
                "source_url": "https://example.com/new",
                "submitted_by": self.admin.pk,
            },
        )
        self.assertEqual(response.status_code, 302)
        change = ChangeRequest.objects.get()
        self.assertEqual(change.submitted_by, self.contributor)
        self.assertEqual(change.old_value["value_number"], "100")
        self.spec.refresh_from_db()
        self.assertEqual(self.spec.value_number, 100)
        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.contributor, action="change_request.submitted"
            ).exists()
        )

    def test_admin_approval_updates_spec_and_creates_audit_log(self):
        change = self.create_spec_change()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("reviews:approve", args=[change.pk]),
            {"review_comment": "Verified"},
        )
        self.assertEqual(response.status_code, 302)
        change.refresh_from_db()
        self.spec.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)
        self.assertEqual(change.reviewed_by, self.admin)
        self.assertEqual(self.spec.value_number, 200)
        self.assertEqual(self.spec.source_url, "https://example.com/new")
        audit = AuditLog.objects.get(action="change_request.approved")
        self.assertEqual(audit.before_data["value_number"], "100")
        self.assertEqual(audit.after_data["value_number"], "200")

    def test_role_admin_submission_is_applied_without_review_queue(self):
        role_admin = get_user_model().objects.create_user(
            username="reviewer@tp-link.com", email="reviewer@tp-link.com", password="secret"
        )
        AccountProfile.objects.create(user=role_admin, email=role_admin.email, role="admin")
        self.client.force_login(role_admin)
        response = self.client.post(
            reverse("changes:suggest", args=[self.product.pk]),
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "250",
                "reason": "Admin correction",
                "source_url": "https://example.com/admin-source",
            },
        )
        self.assertEqual(response.status_code, 302)
        change = ChangeRequest.objects.get(submitted_by=role_admin)
        change.refresh_from_db()
        self.spec.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)
        self.assertEqual(change.reviewed_by, role_admin)
        self.assertEqual(self.spec.value_number, 250)
        self.assertEqual(self.client.get(reverse("reviews:list")).status_code, 200)

    def test_review_product_filter_is_a_searchable_autocomplete_field(self):
        self.create_spec_change()
        self.client.force_login(self.admin)
        response = self.client.get(reverse("reviews:list"), {"product": self.product.pk})
        self.assertContains(response, 'data-product-autocomplete')
        self.assertContains(response, 'type="search"')
        self.assertContains(response, 'name="product"')
        self.assertContains(response, f'value="{self.product.pk}" data-product-value')
        self.assertNotContains(response, 'id="review-product"')

    def test_conflict_prevents_silent_overwrite(self):
        change = self.create_spec_change()
        self.spec.value_number = 150
        self.spec.save()
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("reviews:approve", args=[change.pk]),
            follow=True,
        )
        self.assertContains(response, "当前正式值已在申请提交后发生变化")
        change.refresh_from_db()
        self.spec.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.PENDING)
        self.assertEqual(self.spec.value_number, 150)
        self.assertFalse(AuditLog.objects.filter(action="change_request.approved").exists())

    def test_rejection_requires_comment_and_does_not_update_formal_data(self):
        change = self.create_spec_change()
        self.client.force_login(self.admin)
        self.client.post(reverse("reviews:reject", args=[change.pk]), {})
        change.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.PENDING)
        self.client.post(
            reverse("reviews:reject", args=[change.pk]),
            {"review_comment": "Source is insufficient"},
        )
        change.refresh_from_db()
        self.spec.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.REJECTED)
        self.assertEqual(self.spec.value_number, 100)
        self.assertTrue(AuditLog.objects.filter(action="change_request.rejected").exists())

    def test_product_and_match_changes_use_same_approval_workflow(self):
        product_change = ChangeRequest.objects.create(
            request_type=ChangeRequest.RequestType.PRODUCT,
            target_product=self.product,
            field_name="notes",
            old_value={"value": "Original notes"},
            proposed_value={"value": "Corrected notes"},
            reason="Update notes",
            submitted_by=self.contributor,
        )
        match_change = ChangeRequest.objects.create(
            request_type=ChangeRequest.RequestType.MATCH,
            target_product=self.product,
            target_match=self.match,
            field_name="reason",
            old_value={"value": "Original reason"},
            proposed_value={"value": "Corrected reason"},
            reason="Update match reasoning",
            submitted_by=self.contributor,
        )
        self.client.force_login(self.admin)
        self.client.post(reverse("reviews:approve", args=[product_change.pk]))
        self.client.post(reverse("reviews:approve", args=[match_change.pk]))
        self.product.refresh_from_db()
        self.match.refresh_from_db()
        self.assertEqual(self.product.notes, "Corrected notes")
        self.assertEqual(self.match.reason, "Corrected reason")

    def test_attachment_type_content_size_and_object_access_are_protected(self):
        self.client.force_login(self.contributor)
        url = reverse("changes:suggest", args=[self.product.pk])
        invalid = SimpleUploadedFile("proof.pdf", b"not a pdf")
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
                "attachment": invalid,
            },
        )
        self.assertContains(response, "附件内容与文件扩展名不匹配")

        valid_content = b"%PDF-1.7\nproof"
        valid = SimpleUploadedFile("proof.pdf", valid_content)
        response = self.client.post(
            url,
            {
                "target": f"spec:{self.spec.pk}",
                "proposed_value": "200",
                "reason": "Correction",
                "attachment": valid,
            },
        )
        self.assertEqual(response.status_code, 302)
        change = ChangeRequest.objects.get()
        self.assertNotIn("proof.pdf", change.attachment.name)
        download_url = reverse("changes:attachment", args=[change.pk])
        response = self.client.get(download_url)
        self.assertEqual(b"".join(response.streaming_content), valid_content)
        response.close()
        self.client.force_login(self.other_contributor)
        self.assertEqual(self.client.get(download_url).status_code, 403)
        self.client.force_login(self.admin)
        self.client.post(reverse("reviews:approve", args=[change.pk]))
        change.refresh_from_db()
        self.assertEqual(change.status, ChangeRequest.Status.APPROVED)

        oversized = BytesIO(b"%PDF-1.7")
        oversized.name = "large.pdf"
        oversized.size = MAX_ATTACHMENT_SIZE + 1
        with self.assertRaises(ValidationError):
            validate_change_attachment(oversized)

    def test_review_actions_are_post_only_and_completed_request_cannot_repeat(self):
        change = self.create_spec_change()
        self.client.force_login(self.admin)
        approve_url = reverse("reviews:approve", args=[change.pk])
        self.assertEqual(self.client.get(approve_url).status_code, 405)
        self.client.post(approve_url)
        self.client.post(approve_url)
        self.assertEqual(
            AuditLog.objects.filter(action="change_request.approved").count(), 1
        )
