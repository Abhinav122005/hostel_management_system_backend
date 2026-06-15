from django.urls import path

from . import views


urlpatterns = [
    # Create a new booking
    path("add/", views.create_booking, name="create_booking"),
    # Get all bookings for a user
    path("user/<int:user_id>/", views.get_user_bookings, name="get_user_bookings"),
    # Get all bookings globally
    path("all/", views.get_all_bookings, name="get_all_bookings"),
    # Update status of a specific booking
    path("<int:booking_id>/status/", views.update_booking_status, name="update_booking_status"),
    # Approve a booking
    path("<int:booking_id>/approve/", views.approve_booking, name="approve_booking"),
    # Reject a booking
    path("<int:booking_id>/reject/", views.reject_booking, name="reject_booking"),
]
