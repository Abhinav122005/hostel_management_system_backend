from django.db import models


class User(models.Model):
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    mobile = models.CharField(max_length=20, unique=True)
    password = models.CharField(max_length=255)

    joined_hostel = models.ForeignKey(
        'hostels_app.Hostel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='active_users'
    )
    joined_sharing_type = models.CharField(max_length=50, blank=True)
    joined_sharing_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )
    joined_date = models.DateTimeField(blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

    def public_dict(self):
        return {
            "_id": self.id,
            "name": self.name,
            "email": self.email,
            "mobile": self.mobile,
        }

    def joined_hostel_dict(self):
        if not self.joined_hostel:
            return None

        return {
            "hostelId": str(self.joined_hostel.id),
            "hostelName": self.joined_hostel.name,
            "ownerId": str(self.joined_hostel.owner_id),
            "sharingType": self.joined_sharing_type,
            "sharingPrice": str(self.joined_sharing_price)
            if self.joined_sharing_price is not None
            else None,
            "joinedDate": self.joined_date.isoformat() if self.joined_date else None,
        }

# Create your models here.

