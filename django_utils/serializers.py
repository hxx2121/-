from __future__ import annotations

from rest_framework import serializers

from django_utils.models import UserFile


class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()

    def create(self, validated_data):
        request = self.context["request"]
        f = validated_data["file"]
        user_file = UserFile.objects.create(
            uploader=request.user if getattr(request.user, "is_authenticated", False) else None,
            file=f,
            original_name=getattr(f, "name", ""),
            size=getattr(f, "size", 0) or 0,
            content_type=getattr(f, "content_type", "") or "",
        )
        return user_file


class UserFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFile
        fields = ["id", "original_name", "size", "content_type", "created_at"]

