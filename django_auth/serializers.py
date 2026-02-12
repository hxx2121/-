from __future__ import annotations

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from django_auth.models import UserProfile

User = get_user_model()


def _get_or_create_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128)

    def validate_username(self, value: str) -> str:
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
        )
        _get_or_create_profile(user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, max_length=128)

    def validate(self, attrs):
        user = authenticate(username=attrs.get("username"), password=attrs.get("password"))
        if user is None:
            raise serializers.ValidationError("用户名或密码错误")
        if not user.is_active:
            raise serializers.ValidationError("用户已被禁用")
        attrs["user"] = user
        return attrs


class MeUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128, required=False)
    role = serializers.CharField(max_length=32, required=False)

    def validate_username(self, value: str) -> str:
        user = self.context.get("user")
        qs = User.objects.filter(username=value)
        if user is not None:
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def update(self, instance, validated_data):
        if "username" in validated_data:
            instance.username = validated_data["username"]
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()

        profile = _get_or_create_profile(instance)
        if "role" in validated_data:
            profile.role = validated_data["role"]
            profile.save()
        return instance


class UserAdminListSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "is_staff", "is_superuser", "role", "date_joined"]

    def get_role(self, obj) -> str:
        profile = getattr(obj, "profile", None)
        return getattr(profile, "role", "user")


class UserAdminUpdateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=False)
    password = serializers.CharField(write_only=True, min_length=6, max_length=128, required=False)
    role = serializers.CharField(max_length=32, required=False)

    def validate_username(self, value: str) -> str:
        user = self.context.get("user")
        qs = User.objects.filter(username=value)
        if user is not None:
            qs = qs.exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def update(self, instance, validated_data):
        if "username" in validated_data:
            instance.username = validated_data["username"]
        if "password" in validated_data:
            instance.set_password(validated_data["password"])
        instance.save()

        profile = _get_or_create_profile(instance)
        if "role" in validated_data:
            profile.role = validated_data["role"]
            profile.save()
        return instance
