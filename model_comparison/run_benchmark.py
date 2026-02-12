from __future__ import annotations

import argparse
import json
import math
import os
import random
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


PROJECT_ROOT = Path(__file__).resolve().parent.parent

try:
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env")
except Exception:
    pass

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_DATASET_PATH = Path(r"d:\ai_assistant\data\stackoverflow-python-questions.jsonl")


@dataclass(frozen=True)
class ModelSpec:
    name: str
    provider: str
    model_id: str


def _provider_env(provider: str) -> tuple[str, str] | None:
    if provider == "qwen":
        return "QWEN_API_KEY", "QWEN_API_BASE"
    if provider == "zhipu":
        return "ZHIPU_API_KEY", "ZHIPU_API_BASE"
    return None


def _extract_first_json(text: str) -> dict[str, Any] | None:
    s = (text or "").strip()
    if not s:
        return None
    m = re.search(r"\{[\s\S]*\}", s)
    if not m:
        return None
    try:
        v = json.loads(m.group(0))
        return v if isinstance(v, dict) else None
    except Exception:
        return None


def _safe_mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _jaccard(a: set[str], b: set[str]) -> float:
    union = a | b
    return (len(a & b) / len(union)) if union else 0.0


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                items.append(obj)
    return items


def _sample_questions(items: list[dict[str, Any]], sample_size: int, seed: int) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for it in items:
        title = it.get("title")
        body = it.get("body")
        tags = it.get("tags")
        if not isinstance(title, str) or not title.strip():
            continue
        if not isinstance(body, str) or not body.strip():
            continue
        if not isinstance(tags, list) or not tags:
            continue
        filtered.append(it)

    rnd = random.Random(seed)
    if len(filtered) <= sample_size:
        return filtered
    return rnd.sample(filtered, sample_size)


def _provider_config(provider: str) -> dict[str, str] | None:
    if provider == "qwen":
        return {
            "api_key": os.environ.get("QWEN_API_KEY", "") or "",
            "base_url": os.environ.get("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1") or "",
        }
    if provider == "zhipu":
        return {
            "api_key": os.environ.get("ZHIPU_API_KEY", "") or "",
            "base_url": os.environ.get("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4/") or "",
        }
    return None


def _chat_completion(
    *,
    provider: str,
    model_id: str,
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int | None,
) -> str:
    cfg = _provider_config(provider)
    if not cfg:
        raise ValueError(f"未知 provider: {provider!r}")
    if not cfg["api_key"]:
        raise RuntimeError(f"{provider} 未配置 API_KEY")

    url = cfg["base_url"].rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {cfg['api_key']}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    try:
        return (data["choices"][0]["message"]["content"] or "").strip()
    except Exception:
        return ""


def _prompt_for_record(rec: dict[str, Any]) -> str:
    title = (rec.get("title") or "").strip()
    body = (rec.get("body") or "").strip()
    return (
        "你将看到一个 StackOverflow 的 Python 问题（标题+正文）。请完成两件事，并且只输出 JSON：\n"
        '1) predicted_tags：根据问题内容推断 1~5 个标签（小写英文；用连字符；例如 django-rest-framework）\n'
        "2) answer：用中文回答，给出清晰步骤/原因/边界情况；如果合适请给出可运行的 Python 代码块（```python）。\n"
        '输出 JSON 示例：{"predicted_tags":["python","django"],"answer":"..."}\n'
        "注意：必须是严格 JSON，禁止输出多余文字。\n\n"
        f"标题：{title}\n\n正文：\n{body}\n"
    )


def _normalize_predicted_tags(v: Any) -> list[str]:
    if not isinstance(v, list):
        return []
    out: list[str] = []
    for x in v[:10]:
        if not isinstance(x, str):
            continue
        s = x.strip().lower()
        if not s:
            continue
        s = re.sub(r"[^a-z0-9\-\.]+", "", s)
        if not s:
            continue
        out.append(s)
    uniq: list[str] = []
    seen = set()
    for s in out:
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)
    return uniq[:5]


def _ensure_matplotlib() -> Any:
    try:
        import matplotlib

        matplotlib.use("Agg")
        matplotlib.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        matplotlib.rcParams["axes.unicode_minus"] = False
        import matplotlib.pyplot as plt

        return plt
    except Exception as e:
        raise SystemExit(f"缺少 matplotlib，无法出图。请先安装：pip install matplotlib\n原始错误：{e}")


