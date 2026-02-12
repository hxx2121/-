from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import linear_kernel
except Exception:  # pragma: no cover
    TfidfVectorizer = None  # type: ignore[assignment]
    linear_kernel = None  # type: ignore[assignment]

from django_qa.utils.code_analysis import analyze_code_comprehensive


_CODE_FENCE_RE = re.compile(r"```[^\n]*\n([\s\S]*?)\n```", re.MULTILINE)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_HTML_CODE_RE = re.compile(r"<pre><code>([\s\S]*?)</code></pre>", re.IGNORECASE)


def _strip_html(s: str) -> str:
    if not s:
        return ""
    s = _HTML_CODE_RE.sub(" ", s)
    s = _HTML_TAG_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _strip_code_blocks(s: str) -> str:
    if not s:
        return ""
    s = _CODE_FENCE_RE.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _excerpt(s: str, max_chars: int = 240) -> str:
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1].rstrip() + "…"


def _extract_any_code(text: str, *, max_blocks: int = 3, max_chars: int = 1800) -> str:
    if not text:
        return ""

    blocks: list[str] = []
    for m in _CODE_FENCE_RE.finditer(text):
        code = (m.group(1) or "").strip()
        if code:
            blocks.append(code)
        if len(blocks) >= max_blocks:
            break

    if not blocks:
        for m in _HTML_CODE_RE.finditer(text):
            code = (m.group(1) or "").strip()
            code = _HTML_TAG_RE.sub("", code)
            if code:
                blocks.append(code)
            if len(blocks) >= max_blocks:
                break

    if not blocks:
        return ""

    merged = "\n\n".join(blocks).strip()
    if len(merged) > max_chars:
        merged = merged[:max_chars].rstrip() + "\n"
    return merged


@dataclass(frozen=True)
class QAPair:
    question_id: int
    answer_id: int
    title: str
    question_body: str
    answer_body: str
    tags: list[str]
    question_score: int
    answer_score: int

    @property
    def question_text_for_index(self) -> str:
        raw = f"{self.title}\n{self.question_body}"
        raw = _strip_code_blocks(raw)
        raw = _strip_html(raw)
        return raw


