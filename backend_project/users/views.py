from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import User
from .serializers import (
    UserForgotPasswordSerializer,
    UserLoginSerializer,
    UserRegisterSerializer,
    UserResetPasswordSerializer,
    UserSendOTPSerializer,
    UserSerializer,
    UserVerifyOTPSerializer,
    UserUpdateSerializer,
)


def _otp_error_response(serializer):
    errors = serializer.errors.get("non_field_errors")
    message = errors[0] if errors else serializer.errors
    if message == "User not found":
        return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


# """
# Expected JSON Payload:
# {
#   "name": "John Doe",
#   "email": "john@example.com",
#   "mobile": "1234567890",
#   "password": "secretpassword"
# }
# """
@api_view(["POST"])
def register_user(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserRegisterSerializer(user).data, status=status.HTTP_201_CREATED)

    if "email" in serializer.errors:
        return Response({"message": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# """
# Expected JSON Payload:
# {
#   "email": "john@example.com",
#   "password": "secretpassword"
# }
# """
@api_view(["POST"])
def login_user(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


# """
# Expected JSON Payload:
# {
#   "email": "john@example.com"
# }
# """
@api_view(["POST"])
def send_user_otp(request):
    serializer = UserSendOTPSerializer(data=request.data)
    if serializer.is_valid():
        user, otp = serializer.save()
        return Response(
            {
                "message": "OTP sent successfully",
                "userId": user.id,
                "email": user.email,
                "otp": otp,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


# """
# Expected JSON Payload:
# {
#   "email": "john@example.com",
#   "otp": "123456"
# }
# """
@api_view(["POST"])
def verify_user_otp(request):
    serializer = UserVerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "OTP verified successfully",
                "userId": user.id,
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


# """
# Expected JSON Payload:
# {
#   "email": "john@example.com"
# }
# """
@api_view(["POST"])
def forgot_user_password(request):
    serializer = UserForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        user, otp = serializer.save()
        return Response(
            {
                "message": "Password reset OTP sent successfully",
                "userId": user.id,
                "email": user.email,
                "otp": otp,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


# """
# Expected JSON Payload:
# {
#   "email": "john@example.com",
#   "otp": "123456",
#   "password": "newpassword"
# }
# """
@api_view(["POST"])
def reset_user_password(request):
    serializer = UserResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(
            {
                "message": "Password reset successfully",
                "userId": user.id,
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


@api_view(["GET"])
def get_user_by_id(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "user": UserSerializer(user).data,
            "joinedHostel": user.joined_hostel_dict(),
            "transactions": [],
            "count": 0,
        },
        status=status.HTTP_200_OK,
    )


# """
# Expected JSON Payload:
# {
#   "name": "Updated Name",
#   "email": "updated@example.com",
#   "mobile": "9876543210"
# }
# """
@api_view(["PUT"])
def update_user_profile(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Profile updated successfully",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)