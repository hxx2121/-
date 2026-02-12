from __future__ import annotations

from django.conf import settings
from django.db import models


class PromptTemplate(models.Model):
    scene = models.CharField(max_length=64, db_index=True)
    version = models.CharField(max_length=64, default="v1")
    system_prompt = models.TextField(blank=True, default="")
    user_prompt_template = models.TextField(blank=True, default="")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return f"PromptTemplate(id={self.id}, scene={self.scene}, version={self.version}, active={self.is_active})"


class ProgrammingQuestion(models.Model):
    question_id = models.BigIntegerField(unique=True, db_index=True)
    title = models.TextField(blank=True, default="")
    body = models.TextField(blank=True, default="")
    tags_json = models.JSONField(default=list, blank=True)
    score = models.IntegerField(default=0, db_index=True)
    view_count = models.IntegerField(default=0)
    creation_date = models.DateTimeField(db_index=True)

    class Meta:
        ordering = ["-score", "-question_id"]

    def __str__(self) -> str:
        return f"ProgrammingQuestion(question_id={self.question_id}, score={self.score})"


class ConversationThread(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="qa_threads"
    )
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return f"ConversationThread(id={self.id}, owner_id={self.owner_id})"


class ConversationMessage(models.Model):
    thread = models.ForeignKey(
        ConversationThread, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=16, db_index=True)
    content = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    citations_json = models.JSONField(default=list, blank=True)
    tool_events_json = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return f"ConversationMessage(id={self.id}, thread_id={self.thread_id}, role={self.role})"


class AnswerEvaluation(models.Model):
    message = models.OneToOneField(
        ConversationMessage, on_delete=models.CASCADE, related_name="evaluation"
    )
    syntax_score = models.FloatField(default=0)
    logic_score = models.FloatField(default=0)
    utility_score = models.FloatField(default=0)
    readability_score = models.FloatField(default=0)
    total_score = models.FloatField(default=0, db_index=True)
    analysis_report = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"AnswerEvaluation(id={self.id}, message_id={self.message_id}, total={self.total_score})"


class ProgrammingQAPair(models.Model):
    question_id = models.BigIntegerField(db_index=True)
    answer_id = models.BigIntegerField(db_index=True)
    title = models.TextField(blank=True, default="")
    question_body = models.TextField(blank=True, default="")
    answer_body = models.TextField(blank=True, default="")
    tags_json = models.JSONField(default=list, blank=True)
    question_score = models.IntegerField(default=0, db_index=True)
    answer_score = models.IntegerField(default=0, db_index=True)
    view_count = models.IntegerField(null=True, blank=True)
    question_creation_date = models.DateTimeField(null=True, blank=True, db_index=True)
    answer_creation_date = models.DateTimeField(null=True, blank=True, db_index=True)
    question_code_snippets_json = models.JSONField(default=list, blank=True)
    answer_code_snippets_json = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-answer_score", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["question_id", "answer_id"], name="uniq_qa_pair_question_answer"),
        ]

    def __str__(self) -> str:
        return f"ProgrammingQAPair(qid={self.question_id}, aid={self.answer_id})"
