from django.urls import path
from . import views

urlpatterns = [
    # get or create conversations
    path('conversations/', views.conversation_list, name='conversation_list'),
    
    # get or send messages in a specific conversation
    path('conversations/<int:conversation_id>/messages/', views.message_list, name='message_list'),
]
