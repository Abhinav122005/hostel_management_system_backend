from django.db import models
from users.models import User
from owners.models import Owner

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'owner')
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation between {self.user.email} and {self.owner.email}"

class Message(models.Model):
    SENDER_CHOICES = (
        ('USER', 'User'),
        ('OWNER', 'Owner'),
    )
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender_type = models.CharField(max_length=10, choices=SENDER_CHOICES)
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message by {self.sender_type} in {self.conversation}"
