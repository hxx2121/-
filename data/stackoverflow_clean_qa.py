import argparse
import json
import os
import re
import sqlite3
from dataclasses import dataclass
from glob import glob
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple
 
try:
    import pyarrow.parquet as pq
except ImportError as e:
    raise SystemExit(
        "本脚本依赖 pyarrow，请先安装：\n"
        "  pip install pyarrow\n"
        f"原始错误：{e}"
    )
 
 
_FENCED_CODE_RE = re.compile(r"```[^\n]*\n([\s\S]*?)\n```", re.MULTILINE)
 
 
def _normalize_tags(tags: object) -> List[str]:
    if tags is None:
        return []
    if isinstance(tags, list):
        out = []
        for t in tags:
            s = str(t or "").strip().lower()
            if s:
                out.append(s)
        return out
    if isinstance(tags, str):
        s = tags.strip()
        if not s:
            return []
        if "<" in s and ">" in s:
            parts = re.findall(r"<([^>]+)>", s)
            return [p.strip().lower() for p in parts if p.strip()]
        return [p.strip().lower() for p in re.split(r"[,\s]+", s) if p.strip()]
    return [str(tags).strip().lower()] if str(tags).strip() else []
 
 
def _extract_fenced_code_blocks(markdown: str) -> List[str]:
    if not markdown:
        return []
    blocks = []
    for m in _FENCED_CODE_RE.finditer(markdown):
        code = (m.group(1) or "").rstrip()
        if code:
            blocks.append(code)
    return blocks
 
 
def _extract_indented_code_blocks(markdown: str) -> List[str]:
    if not markdown:
        return []
    lines = markdown.splitlines()
    blocks: List[str] = []
    buf: List[str] = []
    for line in lines + [""]:
        is_code = line.startswith("    ") or line.startswith("\t")
        if is_code:
            buf.append(line[4:] if line.startswith("    ") else line[1:])
            continue
        if buf:
            if len(buf) >= 2:
                blocks.append("\n".join(buf).rstrip())
            buf = []
    return [b for b in blocks if b]
 
 
def extract_code_snippets(markdown: str, *, min_chars: int = 12, max_snippets: int = 20) -> List[str]:
    snippets: List[str] = []
    for b in _extract_fenced_code_blocks(markdown) + _extract_indented_code_blocks(markdown):
        s = (b or "").strip("\n")
        if len(s) < min_chars:
            continue
        snippets.append(s)
        if len(snippets) >= max_snippets:
            break
    seen = set()
    deduped: List[str] = []
    for s in snippets:
        key = s.strip()
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(s)
    return deduped
 
 
def strip_code_from_markdown(markdown: str) -> str:
    if not markdown:
        return ""
    s = _FENCED_CODE_RE.sub("\n", markdown)
    lines = s.splitlines()
    out_lines: List[str] = []
    for line in lines:
        if line.startswith("    ") or line.startswith("\t"):
            continue
        out_lines.append(line)
    s2 = "\n".join(out_lines)
    s2 = re.sub(r"`[^`]+`", " ", s2)
    s2 = re.sub(r"\s+", " ", s2).strip()
    return s2
 
 
def iter_parquet_rows(paths: Sequence[str], *, columns: Sequence[str], batch_size: int) -> Iterator[dict]:
    for path in paths:
        pf = pq.ParquetFile(path)
        for batch in pf.iter_batches(batch_size=batch_size, columns=list(columns)):
            d = batch.to_pydict()
            n = len(batch)
            for i in range(n):
                row = {}
                for c in columns:
                    if c in d:
                        row[c] = d[c][i]
                    else:
                        row[c] = None
                yield row
 
 
class _Deduper:
    def seen_post_id(self, post_id: int) -> bool:
        raise NotImplementedError
 
    def seen_pair(self, qid: int, aid: int) -> bool:
        raise NotImplementedError
 
    def close(self) -> None:
        return None
 
 
class _MemoryDeduper(_Deduper):
    def __init__(self) -> None:
        self._post_ids: set[int] = set()
        self._pairs: set[Tuple[int, int]] = set()
 
    def seen_post_id(self, post_id: int) -> bool:
        if post_id in self._post_ids:
            return True
        self._post_ids.add(post_id)
        return False
 
    def seen_pair(self, qid: int, aid: int) -> bool:
        k = (qid, aid)
        if k in self._pairs:
            return True
        self._pairs.add(k)
        return False
 
 
