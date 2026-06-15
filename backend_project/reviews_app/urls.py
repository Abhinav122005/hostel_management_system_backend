from django.urls import path
from . import views

urlpatterns = [
    # Hostel Reviews
    path("hostels/add/", views.add_review, name="add_review"),
    path("hostels/<int:hostel_id>/", views.get_hostel_reviews, name="get_hostel_reviews"),
    path("hostels/delete/<int:review_id>/", views.delete_review, name="delete_review"),
    
    # User Reviews (by Owners)
    path("users/add/", views.add_user_review, name="add_user_review"),
    path("users/<int:user_id>/", views.get_user_reviews, name="get_user_reviews"),
    path("users/delete/<int:review_id>/", views.delete_user_review, name="delete_user_review"),
]