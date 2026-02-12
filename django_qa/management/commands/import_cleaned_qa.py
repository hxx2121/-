from __future__ import annotations

import json
from datetime import datetime, timezone

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.dateparse import parse_datetime

from django_qa.models import ProgrammingQAPair


def _parse_dt(value: object) -> datetime | None:
    if not value:
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return None
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = parse_datetime(s)
        if dt is None:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt
    return None


class Command(BaseCommand):
    help = "导入清洗后的 StackOverflow 问答数据到数据库"

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="data/stackoverflow-python-qa-cleaned.jsonl",
            help="清洗后的 jsonl 文件路径",
        )
        parser.add_argument("--limit", type=int, default=0, help="最多导入多少条，0 表示全部")
        parser.add_argument("--batch-size", type=int, default=1000, help="批量写入大小")
        parser.add_argument("--truncate", action="store_true", help="导入前清空表")

    def handle(self, *args, **options):
        path: str = options["path"]
        limit: int = int(options["limit"] or 0)
        batch_size: int = int(options["batch_size"] or 1000)
        truncate: bool = bool(options["truncate"])

        if truncate:
            ProgrammingQAPair.objects.all().delete()

        before = ProgrammingQAPair.objects.count()
        created = 0
        seen = 0
        buf: list[ProgrammingQAPair] = []

        def flush():
            nonlocal created, buf
            if not buf:
                return
            with transaction.atomic():
                ProgrammingQAPair.objects.bulk_create(buf, ignore_conflicts=True, batch_size=batch_size)
            created = ProgrammingQAPair.objects.count() - before
            buf = []

        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                qa = ProgrammingQAPair(
                    question_id=int(obj.get("question_id") or 0),
                    answer_id=int(obj.get("answer_id") or 0),
                    title=str(obj.get("title") or ""),
                    question_body=str(obj.get("question_body") or ""),
                    answer_body=str(obj.get("answer_body") or ""),
                    tags_json=list(obj.get("tags") or []),
                    question_score=int(obj.get("question_score") or 0),
                    answer_score=int(obj.get("answer_score") or 0),
                    view_count=(int(obj.get("view_count")) if obj.get("view_count") is not None else None),
                    question_creation_date=_parse_dt(obj.get("question_creation_date")),
                    answer_creation_date=_parse_dt(obj.get("answer_creation_date")),
                    question_code_snippets_json=list(obj.get("question_code_snippets") or []),
                    answer_code_snippets_json=list(obj.get("answer_code_snippets") or []),
                )
                buf.append(qa)
                seen += 1
                if len(buf) >= batch_size:
                    flush()
                    self.stdout.write(f"已处理 {seen} 条，当前表内 {ProgrammingQAPair.objects.count()} 条")
                if limit and seen >= limit:
                    break

        flush()
        after = ProgrammingQAPair.objects.count()
        self.stdout.write(self.style.SUCCESS(f"导入完成：新增 {after - before} 条，当前总计 {after} 条"))

