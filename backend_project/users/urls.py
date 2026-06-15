from django.urls import path

from . import views


urlpatterns = [
    # Register a new user
    path("register/", views.register_user, name="register_user"),
    # Login a user
    path("login/", views.login_user, name="login_user"),
    # Send OTP for user verification
    path("send-otp/", views.send_user_otp, name="send_user_otp"),
    # Verify user OTP
    path("verify-otp/", views.verify_user_otp, name="verify_user_otp"),
    # Forgot user password request
    path("forgot-password/", views.forgot_user_password, name="forgot_user_password"),
    # Reset user password
    path("reset-password/", views.reset_user_password, name="reset_user_password"),
    # Get user details by ID
    path("<int:user_id>/", views.get_user_by_id, name="get_user_by_id"),
    # Update user profile
    path("update/<int:user_id>/", views.update_user_profile, name="update_user_profile"),
]