def _plot_results(results: dict[str, Any], out_dir: Path) -> None:
    plt = _ensure_matplotlib()

    models: dict[str, Any] = results.get("models") or {}
    model_names = list(models.keys())
    if not model_names:
        return

    latencies = [float(models[n].get("avg_latency_ms") or 0.0) for n in model_names]
    totals = [float(models[n].get("total_score") or 0.0) for n in model_names]
    labels = ["语义理解", "代码逻辑", "推理精度", "运行效率"]
    series: dict[str, list[float]] = {}
    for n in model_names:
        info = models[n]
        series[n] = [
            float(info.get("semantic_jaccard_mean") or 0.0),
            float(info.get("logic_score_mean") or 0.0) / 10.0,
            float(info.get("utility_score_mean") or 0.0) / 10.0,
            float(info.get("efficiency_score") or 0.0),
        ]

    angles = [i * (2 * math.pi / len(labels)) for i in range(len(labels))]
    angles += angles[:1]

    best_model = results.get("best_model") or ""
    fig = plt.figure(figsize=(12, 8), constrained_layout=True)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.3])

    ax_lat = fig.add_subplot(gs[0, 0])
    ax_lat.bar(model_names, latencies)
    ax_lat.set_title("平均延迟 (ms)")
    ax_lat.tick_params(axis="x", rotation=15)

    ax_total = fig.add_subplot(gs[0, 1])
    ax_total.bar(model_names, totals)
    ax_total.set_title("综合得分 (0~1)")
    ax_total.set_ylim(0, 1)
    ax_total.tick_params(axis="x", rotation=15)

    ax_radar = fig.add_subplot(gs[1, :], polar=True)
    ax_radar.set_theta_offset(math.pi / 2)
    ax_radar.set_theta_direction(-1)
    ax_radar.set_thetagrids([a * 180 / math.pi for a in angles[:-1]], labels)
    ax_radar.set_ylim(0, 1)

    for name in model_names:
        values = series[name] + series[name][:1]
        lw = 2.8 if best_model and name == best_model else 2.0
        ax_radar.plot(angles, values, linewidth=lw, label=name)
        ax_radar.fill(angles, values, alpha=0.06)

    title = "模型对比：效率/综合得分 + 四维能力雷达图"
    if best_model:
        title += f"（最优：{best_model}）"
    fig.suptitle(title)
    ax_radar.legend(loc="lower center", bbox_to_anchor=(0.5, -0.15), ncol=2, fontsize=10)

    fig.savefig(out_dir / "benchmark_figure.png", dpi=300)
    plt.close(fig)


def _write_core_engine(models: list[ModelSpec], results: dict[str, Any], out_dir: Path) -> dict[str, Any] | None:
    best_name = results.get("best_model")
    if not isinstance(best_name, str) or not best_name:
        return None
    best_spec = next((m for m in models if m.name == best_name), None)
    if not best_spec:
        return None
    env = _provider_env(best_spec.provider)
    if not env:
        return None
    api_key_env, base_url_env = env
    cfg = _provider_config(best_spec.provider) or {}
    core = {
        "name": best_spec.name,
        "provider": best_spec.provider,
        "model_id": best_spec.model_id,
        "base_url": cfg.get("base_url") or "",
        "api_key_env": api_key_env,
        "base_url_env": base_url_env,
    }
    (out_dir / "core_engine.json").write_text(json.dumps(core, ensure_ascii=False, indent=2), encoding="utf-8")
    return core


@dataclass(frozen=True)
class CoreEngine:
    provider: str
    model_id: str

    def chat(self, *, messages: list[dict[str, str]], temperature: float = 0.2, max_tokens: int | None = None) -> str:
        return _chat_completion(
            provider=self.provider,
            model_id=self.model_id,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )


def load_core_engine(results_path: Path | None = None) -> CoreEngine:
    p = results_path or (Path(__file__).resolve().parent / "core_engine.json")
    obj = json.loads(p.read_text(encoding="utf-8"))
    provider = obj.get("provider")
    model_id = obj.get("model_id")
    if not isinstance(provider, str) or not provider:
        raise ValueError("core_engine.json 缺少 provider")
    if not isinstance(model_id, str) or not model_id:
        raise ValueError("core_engine.json 缺少 model_id")
    return CoreEngine(provider=provider, model_id=model_id)


