from django.contrib import admin

from .models import Hostel


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "area", "type", "owner", "rating", "created_at")
    list_filter = ("type", "area")
    search_fields = ("name", "area", "address", "owner__email")
