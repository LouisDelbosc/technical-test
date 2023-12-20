from django.test import TestCase
from django.urls import reverse
from ..models import User, Device, Session


class SessionViewTestCase(TestCase):
    def setUp(self):
        # Set up a test user and device if necessary
        self.user = User.objects.create(email="test@example.com")
        self.device = Device.objects.create(user=self.user, type="othr")

    def test_post_session(self):
        data = {"user": {"email": self.user.email}, "device": {"type": "othr"}}
        response = self.client.post("/session/", data, content_type="application/json")

        session = Session.objects.filter(user=self.user, device=self.device).first()
        self.assertEqual(response.status_code, 201)
        json = response.json()
        self.assertDictEqual(
            json,
            {
                "uuid": f"ses-{session.uuid}",
                "token": session.token,
                "user": {
                    "uuid": f"usr-{self.user.uuid}",
                    "email": "test@example.com",
                },
                "device": {
                    "uuid": f"dev-{self.device.uuid}",
                    "type": "othr",
                },
                "status": "pending",
            },
        )

    def test_post_session__already_created(self):
        data = {"user": {"email": self.user.email}, "device": {"type": "othr"}}

        response = self.client.post("/session/", data, content_type="application/json")
        self.assertEqual(response.status_code, 201)

        response = self.client.post("/session/", data, content_type="application/json")
        self.assertEqual(response.status_code, 200)
