from django.db import models
from users.models import User

class Call(models.Model):
    STATUS_CHOICES = [
        ('ringing', 'Ringing'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('missed', 'Missed'),
    ]

    caller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_made')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calls_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ringing')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call from {self.caller.email} to {self.receiver.email} - {self.status}"
    
    def to_dict(self):
        return {
            "id": self.id,
            "callerId": self.caller.id,
            "receiverId": self.receiver.id,
            "status": self.status,
            "createdAt": self.created_at.isoformat(),
        }
