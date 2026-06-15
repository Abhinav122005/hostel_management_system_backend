from django.urls import path

from . import views


urlpatterns = [
    # Get all hostels
    path("all/", views.get_all_hostels, name="get_all_hostels"),
    # Get top-rated hostels
    path("top-rated/", views.get_top_rated_hostels, name="get_top_rated_hostels"),
    # Search hostels by area
    path("search/", views.get_hostels_by_area, name="get_hostels_by_area"),
    # Get details for a single hostel
    path("single/<int:hostel_id>/", views.get_single_hostel, name="get_single_hostel"),
    # Filter hostels by type
    path("filter/", views.filter_by_type, name="filter_by_type"),
    # Search hostels by area and type combined
    path("search-combo/", views.search_by_area_and_type, name="search_by_area_and_type"),
    # Get nearby hostels based on location
    path("nearby/", views.get_nearby_hostels, name="get_nearby_hostels"),
    # Get top-rated nearby hostels
    path("nearby/top-rated/", views.get_top_rated_hostels, name="get_nearby_top_rated_hostels"),
    # Add a new hostel
    path("add/", views.add_hostel, name="add_hostel"),
    # Decrement vacancy when a booking is made
    path("book/<int:hostel_id>/", views.decrement_vacancy, name="decrement_vacancy"),
    # Get the hostel that a specific user joined
    path("user/joined/<int:user_id>/", views.get_user_joined_hostel, name="get_user_joined_hostel"),
    # Get all hostels owned by a specific owner
    path("owner/<int:owner_id>/", views.get_hostels_by_owner, name="get_hostels_by_owner"),
    # Delete a specific hostel
    path("delete/<int:hostel_id>/", views.delete_hostel, name="delete_hostel"),
    # Get hostels with users registered under an owner
    path("owner/<int:owner_id>/hostel-users/", views.get_hostels_with_users, name="get_hostels_with_users"),
    # Get hostel by ID
    path("<int:hostel_id>/", views.get_hostel_by_id, name="get_hostel_by_id"),
]
