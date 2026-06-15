from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Owner
from .serializers import (
    OwnerForgotPasswordSerializer,
    OwnerLoginSerializer,
    OwnerRegisterSerializer,
    OwnerResetPasswordSerializer,
    OwnerSendOTPSerializer,
    OwnerSerializer,
    OwnerUpdateSerializer,
    OwnerVerifyOTPSerializer,
    generate_owner_token,
)


def _otp_error_response(serializer):
    errors = serializer.errors.get("non_field_errors")
    message = errors[0] if errors else serializer.errors
    if message == "Owner not found":
        return Response({"message": message}, status=status.HTTP_404_NOT_FOUND)
    return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


# """
# Expected JSON Payload:
# {
#   "name": "Jane Owner",
#   "email": "jane@example.com",
#   "mobile": "0987654321",
#   "password": "ownerpassword"
# }
# """
@api_view(["POST"])
def register_owner(request):
    serializer = OwnerRegisterSerializer(data=request.data)
    if serializer.is_valid():
        owner = serializer.save()
        return Response(
            {
                "message": "Owner registered successfully",
                "owner": OwnerSerializer(owner).data,
            },
            status=status.HTTP_201_CREATED,
        )

    if "email" in serializer.errors:
        return Response({"message": "Owner already exists"}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# """
# Expected JSON Payload:
# {
#   "email": "jane@example.com",
#   "password": "ownerpassword"
# }
# """
@api_view(["POST"])
def login_owner(request):
    serializer = OwnerLoginSerializer(data=request.data)
    if not serializer.is_valid():
        detail = serializer.errors.get("non_field_errors")
        if detail:
            message = serializer.errors["non_field_errors"][0]
            if isinstance(message, dict):
                return Response(message, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

    owner = serializer.validated_data["owner"]
    return Response(
        {
            "message": "Login successful. OTP sent successfully",
            "token": generate_owner_token(owner.id),
            "otp": serializer.validated_data["otp"],
            "owner": OwnerSerializer(owner).data,
        },
        status=status.HTTP_200_OK,
    )


# """
# Expected JSON Payload:
# {
#   "name": "Updated Owner Name",
#   "email": "updated@example.com",
#   "mobile": "8888888888",
#   "payuKey": "new_payu_key",
#   "payuSalt": "new_payu_salt"
# }
# """
@api_view(["PUT"])
def update_owner_profile(request, owner_id):
    owner = Owner.objects.filter(id=owner_id).first()
    if not owner:
        return Response({"message": "Owner not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = OwnerUpdateSerializer(owner, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                "message": "Profile updated successfully",
                "owner": OwnerSerializer(owner).data,
            },
            status=status.HTTP_200_OK,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# """
# Expected JSON Payload:
# {
#   "email": "jane@example.com"
# }
# """
@api_view(["POST"])
def send_owner_otp(request):
    serializer = OwnerSendOTPSerializer(data=request.data)
    if serializer.is_valid():
        owner, otp = serializer.save()
        return Response(
            {
                "message": "OTP sent successfully",
                "ownerId": owner.id,
                "email": owner.email,
                "otp": otp,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


# """
# Expected JSON Payload:
# {
#   "email": "jane@example.com",
#   "otp": "123456"
# }
# """
@api_view(["POST"])
def verify_owner_otp(request):
    serializer = OwnerVerifyOTPSerializer(data=request.data)
    if serializer.is_valid():
        owner = serializer.save()
        return Response(
            {
                "message": "OTP verified successfully",
                "ownerId": owner.id,
                "email": owner.email,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


# """
# Expected JSON Payload:
# {
#   "email": "jane@example.com"
# }
# """
@api_view(["POST"])
def forgot_owner_password(request):
    serializer = OwnerForgotPasswordSerializer(data=request.data)
    if serializer.is_valid():
        owner, otp = serializer.save()
        return Response(
            {
                "message": "Password reset OTP sent successfully",
                "ownerId": owner.id,
                "email": owner.email,
                "otp": otp,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


# """
# Expected JSON Payload:
# {
#   "email": "jane@example.com",
#   "otp": "123456",
#   "password": "newpassword"
# }
# """
@api_view(["POST"])
def reset_owner_password(request):
    serializer = OwnerResetPasswordSerializer(data=request.data)
    if serializer.is_valid():
        owner = serializer.save()
        return Response(
            {
                "message": "Password reset successfully",
                "ownerId": owner.id,
                "email": owner.email,
            },
            status=status.HTTP_200_OK,
        )

    return _otp_error_response(serializer)


@api_view(["GET"])
def verify_payu(request, owner_id):
    owner = Owner.objects.filter(id=owner_id).first()
    if not owner:
        return Response({"message": "Owner not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "merchantKey": owner.payu_key,
            "merchantSalt": owner.payu_salt,
        },
        status=status.HTTP_200_OK,
    )
