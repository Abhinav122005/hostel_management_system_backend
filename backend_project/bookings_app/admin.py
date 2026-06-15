from django.contrib import admin

from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "hostel", "sharing_type", "status", "created_at")
    list_filter = ("status", "sharing_type", "created_at")
    search_fields = ("user__name", "user__email", "hostel__name", "hostel__area")
