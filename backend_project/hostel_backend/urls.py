"""
URL configuration for hostel_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Admin dashboard route
    path('admin/', admin.site.urls),
    # User-related endpoints
    path('api/users/', include('users.urls')),
    # Owner-related endpoints
    path('api/owner/', include('owners.urls')),
    # Hostel management endpoints
    path('api/hostels/', include('hostels_app.urls')),
    # Booking management endpoints
    path('api/bookings/', include('bookings_app.urls')),
    # Request handling endpoints
    path('api/requests/', include('requests_app.urls')),
    # Review management endpoints
    path('api/reviews/', include('reviews_app.urls')),
    # Transaction handling endpoints
    path('api/transactions/', include('transactions_app.urls')),
    # Chat app endpoints
    path('api/chat/', include('chat_app.urls')),
    # Notifications app endpoints
    path('api/notifications/', include('notifications_app.urls')),
    # Calls app endpoints
    path('api/calls/', include('calls_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
