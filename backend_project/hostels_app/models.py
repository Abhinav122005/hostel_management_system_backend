from django.db import models

from owners.models import Owner
from users.models import User


class Hostel(models.Model):
    HOSTEL_TYPES = [
        ("boys", "Boys"),
        ("girls", "Girls"),
        ("room", "Room"),
    ]

    name = models.CharField(max_length=255)
    area = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    description = models.TextField(blank=True)
    distance = models.FloatField(blank=True, null=True)
    rating = models.FloatField(default=0)

    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name="hostels")
    type = models.CharField(max_length=20, choices=HOSTEL_TYPES, blank=True)

    images = models.JSONField(default=list, blank=True)
    videos = models.JSONField(default=list, blank=True)
    sharing_media = models.JSONField(default=dict, blank=True)
    sharing_images = models.JSONField(default=dict, blank=True)

    room_sharing = models.JSONField(default=dict, blank=True)
    vacancy = models.JSONField(default=dict, blank=True)

    longitude = models.FloatField(default=0)
    latitude = models.FloatField(default=0)

    hostel_users = models.ManyToManyField(User, blank=True, related_name="joined_hostels")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["area"]),
            models.Index(fields=["type"]),
            models.Index(fields=["rating"]),
        ]

    def __str__(self):
        return self.name

    def public_dict(self, include_users=False):
        data = {
            "_id": self.id,
            "name": self.name,
            "area": self.area,
            "address": self.address,
            "description": self.description,
            "distance": self.distance,
            "rating": self.rating,
            "ownerId": self.owner_id,
            "type": self.type,
            "images": self.images,
            "videos": self.videos,
            "sharingMedia": self.sharing_media,
            "sharingImages": self.sharing_images,
            "roomSharing": self.room_sharing,
            "vacancy": self.vacancy,
            "location": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude],
            },
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }

        if include_users:
            data["hostelUsers"] = [user.public_dict() for user in self.hostel_users.all()]

        return data
