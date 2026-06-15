from django.urls import path
from . import views

urlpatterns = [
    # Get all notifications for a specific user
    path('user/<int:user_id>/', views.get_user_notifications, name='get_user_notifications'),
    
    # Get all notifications for a specific owner
    path('owner/<int:owner_id>/', views.get_owner_notifications, name='get_owner_notifications'),
    
    # Create a new notification
    path('create/', views.create_notification, name='create_notification'),
    
    # Mark a specific notification as read
    path('read/<int:notification_id>/', views.mark_as_read, name='mark_as_read'),
    
    # Delete a specific notification
    path('<int:notification_id>/', views.delete_notification, name='delete_notification'),
]
