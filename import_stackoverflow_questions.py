import os
import sys
import json
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_main.settings")

import django

django.setup()

from django_qa.models import ProgrammingQuestion


DATA_FILE = BASE_DIR / "data" / "stackoverflow-python-questions.jsonl"


def parse_creation_date(raw: str) -> datetime:
    raw = (raw or "").strip()
    if not raw:
        return datetime(2000, 1, 1, 0, 0, 0)
    try:
        return datetime.fromisoformat(raw)
    except Exception:
        try:
            base = raw.split(".")[0]
            return datetime.strptime(base, "%Y-%m-%dT%H:%M:%S")
        except Exception:
            return datetime(2000, 1, 1, 0, 0, 0)


def main():
    if not DATA_FILE.exists():
        print(f"数据文件不存在: {DATA_FILE}")
        return

    existing_ids = set(ProgrammingQuestion.objects.values_list("question_id", flat=True))
    print(f"当前库中已有 {len(existing_ids)} 条 ProgrammingQuestion 记录")

    batch_size = 1000
    batch = []
    total_read = 0
    total_insert = 0

    with DATA_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total_read += 1
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            qid = obj.get("id")
            if qid is None or qid in existing_ids:
                continue

            pq = ProgrammingQuestion(
                question_id=int(qid),
                title=str(obj.get("title") or ""),
                body=str(obj.get("body") or ""),
                tags_json=list(obj.get("tags") or []),
                score=int(obj.get("score") or 0),
                view_count=int(obj.get("view_count") or 0),
                creation_date=parse_creation_date(str(obj.get("creation_date") or "")),
            )
            batch.append(pq)
            existing_ids.add(int(qid))

            if len(batch) >= batch_size:
                ProgrammingQuestion.objects.bulk_create(batch, ignore_conflicts=True)
                total_insert += len(batch)
                print(f"已写入 {total_insert} 条记录（读取 {total_read} 行）")
                batch.clear()

    if batch:
        ProgrammingQuestion.objects.bulk_create(batch, ignore_conflicts=True)
        total_insert += len(batch)

    print(f"导入完成：读取 {total_read} 行，新增 {total_insert} 条 ProgrammingQuestion 记录")


if __name__ == "__main__":
    main()
