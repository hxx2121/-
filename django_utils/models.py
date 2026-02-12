from django.conf import settings
from django.db import models


class UserFile(models.Model):
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_files",
    )
    file = models.FileField(upload_to="uploads/%Y/%m/%d/")
    original_name = models.CharField(max_length=255)
    size = models.BigIntegerField(default=0)
    content_type = models.CharField(max_length=127, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"UserFile(id={self.id}, original_name={self.original_name})"


class Attendance(models.Model):
    """考勤记录表：记录用户登录、活跃等考勤信息。"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="attendances"
    )
    date = models.DateField(help_text="考勤日期")
    sign_in_time = models.DateTimeField(null=True, blank=True, help_text="签到时间")
    sign_out_time = models.DateTimeField(null=True, blank=True, help_text="签退时间")
    status = models.CharField(
        max_length=32, default="normal", help_text="状态：normal/late/leave"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        unique_together = ["user", "date"]

    def __str__(self):
        return f"{self.user}:{self.date}"

