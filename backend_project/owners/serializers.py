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

from .models import Owner

OTP_EXPIRY_MINUTES = 5


def generate_owner_token(owner_id):
    payload = {
        "id": owner_id,
        "role": "owner",
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
    }
    return jwt.encode(payload, os.environ.get("JWT_SECRET", "secret123"), algorithm="HS256")


def generate_and_save_owner_otp(owner):
    otp = f"{random.randint(100000, 999999)}"
    owner.otp = otp
    owner.otp_created_at = django_timezone.now()
    owner.save(update_fields=["otp", "otp_created_at"])
    
    # Send Email
    subject = "Your Verification Code"
    message = f"Your verification OTP code is: {otp}\nThis code will expire in {OTP_EXPIRY_MINUTES} minutes."
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[owner.email],
            fail_silently=True,
        )
    except Exception as e:
        print(f"Failed to send email to {owner.email}: {e}")

    # Send SMS via Twilio
    if owner.mobile and getattr(settings, 'TWILIO_ACCOUNT_SID', None) and getattr(settings, 'TWILIO_AUTH_TOKEN', None):
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=f"Your Hostel Management verification code is {otp}",
                from_=settings.TWILIO_PHONE_NUMBER,
                to=owner.mobile,
            )
        except Exception as e:
            print(f"Failed to send SMS to {owner.mobile}: {e}")
        
    return otp


def owner_otp_is_expired(owner):
    if not owner.otp_created_at:
        return True
    return django_timezone.now() > owner.otp_created_at + timedelta(minutes=OTP_EXPIRY_MINUTES)


def find_owner_by_email_or_mobile(email=None, mobile=None):
    owner = Owner.objects.filter(email=email).first() if email else None
    if not owner and mobile:
        owner = Owner.objects.filter(mobile=mobile).first()
    return owner


def default_payu_key():
    return os.environ.get("PAYU_MERCHANT_KEY") or os.environ.get("MERCHANT_KEY")


def default_payu_salt():
    return os.environ.get("PAYU_MERCHANT_SALT") or os.environ.get("MERCHANT_SALT")


class OwnerSerializer(serializers.ModelSerializer):
    _id = serializers.IntegerField(source="id", read_only=True)
    payuKey = serializers.CharField(source="payu_key", read_only=True)
    payuSalt = serializers.CharField(source="payu_salt", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = Owner
        fields = ("_id", "name", "email", "mobile", "payuKey", "payuSalt", "createdAt")


class OwnerRegisterSerializer(serializers.ModelSerializer):
    payuKey = serializers.CharField(required=False, allow_blank=True, write_only=True)
    payuSalt = serializers.CharField(required=False, allow_blank=True, write_only=True)

    class Meta:
        model = Owner
        fields = ("name", "email", "mobile", "password", "payuKey", "payuSalt")
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        if Owner.objects.filter(email=value).exists():
            raise serializers.ValidationError("Owner already exists")
        return value

    def create(self, validated_data):
        payu_key = validated_data.pop("payuKey", None) or default_payu_key()
        payu_salt = validated_data.pop("payuSalt", None) or default_payu_salt()
        validated_data["password"] = make_password(validated_data["password"])
        return Owner.objects.create(
            **validated_data,
            payu_key=payu_key,
            payu_salt=payu_salt,
        )


class OwnerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        owner = Owner.objects.filter(email=attrs["email"]).first()
        if not owner:
            raise serializers.ValidationError({"message": "Owner not found"})
        if not check_password(attrs["password"], owner.password):
            raise serializers.ValidationError({"message": "Invalid credentials"})
        attrs["owner"] = owner
        attrs["otp"] = generate_and_save_owner_otp(owner)
        return attrs


class OwnerSendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(required=False)

    def validate(self, attrs):
        email = attrs.get("email")
        mobile = attrs.get("mobile")
        if not email and not mobile:
            raise serializers.ValidationError("email or mobile is required")

        owner = find_owner_by_email_or_mobile(email=email, mobile=mobile)
        if not owner:
            raise serializers.ValidationError("Owner not found")

        attrs["owner"] = owner
        return attrs

    def save(self):
        owner = self.validated_data["owner"]
        otp = generate_and_save_owner_otp(owner)
        return owner, otp


class OwnerVerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    mobile = serializers.CharField(required=False)
    otp = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get("email")
        mobile = attrs.get("mobile")
        otp = attrs.get("otp")

        if not email and not mobile:
            raise serializers.ValidationError("email or mobile is required")

        owner = find_owner_by_email_or_mobile(email=email, mobile=mobile)
        if not owner:
            raise serializers.ValidationError("Owner not found")
        if not owner.otp:
            raise serializers.ValidationError("OTP not requested")
        if owner_otp_is_expired(owner):
            raise serializers.ValidationError("OTP expired")
        if owner.otp != otp:
            raise serializers.ValidationError("Invalid OTP")

        attrs["owner"] = owner
        return attrs

    def save(self):
        owner = self.validated_data["owner"]
        owner.otp = None
        owner.otp_created_at = None
        owner.save(update_fields=["otp", "otp_created_at"])
        return owner


class OwnerForgotPasswordSerializer(OwnerSendOTPSerializer):
    pass


class OwnerResetPasswordSerializer(serializers.Serializer):
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

        owner = find_owner_by_email_or_mobile(email=email, mobile=mobile)
        if not owner:
            raise serializers.ValidationError("Owner not found")
        if not owner.otp:
            raise serializers.ValidationError("OTP not requested")
        if owner_otp_is_expired(owner):
            raise serializers.ValidationError("OTP expired")
        if owner.otp != otp:
            raise serializers.ValidationError("Invalid OTP")

        attrs["owner"] = owner
        return attrs

    def save(self):
        owner = self.validated_data["owner"]
        owner.password = make_password(self.validated_data["new_password"])
        owner.otp = None
        owner.otp_created_at = None
        owner.save(update_fields=["password", "otp", "otp_created_at"])
        return owner


class OwnerUpdateSerializer(serializers.ModelSerializer):
    payuKey = serializers.CharField(source="payu_key", required=False, allow_blank=True)
    payuSalt = serializers.CharField(source="payu_salt", required=False, allow_blank=True)

    class Meta:
        model = Owner
        fields = ("name", "email", "mobile", "payuKey", "payuSalt")
        extra_kwargs = {
            "email": {"required": False},
            "mobile": {"required": False},
            "name": {"required": False},
        }

    def validate_email(self, value):
        owner = self.instance
        if Owner.objects.exclude(id=owner.id).filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value
        
    def validate_mobile(self, value):
        owner = self.instance
        if Owner.objects.exclude(id=owner.id).filter(mobile=value).exists():
            raise serializers.ValidationError("Mobile already in use")
        return value
