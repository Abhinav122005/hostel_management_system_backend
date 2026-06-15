from django.contrib import admin

from .models import HostelRequest


@admin.register(HostelRequest)
class HostelRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "user", "hostel", "sender_type", "status", "sharing_type", "created_at")
    list_filter = ("status", "sender_type", "sharing_type", "created_at")
    search_fields = ("owner__email", "user__email", "hostel__name")
