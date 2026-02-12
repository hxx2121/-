from __future__ import annotations

from datetime import timedelta
import time

from django.db.models import Avg, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.request import Request

from django_auth.utils.decorators import admin_required, login_required
from django_main.R import R
from django_qa.models import (
    AnswerEvaluation,
    ConversationMessage,
    ConversationThread,
    ProgrammingQAPair,
    PromptTemplate,
)
from django_qa.serializers import (
    AnswerMetricsSerializer,
    DatasetPairSerializer,
    DatasetPairDetailSerializer,
    MessageCreateSerializer,
    MessageListSerializer,
    PromptCreateSerializer,
    PromptTemplateListSerializer,
    PromptUpdateSerializer,
    QARequestSerializer,
    ThreadCreateSerializer,
    ThreadListSerializer,
)
from django_qa.utils.code_analysis import analyze_code_comprehensive
from django_qa.utils.llm import LLMMessage, chat
from django_qa.utils.prompt import render_template
from django_qa.utils.qa_match import get_default_matcher


def _get_prompt(scene: str | None) -> PromptTemplate | None:
    qs = PromptTemplate.objects.filter(is_active=True)
    if scene:
        qs = qs.filter(scene=scene)
    prompt = qs.order_by("-updated_at", "-id").first()
    return prompt


def _build_context_text(messages: list[ConversationMessage], max_chars: int = 8000) -> str:
    parts: list[str] = []
    for m in messages:
        role = (m.role or "").strip()
        content = (m.content or "").strip()
        if not content:
            continue
        parts.append(f"{role}: {content}")
    text = "\n\n".join(parts).strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


def _build_retrieval_context(recommendations: list[dict], *, max_chars: int = 4500) -> str:
    parts: list[str] = []
    for i, rec in enumerate(recommendations[:3], start=1):
        title = str(rec.get("title") or "").strip()
        ans = str(rec.get("answer_excerpt") or "").strip()
        sim = rec.get("similarity")
        qid = rec.get("question_id")
        aid = rec.get("answer_id")
        header = f"[候选{i}] qid={qid} aid={aid} sim={sim:.4f}" if isinstance(sim, (int, float)) else f"[候选{i}] qid={qid} aid={aid}"
        if title:
            parts.append(f"{header}\n标题：{title}\n参考答案要点：{ans}".strip())
        else:
            parts.append(f"{header}\n参考答案要点：{ans}".strip())
    text = "\n\n".join([p for p in parts if p]).strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


class QAView(GenericAPIView):
    @login_required
    def post(self, request: Request):
        ser = QARequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        question = ser.validated_data["question"]
        scene = ser.validated_data.get("prompt_scene") or "cot_programming"
        prompt = _get_prompt(scene) or _get_prompt(None)

        system_prompt = prompt.system_prompt if prompt else ""
        user_prompt = (
            render_template(
                prompt.user_prompt_template,
                {"question": question, "context": ""},
            )
            if prompt
            else question
        )
        try:
            answer = chat(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_prompt),
                ]
            )
        except Exception as e:
            return R.fail(
                msg="模型调用失败，请检查后端模型配置与 API_KEY",
                code=50201,
                data={"error_type": type(e).__name__},
                http_status=status.HTTP_502_BAD_GATEWAY,
            )

        analysis = analyze_code_comprehensive(answer)
        evaluation = {
            "syntax_score": analysis["syntax_score"],
            "logic_score": analysis["logic_score"],
            "utility_score": analysis["utility_score"],
            "readability_score": analysis["readability_score"],
            "total_score": analysis["total_score"],
            "analysis_report": analysis["report"],
        }
        return R.ok(data={"answer": answer, "evaluation": evaluation})


class ThreadListCreateView(GenericAPIView):
    @login_required
    def get(self, request: Request):
        rows = ConversationThread.objects.filter(owner=request.user).order_by("-updated_at", "-id")
        return R.ok(data=ThreadListSerializer(rows, many=True).data)

    @login_required
    def post(self, request: Request):
        ser = ThreadCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        title = ser.validated_data.get("title") or ""
        row = ConversationThread.objects.create(owner=request.user, title=title)
        return R.ok(data=ThreadListSerializer(row).data)


class ThreadDeleteView(GenericAPIView):
    @login_required
    def delete(self, request: Request, thread_id: int):
        row = ConversationThread.objects.filter(id=thread_id).first()
        if row is None:
            return R.fail(msg="会话不存在", http_status=status.HTTP_404_NOT_FOUND)
        if row.owner_id != request.user.id and not (request.user.is_staff or request.user.is_superuser):
            return R.forbidden(msg="无权删除该会话")
        row.delete()
        return R.ok(data=True)


