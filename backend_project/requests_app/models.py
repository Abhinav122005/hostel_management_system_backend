from django.db import models

from hostels_app.models import Hostel
from owners.models import Owner
from users.models import User


class HostelRequest(models.Model):
    SENDER_CHOICES = [
        ("owner", "Owner"),
        ("user", "User"),
    ]
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="hostel_requests")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hostel_requests")
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="hostel_requests")
    sender_type = models.CharField(max_length=20, choices=SENDER_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    sharing_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sharing_type = models.CharField(max_length=50)
    vacancy_deducted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner"]),
            models.Index(fields=["user"]),
            models.Index(fields=["hostel"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Request {self.id} - {self.status}"
