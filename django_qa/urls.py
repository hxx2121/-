from django.urls import path

from django_qa.views import (
    AdminAnswerMetricsView,
    AdminPromptDetailView,
    AdminPromptListCreateView,
    DatasetPairDetailView,
    DatasetPairsView,
    DatasetSummaryView,
    MessageListCreateView,
    QAView,
    ThreadDeleteView,
    ThreadListCreateView,
)

urlpatterns = [
    path("qa/", QAView.as_view()),
    path("threads/", ThreadListCreateView.as_view()),
    path("threads/<int:thread_id>/", ThreadDeleteView.as_view()),
    path("threads/<int:thread_id>/messages/", MessageListCreateView.as_view()),
    path("dataset/summary/", DatasetSummaryView.as_view()),
    path("dataset/pairs/", DatasetPairsView.as_view()),
    path("dataset/pairs/<int:pair_id>/", DatasetPairDetailView.as_view()),
    path("admin/prompts/", AdminPromptListCreateView.as_view()),
    path("admin/prompts/<int:prompt_id>/", AdminPromptDetailView.as_view()),
    path("admin/answer-metrics/", AdminAnswerMetricsView.as_view()),
]
