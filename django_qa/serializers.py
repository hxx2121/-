from __future__ import annotations

import re

from rest_framework import serializers

from django_qa.models import (
    AnswerEvaluation,
    ConversationMessage,
    ConversationThread,
    ProgrammingQAPair,
    PromptTemplate,
)


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _excerpt(text: str, max_chars: int) -> str:
    s = (text or "").strip()
    s = _HTML_TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


class PromptTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptTemplate
        fields = [
            "id",
            "scene",
            "version",
            "system_prompt",
            "user_prompt_template",
            "is_active",
            "created_at",
            "updated_at",
        ]


class PromptCreateSerializer(serializers.Serializer):
    scene = serializers.CharField(max_length=64)
    version = serializers.CharField(max_length=64, required=False, allow_blank=True, default="v1")
    system_prompt = serializers.CharField(required=False, allow_blank=True, default="")
    user_prompt_template = serializers.CharField(required=False, allow_blank=True, default="")
    is_active = serializers.BooleanField(required=False, default=True)


class PromptUpdateSerializer(serializers.Serializer):
    scene = serializers.CharField(max_length=64, required=False, allow_blank=True)
    version = serializers.CharField(max_length=64, required=False, allow_blank=True)
    system_prompt = serializers.CharField(required=False, allow_blank=True)
    user_prompt_template = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)


class ThreadListSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationThread
        fields = ["id", "title", "created_at", "updated_at"]


class ThreadCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerEvaluation
        fields = [
            "id",
            "syntax_score",
            "logic_score",
            "utility_score",
            "readability_score",
            "total_score",
            "analysis_report",
            "created_at",
        ]


class MessageListSerializer(serializers.ModelSerializer):
    citations = serializers.SerializerMethodField()
    tool_events = serializers.SerializerMethodField()
    evaluation = EvaluationSerializer(read_only=True)

    class Meta:
        model = ConversationMessage
        fields = ["id", "role", "content", "citations", "tool_events", "evaluation", "created_at"]

    def get_citations(self, obj):
        return obj.citations_json or []

    def get_tool_events(self, obj):
        return obj.tool_events_json or []


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField()
    prompt_scene = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


class QARequestSerializer(serializers.Serializer):
    question = serializers.CharField()
    prompt_scene = serializers.CharField(max_length=64, required=False, allow_blank=True, default="")


class QAResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()
    evaluation = EvaluationSerializer(required=False, allow_null=True)


class AnswerMetricsSerializer(serializers.Serializer):
    avg_scores = serializers.DictField(child=serializers.FloatField())
    quality_distribution = serializers.DictField(child=serializers.IntegerField())
    daily_activity = serializers.ListField(child=serializers.DictField())


class DatasetPairSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()
    question_excerpt = serializers.SerializerMethodField()
    answer_excerpt = serializers.SerializerMethodField()

    class Meta:
        model = ProgrammingQAPair
        fields = [
            "id",
            "question_id",
            "answer_id",
            "title",
            "tags",
            "question_score",
            "answer_score",
            "view_count",
            "question_creation_date",
            "answer_creation_date",
            "question_excerpt",
            "answer_excerpt",
            "created_at",
        ]

    def get_tags(self, obj):
        return obj.tags_json or []

    def get_question_excerpt(self, obj):
        return _excerpt(obj.question_body or "", 240)

    def get_answer_excerpt(self, obj):
        return _excerpt(obj.answer_body or "", 360)


class DatasetPairDetailSerializer(serializers.ModelSerializer):
    tags = serializers.SerializerMethodField()

    class Meta:
        model = ProgrammingQAPair
        fields = [
            "id",
            "question_id",
            "answer_id",
            "title",
            "tags",
            "question_score",
            "answer_score",
            "view_count",
            "question_creation_date",
            "answer_creation_date",
            "question_body",
            "answer_body",
            "question_code_snippets_json",
            "answer_code_snippets_json",
            "created_at",
        ]

    def get_tags(self, obj):
        return obj.tags_json or []
