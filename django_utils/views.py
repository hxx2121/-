from __future__ import annotations

import mimetypes

from django.http import FileResponse
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

from django_auth.utils.decorators import admin_required, login_required
from django_main.R import R
from django_utils.models import UserFile
from django_utils.serializers import FileUploadSerializer, UserFileSerializer


class FileUploadView(GenericAPIView):
    serializer_class = FileUploadSerializer

    @login_required
    def post(self, request: Request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return R.validation_error(msg="参数错误", data=serializer.errors)
        user_file = serializer.save()
        return R.ok(data=UserFileSerializer(user_file).data, msg="上传成功")


class FileListView(GenericAPIView):
    @login_required
    def get(self, request: Request):
        files = UserFile.objects.filter(uploader=request.user).order_by("-id")
        return R.ok(data=UserFileSerializer(files, many=True).data)


class FileDownloadView(GenericAPIView):
    @login_required
    def get(self, request: Request, file_id: int):
        user_file = UserFile.objects.filter(pk=file_id).select_related("uploader").first()
        if user_file is None:
            return R.fail(msg="文件不存在", code=40401, http_status=status.HTTP_404_NOT_FOUND)

        if not (
            getattr(request.user, "is_staff", False)
            or getattr(request.user, "is_superuser", False)
            or user_file.uploader_id == request.user.id
        ):
            return R.forbidden(msg="无权限访问该文件")

        file_field = user_file.file
        if not file_field or not file_field.name:
            return R.fail(msg="文件不存在", code=40402, http_status=status.HTTP_404_NOT_FOUND)

        content_type, _ = mimetypes.guess_type(user_file.original_name)
        response = FileResponse(
            file_field.open("rb"),
            as_attachment=True,
            filename=user_file.original_name,
            content_type=content_type or "application/octet-stream",
        )
        return response


class FileDeleteView(GenericAPIView):
    @login_required
    def delete(self, request: Request, file_id: int):
        user_file = UserFile.objects.filter(pk=file_id).select_related("uploader").first()
        if user_file is None:
            return R.fail(msg="文件不存在", code=40401, http_status=status.HTTP_404_NOT_FOUND)

        if not (
            getattr(request.user, "is_staff", False)
            or getattr(request.user, "is_superuser", False)
            or user_file.uploader_id == request.user.id
        ):
            return R.forbidden(msg="无权限删除该文件")

        file_field = user_file.file
        user_file.delete()
        if file_field:
            file_field.delete(save=False)
        return R.ok(msg="删除成功")


class AdminFileListView(GenericAPIView):
    @admin_required
    def get(self, request: Request):
        files = UserFile.objects.all().order_by("-id")
        return R.ok(data=UserFileSerializer(files, many=True).data)


class AdminFileDeleteView(GenericAPIView):
    @admin_required
    def delete(self, request: Request, file_id: int):
        user_file = UserFile.objects.filter(pk=file_id).first()
        if user_file is None:
            return R.fail(msg="文件不存在", code=40401, http_status=status.HTTP_404_NOT_FOUND)

        file_field = user_file.file
        user_file.delete()
        if file_field:
            file_field.delete(save=False)
        return R.ok(msg="删除成功")
