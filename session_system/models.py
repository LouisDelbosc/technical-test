from django.db import models
import uuid
import random
import secrets


def deconstruct_uuid(prefixed_uuid):
    prefix, uuid = prefixed_uuid.split("-", 1)
    return prefix, uuid


class User(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    email = models.EmailField(unique=True)

    def __str__(self):
        return f"usr-{self.uuid}"


class Device(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    vendor_uuid = models.UUIDField(null=True, blank=True)
    type = models.CharField(
        max_length=10,
        choices=[("mobi", "Mobile"), ("othr", "Other")],
    )

    def __str__(self):
        return f"dev-{self.uuid}"


class Session(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    token = models.CharField(max_length=40, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=10,
        choices=[
            ("pending", "Pending"),
            ("confirmed", "Confirmed"),
            ("expired", "Expired"),
        ],
        default="pending",
    )
    is_new_user = models.BooleanField(default=False)
    is_new_device = models.BooleanField(default=False)
    otp_code = models.CharField(max_length=6, blank=True)

    def __str__(self):
        return f"ses-{self.uuid}"

    def generate_token(self):
        return secrets.token_urlsafe(20)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generate_token()
        if not self.otp_code:
            # Generate a 6-digit random number as a string
            self.otp_code = "".join([str(random.randint(0, 9)) for _ in range(6)])
        super().save(*args, **kwargs)
