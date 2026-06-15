from django.db import models
from users.models import User
from owners.models import Owner

class Notification(models.Model):
    RECIPIENT_CHOICES = (
        ('user', 'User'),
        ('owner', 'Owner'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    recipient_type = models.CharField(max_length=10, choices=RECIPIENT_CHOICES)
    type = models.CharField(max_length=50) # 'request', 'chat', etc.
    message = models.TextField()
    read = models.BooleanField(default=False)
    data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - to {self.recipient_type}"