class _SqliteDeduper(_Deduper):
    def __init__(self, db_path: str) -> None:
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._conn.execute("CREATE TABLE IF NOT EXISTS seen_posts (id INTEGER PRIMARY KEY);")
        self._conn.execute("CREATE TABLE IF NOT EXISTS seen_pairs (qid INTEGER NOT NULL, aid INTEGER NOT NULL, PRIMARY KEY (qid, aid));")
        self._conn.commit()
 
    def seen_post_id(self, post_id: int) -> bool:
        cur = self._conn.execute("INSERT OR IGNORE INTO seen_posts (id) VALUES (?);", (int(post_id),))
        return cur.rowcount == 0
 
    def seen_pair(self, qid: int, aid: int) -> bool:
        cur = self._conn.execute(
            "INSERT OR IGNORE INTO seen_pairs (qid, aid) VALUES (?, ?);",
            (int(qid), int(aid)),
        )
        return cur.rowcount == 0
 
    def close(self) -> None:
        try:
            self._conn.commit()
        finally:
            self._conn.close()
 
 
@dataclass(frozen=True)
class Question:
    id: int
    title: str
    body: str
    tags: List[str]
    score: int
    view_count: Optional[int]
    creation_date: Optional[str]
    accepted_answer_id: Optional[int]
    code_snippets: List[str]
    text: str
 
 
@dataclass(frozen=True)
class Answer:
    id: int
    parent_id: int
    body: str
    score: int
    creation_date: Optional[str]
    code_snippets: List[str]
    text: str
 
 
def _tags_match(tags: List[str], include_any: List[str], exclude_any: List[str]) -> bool:
    if not tags:
        return False if include_any else True
    ts = set(tags)
    if exclude_any and (ts & set(exclude_any)):
        return False
    if include_any:
        return bool(ts & set(include_any))
    return True
 
 
def _parse_int(v: object) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(v)
    except Exception:
        return None
 
 
def _build_deduper(dedup_db: Optional[str]) -> _Deduper:
    if dedup_db:
        return _SqliteDeduper(dedup_db)
    return _MemoryDeduper()
 
 
