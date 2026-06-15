from django.db import models

from hostels_app.models import Hostel
from users.models import User


class Booking(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookings")
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="bookings")
    sharing_type = models.CharField(max_length=50)
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    vacancy_deducted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["hostel"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Booking {self.id} - {self.user.email}"

