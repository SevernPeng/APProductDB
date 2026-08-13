from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditLog
from catalog.models import Brand, Category, Product
from changes.models import ChangeRequest
from imports.models import ImportJob


class AuthenticationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="viewer", password="a-strong-test-password"
        )

    def test_login_page_has_registration_link(self):
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign In")
        self.assertContains(response, "Register")

    def test_successful_login_redirects_to_home(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "a-strong-test-password"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_logout_requires_post_and_redirects_to_login(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))


class GroupInitializationTests(TestCase):
    def test_legacy_permission_groups_are_removed(self):
        from django.contrib.auth.models import Group

        self.assertFalse(Group.objects.filter(name__in=("Viewer", "Contributor")).exists())


class AccountSystemTests(TestCase):
    def test_root_account_is_seeded_with_expected_role_and_password(self):
        root = get_user_model().objects.get(username="root")
        self.assertTrue(root.is_superuser)
        self.assertTrue(root.check_password("Nqt1_Ulk0"))
        self.assertEqual(root.account_profile.role, "root")

    def test_registration_requires_company_email_and_rejects_duplicates(self):
        url = reverse("accounts:register")
        response = self.client.post(
            url,
            {"email": "person@example.com", "password1": "Good-Test-Pass-928!", "password2": "Good-Test-Pass-928!"},
        )
        self.assertContains(response, "Only @tp-link.com company email addresses are supported")
        response = self.client.post(
            url,
            {"email": "Person@TP-LINK.COM", "password1": "Good-Test-Pass-928!", "password2": "Good-Test-Pass-928!"},
        )
        self.assertRedirects(response, reverse("home"))
        user = get_user_model().objects.get(username="person@tp-link.com")
        self.assertEqual(user.account_profile.role, "user")
        self.client.logout()
        response = self.client.post(
            url,
            {"email": "PERSON@tp-link.com", "password1": "Another-Test-Pass-837!", "password2": "Another-Test-Pass-837!"},
        )
        self.assertContains(response, "This email is already registered")
        self.assertEqual(get_user_model().objects.filter(email__iexact="person@tp-link.com").count(), 1)

    def test_company_email_login_is_case_insensitive(self):
        user = get_user_model().objects.create_user(
            username="person@tp-link.com", email="person@tp-link.com", password="Good-Test-Pass-928!"
        )
        response = self.client.post(
            reverse("login"),
            {"username": "PERSON@TP-LINK.COM", "password": "Good-Test-Pass-928!"},
        )
        self.assertRedirects(response, reverse("home"))

    def test_all_non_root_accounts_are_users_and_only_root_can_list_them(self):
        user = get_user_model().objects.create_user(
            username="member@tp-link.com", email="member@tp-link.com"
        )
        profile = user.account_profile
        self.assertEqual(profile.role, "user")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 403)
        root = get_user_model().objects.get(username="root")
        self.client.force_login(root)
        response = self.client.get(reverse("accounts:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "member@tp-link.com")
        self.assertNotContains(response, "Admin")
        self.assertContains(response, reverse("accounts:delete", args=[profile.pk]))

    def test_root_can_delete_user_and_preserve_business_history(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="delete-me@tp-link.com",
            email="delete-me@tp-link.com",
        )
        category = Category.objects.create(name="Access Point", slug="access-point")
        brand = Brand.objects.create(name="TP-Link", slug="tp-link", is_own_brand=True)
        product = Product.objects.create(brand=brand, category=category, model="EAP-delete")
        change = ChangeRequest.objects.create(
            request_type=ChangeRequest.RequestType.PRODUCT,
            target_product=product,
            field_name="notes",
            old_value={"value": "old"},
            proposed_value={"value": "new"},
            reason="Historical change",
            submitted_by=user,
        )
        job = ImportJob.objects.create(
            uploaded_file="imports/source/history.xlsx",
            uploaded_by=user,
        )
        root = user_model.objects.get(username="root")
        self.client.force_login(root)

        response = self.client.post(
            reverse("accounts:delete", args=[user.account_profile.pk]),
            REMOTE_ADDR="127.0.0.1",
        )

        self.assertRedirects(response, reverse("accounts:list"))
        self.assertFalse(user_model.objects.filter(pk=user.pk).exists())
        change.refresh_from_db()
        job.refresh_from_db()
        self.assertIsNone(change.submitted_by)
        self.assertIsNone(job.uploaded_by)
        audit = AuditLog.objects.get(action="account.deleted", object_id=str(user.pk))
        self.assertEqual(audit.actor, root)
        self.assertEqual(audit.before_data["username"], "delete-me@tp-link.com")
        self.assertEqual(audit.ip_address, "127.0.0.1")

    def test_root_account_cannot_be_deleted(self):
        root = get_user_model().objects.get(username="root")
        self.client.force_login(root)
        response = self.client.post(
            reverse("accounts:delete", args=[root.account_profile.pk]),
            follow=True,
        )
        self.assertContains(response, "The root account cannot be deleted")
        self.assertTrue(get_user_model().objects.filter(pk=root.pk).exists())
        self.assertFalse(AuditLog.objects.filter(action="account.deleted").exists())

    def test_user_cannot_delete_accounts_and_delete_requires_post(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(username="member@tp-link.com")
        target = user_model.objects.create_user(username="target@tp-link.com")
        url = reverse("accounts:delete", args=[target.account_profile.pk])
        self.client.force_login(user)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(user_model.objects.filter(pk=target.pk).exists())
        root = user_model.objects.get(username="root")
        self.client.force_login(root)
        self.assertEqual(self.client.get(url).status_code, 405)