def main() -> None:
    base_dir = os.path.dirname(__file__)
 
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-glob", default=os.path.join(base_dir, "stackoverflow-posts-*.parquet"))
    parser.add_argument("--output", default=os.path.join(base_dir, "stackoverflow-python-qa-cleaned.jsonl"))
    parser.add_argument("--include-tag", action="append", default=["python"])
    parser.add_argument("--exclude-tag", action="append", default=[])
    parser.add_argument("--min-question-score", type=int, default=1)
    parser.add_argument("--min-answer-score", type=int, default=1)
    parser.add_argument("--min-body-chars", type=int, default=80)
    parser.add_argument("--max-body-chars", type=int, default=12000)
    parser.add_argument("--min-text-chars", type=int, default=40)
    parser.add_argument("--require-code", choices=["question", "answer", "either", "none"], default="either")
    parser.add_argument("--min-code-chars", type=int, default=12)
    parser.add_argument("--max-code-snippets", type=int, default=20)
    parser.add_argument("--answer-policy", choices=["best", "all"], default="best")
    parser.add_argument("--max-pairs", type=int, default=10000)
    parser.add_argument("--batch-size", type=int, default=8192)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--dedup-db", default="")
    args = parser.parse_args()
 
    files = sorted(glob(args.input_glob))
    if not files:
        raise SystemExit(f"未找到任何 parquet 文件，检查路径是否正确：{args.input_glob}")
 
    include_any = [str(x or "").strip().lower() for x in (args.include_tag or []) if str(x or "").strip()]
    exclude_any = [str(x or "").strip().lower() for x in (args.exclude_tag or []) if str(x or "").strip()]
 
    columns = [
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
    ]
 
    deduper = _build_deduper(args.dedup_db.strip() or None)
    try:
        questions: Dict[int, Question] = {}
 
        scanned = 0
        kept_questions = 0
        for row in iter_parquet_rows(files, columns=columns, batch_size=int(args.batch_size)):
            scanned += 1
            if args.limit and scanned > int(args.limit):
                break
 
            if int(row.get("PostTypeId") or 0) != 1:
                continue

            post_id = _parse_int(row.get("Id"))
            if post_id is None:
                continue
            if deduper.seen_post_id(post_id):
                continue
 
            title = str(row.get("Title") or "").strip()
            body = str(row.get("Body") or "").strip()
            if not title or not body:
                continue
            if len(body) < int(args.min_body_chars) or len(body) > int(args.max_body_chars):
                continue
 
            tags = _normalize_tags(row.get("Tags"))
            if not _tags_match(tags, include_any=include_any, exclude_any=exclude_any):
                continue
 
            score = int(row.get("Score") or 0)
            if score < int(args.min_question_score):
                continue
 
            code_snippets = extract_code_snippets(
                body,
                min_chars=int(args.min_code_chars),
                max_snippets=int(args.max_code_snippets),
            )
            text = strip_code_from_markdown(body)
            if len(text) < int(args.min_text_chars):
                continue
            if args.require_code == "question" and not code_snippets:
                continue
 
            accepted_answer_id = _parse_int(row.get("AcceptedAnswerId"))
            view_count = _parse_int(row.get("ViewCount"))
            creation_date = str(row.get("CreationDate") or "").strip() or None
 
            questions[post_id] = Question(
                id=post_id,
                title=title,
                body=body,
                tags=tags,
                score=score,
                view_count=view_count,
                creation_date=creation_date,
                accepted_answer_id=accepted_answer_id,
                code_snippets=code_snippets,
                text=text,
            )
            kept_questions += 1
 
        scanned2 = 0
        kept_answers = 0
        accepted_hits = 0
        best_by_qid: Dict[int, Answer] = {}
        accepted_by_qid: Dict[int, Answer] = {}
        all_by_qid: Dict[int, List[Answer]] = {}
 
        for row in iter_parquet_rows(files, columns=columns, batch_size=int(args.batch_size)):
            scanned2 += 1
            if args.limit and scanned2 > int(args.limit):
                break
 
            if int(row.get("PostTypeId") or 0) != 2:
                continue
            parent_id = _parse_int(row.get("ParentId"))
            if parent_id is None or parent_id not in questions:
                continue
 
            aid = _parse_int(row.get("Id"))
            if aid is None:
                continue
            if deduper.seen_post_id(aid):
                continue
 
            body = str(row.get("Body") or "").strip()
            if not body:
                continue
            if len(body) < int(args.min_body_chars) or len(body) > int(args.max_body_chars):
                continue
 
            score = int(row.get("Score") or 0)
            if score < int(args.min_answer_score):
                continue
 
            code_snippets = extract_code_snippets(
                body,
                min_chars=int(args.min_code_chars),
                max_snippets=int(args.max_code_snippets),
            )
            text = strip_code_from_markdown(body)
            if len(text) < int(args.min_text_chars):
                continue
            if args.require_code == "answer" and not code_snippets:
                continue
 
            creation_date = str(row.get("CreationDate") or "").strip() or None
            ans = Answer(
                id=aid,
                parent_id=parent_id,
                body=body,
                score=score,
                creation_date=creation_date,
                code_snippets=code_snippets,
                text=text,
            )
 
            kept_answers += 1
            q = questions[parent_id]
            if q.accepted_answer_id is not None and int(q.accepted_answer_id) == int(aid):
                accepted_by_qid[parent_id] = ans
                accepted_hits += 1
 
            if args.answer_policy == "all":
                all_by_qid.setdefault(parent_id, []).append(ans)
            else:
                cur = best_by_qid.get(parent_id)
                if cur is None or ans.score > cur.score:
                    best_by_qid[parent_id] = ans
 
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
 
        written = 0
        max_pairs = int(args.max_pairs or 0)
        with open(args.output, "w", encoding="utf-8") as f:
            for qid, q in questions.items():
                selected: List[Answer] = []
                if args.answer_policy == "all":
                    selected = all_by_qid.get(qid, [])
                else:
                    selected = []
                    a = accepted_by_qid.get(qid) or best_by_qid.get(qid)
                    if a is not None:
                        selected = [a]
 
                if not selected:
                    continue
 
                for a in selected:
                    if deduper.seen_pair(qid, a.id):
                        continue
 
                    if args.require_code == "either":
                        if not q.code_snippets and not a.code_snippets:
                            continue
 
                    rec = {
                        "question_id": q.id,
                        "answer_id": a.id,
                        "title": q.title,
                        "question_body": q.body,
                        "answer_body": a.body,
                        "tags": q.tags,
                        "question_score": q.score,
                        "answer_score": a.score,
                        "view_count": q.view_count,
                        "question_creation_date": q.creation_date,
                        "answer_creation_date": a.creation_date,
                        "question_code_snippets": q.code_snippets,
                        "answer_code_snippets": a.code_snippets,
                    }
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    written += 1
                    if max_pairs and written >= max_pairs:
                        break
                if max_pairs and written >= max_pairs:
                    break
 
        print(
            json.dumps(
                {
                    "files": len(files),
                    "scanned_pass1": scanned,
                    "kept_questions": kept_questions,
                    "scanned_pass2": scanned2,
                    "kept_answers": kept_answers,
                    "accepted_answer_hits": accepted_hits,
                    "written_pairs": written,
                    "max_pairs": max_pairs,
                    "output": os.path.abspath(args.output),
                },
                ensure_ascii=False,
            )
        )
    finally:
        deduper.close()
 
 
if __name__ == "__main__":
    main()
