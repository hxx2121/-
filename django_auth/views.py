from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request
from rest_framework.authtoken.models import Token

from django_auth.models import UserProfile
from django_auth.serializers import (
    LoginSerializer,
    MeUpdateSerializer,
    RegisterSerializer,
    UserAdminListSerializer,
    UserAdminUpdateSerializer,
)
from django_auth.utils.decorators import admin_required, login_required
from django_main.R import R

User = get_user_model()


def _get_or_create_profile(user) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _user_data(user):
    profile = getattr(user, "profile", None) or _get_or_create_profile(user)
    return {
        "id": user.id,
        "username": user.username,
        "role": profile.role,
        "is_admin": bool(user.is_staff or user.is_superuser),
    }


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request: Request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            msg = "参数错误"
            username_errors = errors.get("username")
            if isinstance(username_errors, (list, tuple)) and username_errors:
                msg = str(username_errors[0])
            return R.validation_error(msg=msg, data=errors)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        data = _user_data(user)
        data["token"] = token.key
        return R.ok(data=data, msg="注册成功")


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request: Request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            errors = serializer.errors
            msg = "参数错误"
            non_field_errors = errors.get("non_field_errors")
            if isinstance(non_field_errors, (list, tuple)) and non_field_errors:
                msg = str(non_field_errors[0])
            return R.validation_error(msg=msg, data=errors)
        user = serializer.validated_data["user"]
        _get_or_create_profile(user)
        token, _ = Token.objects.get_or_create(user=user)
        data = _user_data(user)
        data["token"] = token.key
        return R.ok(data=data, msg="登录成功")


class LogoutView(GenericAPIView):
    @login_required
    def post(self, request: Request):
        Token.objects.filter(user=request.user).delete()
        return R.ok(msg="退出成功")


class MeUpdateView(GenericAPIView):
    serializer_class = MeUpdateSerializer

    @login_required
    def get(self, request: Request):
        return R.ok(data=_user_data(request.user))

    @login_required
    def put(self, request: Request):
        return self._update(request, partial=False)

    @login_required
    def patch(self, request: Request):
        return self._update(request, partial=True)

    def _update(self, request: Request, partial: bool):
        serializer = self.get_serializer(
            instance=request.user,
            data=request.data,
            partial=partial,
            context={"user": request.user},
        )
        if not serializer.is_valid():
            return R.validation_error(msg="参数错误", data=serializer.errors)
        user = serializer.save()
        return R.ok(data=_user_data(user), msg="修改成功")


class AdminUserListView(GenericAPIView):
    @admin_required
    def get(self, request: Request):
        users = User.objects.all().select_related("profile").order_by("id")
        serializer = UserAdminListSerializer(users, many=True)
        return R.ok(data=serializer.data)


class AdminUserDetailView(GenericAPIView):
    serializer_class = UserAdminUpdateSerializer

    @admin_required
    def put(self, request: Request, user_id: int):
        return self._update(request, user_id=user_id, partial=False)

    @admin_required
    def patch(self, request: Request, user_id: int):
        return self._update(request, user_id=user_id, partial=True)

    @admin_required
    def delete(self, request: Request, user_id: int):
        user = User.objects.filter(pk=user_id).first()
        if user is None:
            return R.fail(msg="用户不存在", code=40401, http_status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return R.ok(msg="删除成功")

    def _update(self, request: Request, user_id: int, partial: bool):
        user = User.objects.filter(pk=user_id).select_related("profile").first()
        if user is None:
            return R.fail(msg="用户不存在", code=40401, http_status=status.HTTP_404_NOT_FOUND)

        serializer = self.get_serializer(
            instance=user,
            data=request.data,
            partial=partial,
            context={"user": user},
        )
        if not serializer.is_valid():
            return R.validation_error(msg="参数错误", data=serializer.errors)
        serializer.save()
        return R.ok(data=_user_data(user), msg="修改成功")