def _evaluate_models(models: list[ModelSpec], records: list[dict[str, Any]], max_tokens: int | None) -> dict[str, Any]:
    from django_qa.utils.code_analysis import analyze_code_comprehensive

    results: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": {"count": len(records)},
        "models": {},
        "best_model": None,
    }

    per_model_latency: dict[str, float] = {}

    for spec in models:
        latencies_ms: list[float] = []
        semantic_scores: list[float] = []
        logic_scores: list[float] = []
        utility_scores: list[float] = []

        for idx, rec in enumerate(records, start=1):
            prompt = _prompt_for_record(rec)
            messages = [{"role": "system", "content": "你是一个严谨的编程助手，严格按要求输出。"}, {"role": "user", "content": prompt}]

            start = time.perf_counter()
            raw = ""
            try:
                raw = _chat_completion(
                    provider=spec.provider,
                    model_id=spec.model_id,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
            except Exception:
                raw = ""
            end = time.perf_counter()

            lat_ms = (end - start) * 1000.0
            latencies_ms.append(lat_ms)

            obj = _extract_first_json(raw) or {}
            predicted_tags = _normalize_predicted_tags(obj.get("predicted_tags"))
            answer = obj.get("answer") if isinstance(obj.get("answer"), str) else ""

            gt_tags = rec.get("tags") if isinstance(rec.get("tags"), list) else []
            gt_set = {str(t).strip().lower() for t in gt_tags if str(t).strip()}
            pred_set = set(predicted_tags)
            semantic = _jaccard(pred_set, gt_set)
            semantic_scores.append(semantic)

            analysis = analyze_code_comprehensive(answer)
            logic_scores.append(float(analysis.get("logic_score") or 0.0))
            utility_scores.append(float(analysis.get("utility_score") or 0.0))

            if idx % 20 == 0:
                print(f"[{spec.name}] {idx}/{len(records)} done")

        avg_latency = _safe_mean(latencies_ms)
        per_model_latency[spec.name] = avg_latency

        results["models"][spec.name] = {
            "provider": spec.provider,
            "model_id": spec.model_id,
            "avg_latency_ms": avg_latency,
            "semantic_jaccard_mean": _safe_mean(semantic_scores),
            "logic_score_mean": _safe_mean(logic_scores),
            "utility_score_mean": _safe_mean(utility_scores),
        }

    if not per_model_latency:
        return results

    min_latency = min(v for v in per_model_latency.values() if v > 0) if any(v > 0 for v in per_model_latency.values()) else 1.0
    best_name = None
    best_total = -1.0
    for name, info in (results.get("models") or {}).items():
        latency = float(info.get("avg_latency_ms") or 0.0)
        efficiency = (min_latency / latency) if latency > 0 else 0.0
        efficiency = max(0.0, min(1.0, efficiency))
        semantic = float(info.get("semantic_jaccard_mean") or 0.0)
        code_logic = float(info.get("logic_score_mean") or 0.0) / 10.0
        reasoning = float(info.get("utility_score_mean") or 0.0) / 10.0
        total = (semantic + code_logic + reasoning + efficiency) / 4.0
        info["efficiency_score"] = efficiency
        info["total_score"] = total
        if total > best_total:
            best_total = total
            best_name = name

    results["best_model"] = best_name
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH), help="StackOverflow questions jsonl path")
    parser.add_argument("--sample-size", type=int, default=int(os.environ.get("SAMPLE_SIZE", "500")))
    parser.add_argument("--seed", type=int, default=int(os.environ.get("SAMPLE_SEED", "42")))
    parser.add_argument("--max-tokens", type=int, default=int(os.environ.get("MAX_TOKENS", "900")))
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        raise SystemExit(f"数据集文件不存在: {dataset_path}")

    items = _read_jsonl(dataset_path)
    records = _sample_questions(items, args.sample_size, args.seed)

    models = [
        ModelSpec(name="qwen-max", provider="qwen", model_id="qwen-max"),
        ModelSpec(name="qwen-plus", provider="qwen", model_id="qwen-plus"),
        ModelSpec(name="glm-4", provider="zhipu", model_id="glm-4"),
        ModelSpec(name="glm-4-flash", provider="zhipu", model_id="glm-4-flash"),
    ]

    out_dir = Path(__file__).resolve().parent
    out_dir.mkdir(parents=True, exist_ok=True)

    results = _evaluate_models(models, records, args.max_tokens)
    (out_dir / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    _plot_results(results, out_dir)
    core = _write_core_engine(models, results, out_dir)

    print("OK")
    print(f"results: {out_dir / 'results.json'}")
    print(f"plot:    {out_dir / 'benchmark_figure.png'}")
    if core:
        print(f"core:    {out_dir / 'core_engine.json'}")
    print(f"best_model: {results.get('best_model') or '<none>'}")


if __name__ == "__main__":
    main()

