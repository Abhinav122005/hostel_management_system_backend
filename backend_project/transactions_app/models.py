from django.db import models
from users.models import User
from owners.models import Owner
from hostels_app.models import Hostel

class Transaction(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("success", "Success"),
        ("failed", "Failed"),
    ]

    PAYMENT_TYPE_CHOICES = [
        ("rent", "Rent"),
        ("booking", "Booking"),
        ("deposit", "Deposit"),
        ("other", "Other"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transactions")
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="transactions")
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="transactions")
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=255, unique=True, blank=True, null=True) # Local or PayU ID
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default="rent")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    description = models.TextField(blank=True)
    
    payu_hash = models.CharField(max_length=255, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Txn {self.id} - {self.status} - {self.amount}"
