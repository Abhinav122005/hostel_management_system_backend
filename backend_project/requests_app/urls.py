from django.urls import path

from . import views


urlpatterns = [
    # Send a new request
    path("send/", views.send_request, name="send_request"),
    # Get all requests sent by a user
    path("user/<int:user_id>/", views.get_user_requests, name="get_user_requests"),
    # Get all requests received by an owner
    path("owner/<int:owner_id>/", views.get_owner_requests, name="get_owner_requests"),
    # Update status of a request
    path("<int:request_id>/status/", views.update_request_status, name="update_request_status"),
    # Search for users
    path("searchusers/", views.search_users, name="search_users"),
    # Get the joined hostel for a user
    path("hostel/<int:user_id>/", views.get_joined_hostel, name="get_joined_hostel"),
]