class QAMatcher:
    def __init__(self, *, data_path: Path, cache_dir: Path) -> None:
        self._data_path = data_path
        self._cache_dir = cache_dir
        self._lock = threading.Lock()

        self._pairs: list[QAPair] = []
        self._vectorizer: Any | None = None
        self._matrix: Any | None = None
        self._ready = False

    def ensure_ready(self) -> None:
        if self._ready:
            return
        with self._lock:
            if self._ready:
                return
            self._build_or_load()
            self._ready = True

    def _build_or_load(self) -> None:
        if TfidfVectorizer is None or linear_kernel is None:
            self._pairs = []
            self._vectorizer = None
            self._matrix = None
            return

        if not self._data_path.exists():
            self._pairs = []
            self._vectorizer = None
            self._matrix = None
            return

        os.makedirs(self._cache_dir, exist_ok=True)
        index_path = self._cache_dir / "index.joblib"

        src_mtime = int(self._data_path.stat().st_mtime)
        src_size = int(self._data_path.stat().st_size)
        if index_path.exists():
            try:
                import joblib  # type: ignore

                payload = joblib.load(str(index_path))
                if (
                    isinstance(payload, dict)
                    and payload.get("src_mtime") == src_mtime
                    and payload.get("src_size") == src_size
                    and payload.get("pairs")
                    and payload.get("vectorizer") is not None
                    and payload.get("matrix") is not None
                ):
                    self._pairs = payload["pairs"]
                    self._vectorizer = payload["vectorizer"]
                    self._matrix = payload["matrix"]
                    return
            except Exception:
                pass

        pairs = self._load_pairs()
        texts = [p.question_text_for_index for p in pairs]
        vectorizer = TfidfVectorizer(
            max_features=60000,
            ngram_range=(1, 2),
            stop_words="english",
            lowercase=True,
            min_df=2,
        )
        matrix = vectorizer.fit_transform(texts)

        try:
            import joblib  # type: ignore

            joblib.dump(
                {
                    "src_mtime": src_mtime,
                    "src_size": src_size,
                    "count": len(pairs),
                    "built_at": int(time.time()),
                    "pairs": pairs,
                    "vectorizer": vectorizer,
                    "matrix": matrix,
                },
                str(index_path),
                compress=3,
            )
        except Exception:
            pass

        self._pairs = pairs
        self._vectorizer = vectorizer
        self._matrix = matrix

    def _load_pairs(self, *, limit: int = 15000) -> list[QAPair]:
        out: list[QAPair] = []
        with self._data_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                out.append(
                    QAPair(
                        question_id=int(obj.get("question_id") or 0),
                        answer_id=int(obj.get("answer_id") or 0),
                        title=str(obj.get("title") or ""),
                        question_body=str(obj.get("question_body") or ""),
                        answer_body=str(obj.get("answer_body") or ""),
                        tags=list(obj.get("tags") or []),
                        question_score=int(obj.get("question_score") or 0),
                        answer_score=int(obj.get("answer_score") or 0),
                    )
                )
                if limit and len(out) >= limit:
                    break
        return out

    def match_and_recommend(
        self,
        question: str,
        *,
        top_k_match: int = 8,
        top_k_recommend: int = 3,
    ) -> dict[str, Any]:
        self.ensure_ready()
        if not self._pairs or self._vectorizer is None or self._matrix is None:
            return {"matches": [], "recommendations": []}

        q = _strip_code_blocks(question or "")
        q = _strip_html(q)
        if not q:
            return {"matches": [], "recommendations": []}

        q_vec = self._vectorizer.transform([q])
        scores = linear_kernel(q_vec, self._matrix).ravel()

        top_k_match = max(1, min(int(top_k_match), 30))
        top_k_recommend = max(1, min(int(top_k_recommend), 10))
        best_idx = scores.argsort()[::-1][: max(top_k_match, top_k_recommend * 4)]

        matches: list[dict[str, Any]] = []
        candidates: list[dict[str, Any]] = []
        for idx in best_idx:
            pair = self._pairs[int(idx)]
            sim = float(scores[int(idx)])
            matches.append(
                {
                    "question_id": pair.question_id,
                    "answer_id": pair.answer_id,
                    "title": pair.title,
                    "similarity": sim,
                    "tags": pair.tags[:8],
                    "answer_score": pair.answer_score,
                    "question_excerpt": _excerpt(_strip_html(_strip_code_blocks(pair.question_body)), 220),
                    "answer_excerpt": _excerpt(_strip_html(_strip_code_blocks(pair.answer_body)), 260),
                }
            )
            candidates.append({"pair": pair, "similarity": sim})

        matches = matches[:top_k_match]

        recs: list[dict[str, Any]] = []
        for c in candidates[: top_k_recommend * 4]:
            pair: QAPair = c["pair"]
            sim = float(c["similarity"])
            code = _extract_any_code(pair.answer_body)
            analysis = analyze_code_comprehensive(f"```python\n{code}\n```" if code else "")
            quality = float(analysis.get("total_score") or 0.0) / 10.0
            upvote = float(max(0, pair.answer_score))
            upvote_norm = min(1.0, upvote / 50.0)
            combined = sim * 0.45 + quality * 0.35 + upvote_norm * 0.20
            recs.append(
                {
                    "question_id": pair.question_id,
                    "answer_id": pair.answer_id,
                    "title": pair.title,
                    "combined_score": float(combined),
                    "similarity": sim,
                    "answer_score": pair.answer_score,
                    "quality": {
                        "syntax_score": float(analysis.get("syntax_score") or 0.0),
                        "logic_score": float(analysis.get("logic_score") or 0.0),
                        "utility_score": float(analysis.get("utility_score") or 0.0),
                        "readability_score": float(analysis.get("readability_score") or 0.0),
                        "total_score": float(analysis.get("total_score") or 0.0),
                        "report": str(analysis.get("report") or ""),
                    },
                    "question_excerpt": _excerpt(_strip_html(_strip_code_blocks(pair.question_body)), 220),
                    "answer_excerpt": _excerpt(_strip_html(_strip_code_blocks(pair.answer_body)), 420),
                }
            )

        recs.sort(key=lambda x: float(x.get("combined_score") or 0.0), reverse=True)
        recs = recs[:top_k_recommend]
        return {"matches": matches, "recommendations": recs}


_DEFAULT_MATCHER: QAMatcher | None = None
_DEFAULT_LOCK = threading.Lock()


def get_default_matcher() -> QAMatcher:
    global _DEFAULT_MATCHER
    if _DEFAULT_MATCHER is not None:
        return _DEFAULT_MATCHER
    with _DEFAULT_LOCK:
        if _DEFAULT_MATCHER is not None:
            return _DEFAULT_MATCHER
        base_dir = Path(getattr(settings, "BASE_DIR", Path.cwd()))
        data_path = base_dir / "data" / "stackoverflow-python-qa-cleaned.jsonl"
        cache_dir = base_dir / "output" / "qa_index"
        _DEFAULT_MATCHER = QAMatcher(data_path=data_path, cache_dir=cache_dir)
        return _DEFAULT_MATCHER
