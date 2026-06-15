import os
import random
from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone as django_timezone
from django.core.mail import send_mail
from twilio.rest import Client
from rest_framework import serializers

from .models import User

OTP_EXPIRY_MINUTES = 5


def generate_user_token(user_id):
    payload = {
        "id": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=30),
    }
    return jwt.encode(payload, os.environ.get("JWT_SECRET", settings.SECRET_KEY), algorithm="HS256")


def generate_and_save_user_otp(user):
    otp = f"{random.randint(100000, 999999)}"
    user.otp = otp
    user.otp_created_at = django_timezone.now()
    user.save(update_fields=["otp", "otp_created_at", "updated_at"])
    
    # Send Email
    subject = "Your Verification Code"
    message = f"Your verification OTP code is: {otp}\nThis code will expire in {OTP_EXPIRY_MINUTES} minutes."
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[user.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email to {user.email}: {e}")

    # Send SMS via Twilio
    if user.mobile and getattr(settings, 'TWILIO_ACCOUNT_SID', None) and getattr(settings, 'TWILIO_AUTH_TOKEN', None):
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your Hostel Management verification code is {otp}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=user.mobile,
            )
        except Exception as e:
            print(f"Failed to send SMS to {user.mobile}: {e}")
        
    return otp


def user_otp_is_expired(user):
    if not user.otp_created_at:
        return True
    return django_timezone.now() > user.otp_created_at + timedelta(minutes=OTP_EXPIRY_MINUTES)


def find_user_by_email_or_mobile(email=None, mobile=None):
    user = User.objects.filter(email=email).first() if email else None
    if not user and mobile:
        user = User.objects.filter(mobile=mobile).first()
    return user


class UserSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    joinedHostel = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "_id",
            "name",
            "email",
            "mobile",
            "joinedHostel",
            "created_at",
            "updated_at",
        )

    def get_joinedHostel(self, obj):
        return obj.joined_hostel_dict()


class UserRegisterSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "email", "mobile", "password", "token")
        extra_kwargs = {
            "password": {"write_only": True},
            "mobile": {"write_only": True},
        }

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("User already exists")
        return value

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data["password"])
        return User.objects.create(**validated_data)

    def get_token(self, obj):
        return generate_user_token(obj.id)

    def to_representation(self, instance):
        return {
            "_id": instance.id,
            "name": instance.name,
            "email": instance.email,
            "token": generate_user_token(instance.id),
        }


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = User.objects.filter(email=attrs["email"]).first()
        if not user or not check_password(attrs["password"], user.password):
            raise serializers.ValidationError("Invalid credentials")
        attrs["user"] = user
        attrs["otp"] = generate_and_save_user_otp(user)
        return attrs

    def to_representation(self, instance):
        user = instance["user"]
        return {
            "message": "Login successful. OTP sent successfully",
            "_id": user.id,
            "name": user.name,
            "mobile": user.mobile,
            "email": user.email,
            "otp": instance["otp"],
            "token": generate_user_token(user.id),
        }


class UserSendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(required=False)

    def validate(self, attrs):
        email = attrs.get("email")
        mobile = attrs.get("mobile")
        if not email and not mobile:
            raise serializers.ValidationError("email or mobile is required")

        user = find_user_by_email_or_mobile(email=email, mobile=mobile)
        if not user:
            raise serializers.ValidationError("User not found")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        otp = generate_and_save_user_otp(user)
        return user, otp


class UserVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        mobile = attrs.get("mobile")
        otp = attrs.get("otp")

        if not email and not mobile:
            raise serializers.ValidationError("email or mobile is required")

        user = find_user_by_email_or_mobile(email=email, mobile=mobile)
        if not user:
            raise serializers.ValidationError("User not found")
        if not user.otp:
            raise serializers.ValidationError("OTP not requested")
        if user_otp_is_expired(user):
            raise serializers.ValidationError("OTP expired")
        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.otp = None
        user.otp_created_at = None
        user.save(update_fields=["otp", "otp_created_at", "updated_at"])
        return user


class UserForgotPasswordSerializer(UserSendOTPSerializer):
    pass


class UserResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        mobile = attrs.get("mobile")
        otp = attrs.get("otp")

        if not email and not mobile:
            raise serializers.ValidationError("email or mobile is required")

        user = find_user_by_email_or_mobile(email=email, mobile=mobile)
        if not user:
            raise serializers.ValidationError("User not found")
        if not user.otp:
            raise serializers.ValidationError("OTP not requested")
        if user_otp_is_expired(user):
            raise serializers.ValidationError("OTP expired")
        if user.otp != otp:
            raise serializers.ValidationError("Invalid OTP")

        attrs["user"] = user
        return attrs

    def save(self):
        user = self.validated_data["user"]
        user.password = make_password(self.validated_data["new_password"])
        user.otp = None
        user.otp_created_at = None
        user.save(update_fields=["password", "otp", "otp_created_at", "updated_at"])
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("name", "email", "mobile")
        extra_kwargs = {
            "email": {"required": False},
            "mobile": {"required": False},
            "name": {"required": False},
        }

    def validate_email(self, value):
        user = self.instance
        if User.objects.exclude(id=user.id).filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value

    def validate_mobile(self, value):
        user = self.instance
        if User.objects.exclude(id=user.id).filter(mobile=value).exists():
            raise serializers.ValidationError("Mobile already in use")
        return value
