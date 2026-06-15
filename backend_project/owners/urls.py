from django.urls import path

from . import views


urlpatterns = [
    # Register a new owner
    path("register/", views.register_owner, name="register_owner"),
    # Login an owner
    path("login/", views.login_owner, name="login_owner"),
    # Send OTP for owner verification
    path("send-otp/", views.send_owner_otp, name="send_owner_otp"),
    # Verify owner OTP
    path("verify-otp/", views.verify_owner_otp, name="verify_owner_otp"),
    # Forgot owner password request
    path("forgot-password/", views.forgot_owner_password, name="forgot_owner_password"),
    # Reset owner password
    path("reset-password/", views.reset_owner_password, name="reset_owner_password"),
    # Verify PayU credentials for an owner
    path("verify/<int:owner_id>/", views.verify_payu, name="verify_payu"),
    # Update owner profile
    path("update/<int:owner_id>/", views.update_owner_profile, name="update_owner_profile"),
]