class MessageListCreateView(GenericAPIView):
    @login_required
    def get(self, request: Request, thread_id: int):
        thread = ConversationThread.objects.filter(id=thread_id, owner=request.user).first()
        if thread is None:
            return R.fail(msg="会话不存在", http_status=status.HTTP_404_NOT_FOUND)
        rows = ConversationMessage.objects.filter(thread=thread).order_by("id")
        return R.ok(data=MessageListSerializer(rows, many=True).data)

    @login_required
    def post(self, request: Request, thread_id: int):
        thread = ConversationThread.objects.filter(id=thread_id, owner=request.user).first()
        if thread is None:
            return R.fail(msg="会话不存在", http_status=status.HTTP_404_NOT_FOUND)

        ser = MessageCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        content = ser.validated_data["content"]
        scene = ser.validated_data.get("prompt_scene") or "cot_programming"

        user_msg = ConversationMessage.objects.create(
            thread=thread,
            role="user",
            content=content,
            citations_json=[],
            tool_events_json=[],
        )

        recent = list(ConversationMessage.objects.filter(thread=thread).order_by("-id")[:12])
        recent.reverse()
        context_text = _build_context_text(recent[:-1])
        prompt = _get_prompt(scene) or _get_prompt(None)

        tool_events: list[dict] = []
        citations: list[dict] = []
        retrieval_context = ""
        try:
            t0 = time.perf_counter()
            matcher = get_default_matcher()
            retrieval = matcher.match_and_recommend(content, top_k_match=8, top_k_recommend=3)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)
            tool_events.append(
                {
                    "name": "qa_match_and_recommend",
                    "payload": {"question": content, "top_k_match": 8, "top_k_recommend": 3},
                    "elapsed_ms": elapsed_ms,
                    "tool_out": {"ok": True, "result": retrieval, "error": None, "meta": {"tool": "qa_match_and_recommend"}},
                }
            )
            citations = [
                {"type": "match", **m} for m in (retrieval.get("matches") or [])[:8]
            ] + [
                {"type": "recommendation", **r} for r in (retrieval.get("recommendations") or [])[:3]
            ]
            retrieval_context = _build_retrieval_context(list(retrieval.get("recommendations") or []))
        except Exception as e:
            tool_events.append(
                {
                    "name": "qa_match_and_recommend",
                    "payload": {"question": content, "top_k_match": 8, "top_k_recommend": 3},
                    "elapsed_ms": 0,
                    "tool_out": {
                        "ok": False,
                        "result": {"matches": [], "recommendations": []},
                        "error": str(e),
                        "meta": {"tool": "qa_match_and_recommend"},
                    },
                }
            )

        system_prompt = prompt.system_prompt if prompt else ""
        merged_context = context_text
        if retrieval_context:
            merged_context = (merged_context + "\n\n" if merged_context else "") + "相似问答检索结果（供参考，优先保证答案正确性）：\n" + retrieval_context
        user_prompt = (
            render_template(
                prompt.user_prompt_template,
                {"question": content, "context": merged_context},
            )
            if prompt
            else content
        )

        try:
            answer_text = chat(
                [
                    LLMMessage(role="system", content=system_prompt),
                    LLMMessage(role="user", content=user_prompt),
                ]
            )
        except Exception as e:
            return R.fail(
                msg="模型调用失败，请检查后端模型配置与 API_KEY",
                code=50201,
                data={"error_type": type(e).__name__},
                http_status=status.HTTP_502_BAD_GATEWAY,
            )

        assistant_msg = ConversationMessage.objects.create(
            thread=thread,
            role="assistant",
            content=answer_text,
            citations_json=citations,
            tool_events_json=tool_events,
        )

        analysis = analyze_code_comprehensive(answer_text)
        AnswerEvaluation.objects.create(
            message=assistant_msg,
            syntax_score=analysis["syntax_score"],
            logic_score=analysis["logic_score"],
            utility_score=analysis["utility_score"],
            readability_score=analysis["readability_score"],
            total_score=analysis["total_score"],
            analysis_report=analysis["report"],
        )

        thread.updated_at = timezone.now()
        if not thread.title:
            thread.title = (content or "")[:40]
        thread.save(update_fields=["updated_at", "title"])

        return R.ok(
            data={
                "user": MessageListSerializer(user_msg).data,
                "assistant": MessageListSerializer(assistant_msg).data,
            }
        )


class AdminPromptListCreateView(GenericAPIView):
    @admin_required
    def get(self, request: Request):
        rows = PromptTemplate.objects.all().order_by("-updated_at", "-id")
        return R.ok(data=PromptTemplateListSerializer(rows, many=True).data)

    @admin_required
    def post(self, request: Request):
        ser = PromptCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        row = PromptTemplate.objects.create(**ser.validated_data)
        return R.ok(data=PromptTemplateListSerializer(row).data)


