import json
import os
from glob import glob
from typing import Iterable, List, Optional

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError as e:
    raise SystemExit(
        "本脚本依赖 pyarrow，请先安装：\n"
        "  pip install pyarrow\n"
        f"原始错误：{e}"
    )


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INPUT_GLOB = os.path.join(DATA_DIR, "stackoverflow-posts-*.parquet")
OUTPUT_PATH = os.path.join(DATA_DIR, "stackoverflow-python-questions.jsonl")


PY_TAGS = {
    "python",
    "python-2.7",
    "python-3.x",
    "pandas",
    "django",
    "flask",
    "numpy",
    "scipy",
    "tensorflow",
    "pytorch",
}


def is_python_tags(tags: Optional[List[str]]) -> bool:
    if not tags:
        return False
    lowered = {str(t or "").strip().lower() for t in tags}
    if lowered & PY_TAGS:
        return True
    for t in lowered:
        if t.startswith("python-") or t.endswith("-python"):
            return True
    return False


def has_code(body: str) -> bool:
    text = (body or "").lower()
    if "```" in text or "\n    " in text:
        return True
    if "def " in text or "class " in text:
        return True
    if "import " in text:
        return True
    return False


def iter_parquet_rows(path: str) -> Iterable[dict]:
    table = pq.read_table(
        path,
        columns=[
            "Id",
            "PostTypeId",
            "AcceptedAnswerId",
            "ParentId",
            "Score",
            "ViewCount",
            "Body",
            "Title",
            "Tags",
            "CreationDate",
        ],
    )
    for batch in table.to_batches():
        batch_dict = batch.to_pydict()
        rows = len(batch)
        for i in range(rows):
            yield {
                "Id": batch_dict["Id"][i],
                "PostTypeId": batch_dict["PostTypeId"][i],
                "AcceptedAnswerId": batch_dict.get("AcceptedAnswerId", [None])[i],
                "ParentId": batch_dict.get("ParentId", [None])[i],
                "Score": batch_dict.get("Score", [0])[i],
                "ViewCount": batch_dict.get("ViewCount", [None])[i],
                "Body": batch_dict.get("Body", [None])[i],
                "Title": batch_dict.get("Title", [None])[i],
                "Tags": batch_dict.get("Tags", [None])[i],
                "CreationDate": batch_dict.get("CreationDate", [None])[i],
            }


def clean_stackoverflow_python():
    files = sorted(glob(INPUT_GLOB))
    if not files:
        raise SystemExit(f"未找到任何 parquet 文件，检查路径是否正确：{INPUT_GLOB}")

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    kept = 0
    total = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8") as out_f:
        for path in files:
            for row in iter_parquet_rows(path):
                total += 1
                if int(row["PostTypeId"] or 0) != 1:
                    continue
                body = row.get("Body") or ""
                title = row.get("Title") or ""
                tags = row.get("Tags") or []

                if not title or not body:
                    continue
                if not is_python_tags(tags):
                    continue
                if not has_code(body):
                    continue

                if len(body) < 80 or len(body) > 8000:
                    continue

                item = {
                    "id": int(row["Id"]),
                    "title": title,
                    "body": body,
                    "tags": tags,
                    "score": int(row.get("Score") or 0),
                    "view_count": int(row.get("ViewCount") or 0) if row.get("ViewCount") is not None else None,
                    "creation_date": row.get("CreationDate"),
                }
                out_f.write(json.dumps(item, ensure_ascii=False) + "\n")
                kept += 1

    print(f"总计扫描 {total} 条帖子，保留 {kept} 条 Python 相关问答（写入 {OUTPUT_PATH}）。")


if __name__ == "__main__":
    clean_stackoverflow_python()

