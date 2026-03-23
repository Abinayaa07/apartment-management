from django.test import TestCase
from django.test import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
import shutil
import tempfile

from .models import FamilyMember, User


TEMP_MEDIA_ROOT = tempfile.mkdtemp()


class DashboardViewTests(TestCase):
    def test_resident_dashboard_renders(self):
        user = User.objects.create_user(
            username="resident1",
            password="testpass123",
            role="resident",
            phone="1111111111",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/resident_dashboard.html")

    def test_security_dashboard_renders(self):
        user = User.objects.create_user(
            username="security1",
            password="testpass123",
            role="security",
            phone="2222222222",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/security_dashboard.html")

    def test_staff_dashboard_renders(self):
        user = User.objects.create_user(
            username="staff1",
            password="testpass123",
            role="staff",
            phone="3333333333",
            is_approved=True,
        )

        self.client.force_login(user)
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/staff_dashboard.html")


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class RegistrationDocumentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_resident_registration_requires_documents(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "resident_docs",
                "email": "resident@example.com",
                "phone": "9999999999",
                "flat_number": "A-101",
                "role": "resident",
                "password1": "testpass123!",
                "password2": "testpass123!",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Residents must upload an ID proof.")
        self.assertContains(response, "Residents must upload an address proof.")

    def test_resident_registration_with_documents_succeeds(self):
        id_proof = SimpleUploadedFile("id.txt", b"id proof", content_type="text/plain")
        address_proof = SimpleUploadedFile("address.txt", b"address proof", content_type="text/plain")

        response = self.client.post(
            reverse("register"),
            {
                "username": "resident_ok",
                "email": "residentok@example.com",
                "phone": "8888888888",
                "flat_number": "A-102",
                "role": "resident",
                "password1": "testpass123!",
                "password2": "testpass123!",
                "id_proof": id_proof,
                "address_proof": address_proof,
            },
        )

        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="resident_ok")
        self.assertFalse(user.is_approved)
        self.assertTrue(bool(user.id_proof))
        self.assertTrue(bool(user.address_proof))


class DashboardApprovalTests(TestCase):
    def test_admin_can_approve_resident_from_dashboard(self):
        admin_user = User.objects.create_user(
            username="admin1",
            password="testpass123",
            role="admin",
            phone="7777777777",
            is_approved=True,
        )
        resident = User.objects.create_user(
            username="resident_pending",
            password="testpass123",
            role="resident",
            phone="6666666666",
            is_approved=False,
        )

        self.client.force_login(admin_user)
        response = self.client.post(reverse("approve_resident", args=[resident.id]))

        self.assertRedirects(response, reverse("dashboard"))
        resident.refresh_from_db()
        self.assertTrue(resident.is_approved)

    def test_non_admin_cannot_approve_resident_from_dashboard(self):
        staff_user = User.objects.create_user(
            username="staff2",
            password="testpass123",
            role="staff",
            phone="5555555555",
            is_approved=True,
        )
        resident = User.objects.create_user(
            username="resident_waiting",
            password="testpass123",
            role="resident",
            phone="4444444444",
            is_approved=False,
        )

        self.client.force_login(staff_user)
        response = self.client.post(reverse("approve_resident", args=[resident.id]))

        self.assertRedirects(response, reverse("dashboard"))
        resident.refresh_from_db()
        self.assertFalse(resident.is_approved)


class FamilyDetailsTests(TestCase):
    def test_resident_can_add_own_family_member(self):
        resident = User.objects.create_user(
            username="resident_family",
            password="testpass123",
            role="resident",
            phone="1212121212",
            flat_number="A-101",
            is_approved=True,
        )

        self.client.force_login(resident)
        response = self.client.post(
            reverse("my_family_details"),
            {
                "member_name": "Ravi Kumar",
                "gender": "male",
                "relationship": "Brother",
                "date_of_birth": "2000-05-10",
            },
        )

        self.assertRedirects(response, reverse("my_family_details"))
        self.assertEqual(resident.family_members.count(), 1)

    def test_staff_can_view_family_records(self):
        staff_user = User.objects.create_user(
            username="staff_family",
            password="testpass123",
            role="staff",
            phone="3434343434",
            is_approved=True,
        )
        resident = User.objects.create_user(
            username="resident_family_view",
            password="testpass123",
            role="resident",
            phone="5656565656",
            flat_number="B-202",
            is_approved=True,
        )
        FamilyMember.objects.create(
            resident=resident,
            member_name="Anita",
            gender="female",
            relationship="Mother",
            date_of_birth="1982-04-08",
        )

        self.client.force_login(staff_user)
        response = self.client.get(reverse("manage_family_details"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "B-202")
        self.assertContains(response, "Anita")
