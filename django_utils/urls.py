from django.urls import path

from django_utils.views import (
    AdminFileDeleteView,
    AdminFileListView,
    FileDeleteView,
    FileDownloadView,
    FileListView,
    FileUploadView,
)

urlpatterns = [
    path("files/upload/", FileUploadView.as_view()),
    path("files/list/", FileListView.as_view()),
    path("files/<int:file_id>/download/", FileDownloadView.as_view()),
    path("files/<int:file_id>/", FileDeleteView.as_view()),
    path("admin/files/list/", AdminFileListView.as_view()),
    path("admin/files/<int:file_id>/", AdminFileDeleteView.as_view()),
]
