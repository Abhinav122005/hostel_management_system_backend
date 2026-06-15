from django.db import models


class Owner(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=20)
    password = models.CharField(max_length=255)
    payu_key = models.CharField(max_length=255, blank=True, null=True)
    payu_salt = models.CharField(max_length=255, blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email

    def public_dict(self):
        return {
            "_id": self.id,
            "name": self.name,
            "email": self.email,
            "mobile": self.mobile,
            "payuKey": self.payu_key,
            "payuSalt": self.payu_salt,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

# Create your models here.