class AdminPromptDetailView(GenericAPIView):
    @admin_required
    def patch(self, request: Request, prompt_id: int):
        row = PromptTemplate.objects.filter(id=prompt_id).first()
        if row is None:
            return R.fail(msg="提示词模板不存在", http_status=status.HTTP_404_NOT_FOUND)
        ser = PromptUpdateSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        for k, v in ser.validated_data.items():
            setattr(row, k, v)
        row.save()
        return R.ok(data=PromptTemplateListSerializer(row).data)

    @admin_required
    def delete(self, request: Request, prompt_id: int):
        row = PromptTemplate.objects.filter(id=prompt_id).first()
        if row is None:
            return R.fail(msg="提示词模板不存在", http_status=status.HTTP_404_NOT_FOUND)
        row.delete()
        return R.ok(data=True)


class AdminAnswerMetricsView(GenericAPIView):
    @admin_required
    def get(self, request: Request):
        qs = AnswerEvaluation.objects.all()
        avg = qs.aggregate(
            syntax=Avg("syntax_score"),
            logic=Avg("logic_score"),
            utility=Avg("utility_score"),
            readability=Avg("readability_score"),
            total=Avg("total_score"),
        )
        avg_scores = {k: float(avg.get(k) or 0.0) for k in ["syntax", "logic", "utility", "readability", "total"]}

        low = qs.filter(total_score__lt=4).count()
        medium = qs.filter(total_score__gte=4, total_score__lt=6).count()
        good = qs.filter(total_score__gte=6, total_score__lt=8).count()
        excellent = qs.filter(total_score__gte=8).count()
        quality_distribution = {"low": low, "medium": medium, "good": good, "excellent": excellent}

        start = timezone.now().date() - timedelta(days=6)
        daily_qs = (
            qs.filter(created_at__date__gte=start)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        daily_activity = [{"date": str(row["date"]), "count": int(row["count"])} for row in daily_qs]

        data = {"avg_scores": avg_scores, "quality_distribution": quality_distribution, "daily_activity": daily_activity}
        out = AnswerMetricsSerializer(data=data)
        out.is_valid(raise_exception=True)
        return R.ok(data=out.data)


class DatasetSummaryView(GenericAPIView):
    @login_required
    def get(self, request: Request):
        total = ProgrammingQAPair.objects.count()
        top_pairs = ProgrammingQAPair.objects.order_by("-answer_score", "-id")[:8]
        tags_counter: dict[str, int] = {}
        for tags in ProgrammingQAPair.objects.values_list("tags_json", flat=True):
            if not tags:
                continue
            for t in tags:
                key = str(t or "").strip()
                if not key:
                    continue
                tags_counter[key] = tags_counter.get(key, 0) + 1
        top_tags = sorted(
            [{"tag": k, "count": v} for k, v in tags_counter.items()],
            key=lambda x: int(x["count"]),
            reverse=True,
        )[:20]
        data = {
            "total": int(total),
            "top_tags": top_tags,
            "top_pairs": DatasetPairSerializer(top_pairs, many=True).data,
        }
        return R.ok(data=data)


class DatasetPairsView(GenericAPIView):
    @login_required
    def get(self, request: Request):
        q = (request.query_params.get("q") or "").strip()
        tag = (request.query_params.get("tag") or "").strip()
        sort = (request.query_params.get("sort") or "answer_score").strip()
        page = int(request.query_params.get("page") or 1)
        page_size = int(request.query_params.get("page_size") or 20)
        page = 1 if page < 1 else page
        page_size = 20 if page_size <= 0 else min(page_size, 100)

        qs = ProgrammingQAPair.objects.all()
        if q:
            qs = qs.filter(
                Q(title__icontains=q)
                | Q(question_body__icontains=q)
                | Q(answer_body__icontains=q)
            )
        if tag:
            qs = qs.filter(tags_json__contains=[tag])

        if sort == "recent":
            qs = qs.order_by("-created_at", "-id")
        elif sort == "question_score":
            qs = qs.order_by("-question_score", "-id")
        else:
            qs = qs.order_by("-answer_score", "-id")

        total = qs.count()
        start = (page - 1) * page_size
        rows = qs[start : start + page_size]
        data = {
            "page": page,
            "page_size": page_size,
            "total": int(total),
            "items": DatasetPairSerializer(rows, many=True).data,
        }
        return R.ok(data=data)


class DatasetPairDetailView(GenericAPIView):
    @login_required
    def get(self, request: Request, pair_id: int):
        row = ProgrammingQAPair.objects.filter(id=pair_id).first()
        if row is None:
            return R.fail(msg="数据不存在", http_status=status.HTTP_404_NOT_FOUND)
        return R.ok(data=DatasetPairDetailSerializer(row).data)
