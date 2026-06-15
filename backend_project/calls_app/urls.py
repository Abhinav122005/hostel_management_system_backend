from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_call, name='create_call'),
    path('update/<int:call_id>/', views.update_call_status, name='update_call_status'),
    path('user/<int:user_id>/', views.get_user_calls, name='get_user_calls'),
]
