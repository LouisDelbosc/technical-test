from django.test import TestCase
from django.utils import timezone
import datetime
from ..models import User, Device, Session


class CreateSessionViewTestCase(TestCase):
    def setUp(self):
        # Set up a test user and device if necessary
        self.user = User.objects.create(email="test@example.com")
        self.device = Device.objects.create(user=self.user, type="othr")

    def test_post_session(self):
        data = {"user": {"email": self.user.email}, "device": {"type": "othr"}}
        response = self.client.post("/session/", data, content_type="application/json")

        session = Session.objects.filter(user=self.user, device=self.device).first()
        self.assertEqual(response.status_code, 201)
        self.assertDictEqual(
            response.json(),
            {
                "uuid": f"ses-{session.uuid}",
                "token": session.token,
                "status": "pending",
                "is_new_user": False,
                "is_new_device": False,
                "user": {
                    "uuid": f"usr-{self.user.uuid}",
                    "email": "test@example.com",
                },
                "device": {
                    "uuid": f"dev-{self.device.uuid}",
                    "type": "othr",
                },
            },
        )

    def test_post_session__consecutive(self):
        data = {
            "user": {"email": self.user.email},
            "device": {
                "type": "mobi",
                "vendor_uuid": "20354d7a-e4fe-47af-8ff6-187bca92f3f9",
            },
        }

        response = self.client.post("/session/", data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        response = self.client.post("/session/", data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        session = Session.objects.filter(
            user__email="test@example.com", device__type="mobi"
        ).first()
        self.assertDictEqual(
            response.json(),
            {
                "uuid": f"ses-{session.uuid}",
                "token": session.token,
                "status": "pending",
                "is_new_user": False,
                "is_new_device": True,
                "user": {
                    "uuid": f"usr-{session.user.uuid}",
                    "email": "test@example.com",
                },
                "device": {
                    "uuid": f"dev-{session.device.uuid}",
                    "vendor_uuid": "20354d7a-e4fe-47af-8ff6-187bca92f3f9",
                    "type": "mobi",
                },
            },
        )

    def test_post_session__expired(self):
        data = {"user": {"email": self.user.email}, "device": {"type": "othr"}}
        expired_date = timezone.make_aware(datetime.datetime(2023, 12, 19))
        expired_session = Session.objects.create(user=self.user, device=self.device)
        expired_session.created_at = expired_date
        expired_session.save()

        response = self.client.post("/session/", data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        expired_session.refresh_from_db()
        self.assertEqual(expired_session.status, "expired")
        self.assertTrue(response.json()["uuid"] != str(expired_session))
        self.assertEqual(response.json()["status"], "pending")

    def test_post_session__mobi_no_vendor(self):
        data = {
            "user": {"email": self.user.email},
            "device": {
                "type": "mobi",
            },
        }

        response = self.client.post("/session/", data, content_type="application/json")
        self.assertEqual(response.status_code, 400)


class UpdateSessionViewTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(email="test@example.com")
        self.device = Device.objects.create(user=self.user, type="othr")
        self.session = Session.objects.create(
            user=self.user, device=self.device, otp_code="123456"
        )

    def test_patch_session(self):
        data = {"otp_code": "123456"}
        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.session.token}"}
        response = self.client.patch(
            f"/session/{self.session.uuid}/",
            data,
            content_type="application/json",
            **auth_header,
        )

        self.session.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(
            response.json(),
            {
                "uuid": f"ses-{self.session.uuid}",
                "token": self.session.token,
                "status": "confirmed",
                "is_new_user": False,
                "is_new_device": False,
                "user": {
                    "uuid": f"usr-{self.session.user.uuid}",
                    "email": "test@example.com",
                },
                "device": {
                    "uuid": f"dev-{self.session.device.uuid}",
                    "type": "othr",
                },
            },
        )

    def test_patch_session__wrong_otp_code(self):
        data = {"otp_code": "123455"}
        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.session.token}"}
        response = self.client.patch(
            f"/session/{self.session.uuid}/",
            data,
            content_type="application/json",
            **auth_header,
        )

        self.assertEqual(response.status_code, 400)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "pending")

    def test_patch_session__no_headers(self):
        data = {"otp_code": "123456"}
        response = self.client.patch(
            f"/session/{self.session.uuid}/",
            data,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "pending")
        self.assertEqual(response.json(), {"error": "Unauthorized"})

    def test_patch_session__expired_session(self):
        expired_date = timezone.make_aware(datetime.datetime(2023, 12, 19))
        self.session.created_at = expired_date
        self.session.save()
        data = {"otp_code": "123456"}

        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.session.token}"}
        response = self.client.patch(
            f"/session/{self.session.uuid}/",
            data,
            content_type="application/json",
            **auth_header,
        )

        self.assertEqual(response.status_code, 401)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "expired")
