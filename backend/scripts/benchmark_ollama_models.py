#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import httpx


DEFAULT_MODELS = [
    "qwen3:8b",
    "qwen3.5:latest",
    "qwen3:14b",
    "phi4-mini-reasoning:latest",
    "gemma3:12b",
]

SYSTEM_PROMPT = (
    "You are being benchmarked as a local assistant. "
    "Answer clearly and concisely. "
    "When context is provided, stay grounded in it and say what is unknown instead of inventing facts."
)

KEDAH_CONTEXT = """Grounding facts from the project's Kedah investment showcase:
- Total approved investment RM: 62,599,928,663.3959
- Top 5 industries by approved investment RM:
  1. Manufacturing: 4,065,271,041.63
  2. Plastic Products: 2,562,888,007.09
  3. Electrical & Electronics: 725,028,545.14
  4. Transport Equipment: 604,691,083.88
  5. Services: 299,393,519.82
- Total employment from all investment records: 268,621
- Top 5 countries by foreign investment amount:
  1. USA: 9,726,328,205.02
  2. Japan: 7,381,662,060.48
  3. The People's Republic of China: 4,747,461,112.0
  4. Germany: 1,278,044,633.0
  5. Singapore: 440,549,723.14
- Distinct sectors present: services, unknown, manufacturing
- Limitation: the available summary does not contain enough yearly totals to identify which year had the highest approved investment."""

AIRPORT_CONTEXT = """Grounding rules from the project's airport operations blueprint:
- For high-risk domains like airport incidents, safety, compliance, HR, legal, or emergency response:
  - prefer approved documents
  - show citation and document version
  - avoid speculative answers
  - add an escalation note when confidence is low
- Example approved answer:
  "Based on Emergency Response Manual v3.2, Section 4.1, notify Airport Fire & Rescue Service immediately and initiate incident reporting Form IR-02. Please verify with duty supervisor if the incident involves fuel leakage."
- Priority-based grounding order:
  1. Curated FAQ / approved answer
  2. Approved SOP / policy chunks
  3. Structured data result
  4. General model reasoning only when grounded sources are insufficient"""


@dataclass(frozen=True)
class BenchmarkQuestion:
    slug: str
    topic: str
    prompt: str
    context: str
    source_note: str


@dataclass
class BenchmarkResult:
    model: str
    question_slug: str
    topic: str
    wall_time_s: float
    total_duration_s: float | None
    load_duration_s: float | None
    prompt_eval_count: int | None
    eval_count: int | None
    eval_duration_s: float | None
    tokens_per_second: float | None
    answer: str
    source_note: str


QUESTIONS = [
    BenchmarkQuestion(
        slug="kedah-investor-summary",
        topic="kedah-investment",
        prompt=(
            "Using only the context, write a short investor-facing summary of Kedah's approved investment story. "
            "Mention the overall scale, the strongest industries, and what foreign investor interest suggests."
        ),
        context=KEDAH_CONTEXT,
        source_note="showcase_kedah_best_qa.txt",
    ),
    BenchmarkQuestion(
        slug="kedah-priority-sectors",
        topic="kedah-investment",
        prompt=(
            "From the context, recommend the top 3 sectors to highlight in a Kedah investment pitch. "
            "Give one sentence of justification for each."
        ),
        context=KEDAH_CONTEXT,
        source_note="showcase_kedah_best_qa.txt",
    ),
    BenchmarkQuestion(
        slug="kedah-data-limitation",
        topic="kedah-investment",
        prompt=(
            "A client asks which year had the highest total approved investment RM. "
            "Answer safely using only the context and explain the data limitation."
        ),
        context=KEDAH_CONTEXT,
        source_note="showcase_kedah_best_qa.txt",
    ),
    BenchmarkQuestion(
        slug="airport-runway-incident",
        topic="airport-operations",
        prompt=(
            "An aircraft incident happens on the runway. "
            "Draft the safest short answer an internal airport assistant should give, based only on the context."
        ),
        context=AIRPORT_CONTEXT,
        source_note="production_multitenant_customer_service_platform_blueprint.md",
    ),
    BenchmarkQuestion(
        slug="airport-ai-guardrails",
        topic="airport-operations",
        prompt=(
            "Summarize the response rules the assistant should follow for airport emergency or safety questions. "
            "Keep it brief and practical."
        ),
        context=AIRPORT_CONTEXT,
        source_note="production_multitenant_customer_service_platform_blueprint.md",
    ),
    BenchmarkQuestion(
        slug="airport-form-and-escalation",
        topic="airport-operations",
        prompt=(
            "What form should be initiated for an apron or runway incident, and who should be notified first? "
            "Answer carefully and include an escalation caveat if needed."
        ),
        context=AIRPORT_CONTEXT,
        source_note="production_multitenant_customer_service_platform_blueprint.md",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark several Ollama models on Kedah investment and airport prompts."
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=DEFAULT_MODELS,
        help="Ollama model tags to benchmark.",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama base URL.",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=4096,
        help="Context window to request from Ollama.",
    )
    parser.add_argument(
        "--num-predict",
        type=int,
        default=512,
        help="Maximum generated tokens per answer.",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for the benchmark.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="How many times to run each model/question pair.",
    )
    parser.add_argument(
        "--skip-warmup",
        action="store_true",
        help="Do not warm up each model before the benchmark.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "benchmark_results"),
        help="Directory to store markdown and JSON reports.",
    )
    return parser.parse_args()


def build_user_message(question: BenchmarkQuestion) -> str:
    return (
        f"Context:\n{question.context}\n\n"
        f"Question:\n{question.prompt}\n\n"
        "Answer in plain English. If the context is insufficient, say so plainly."
    )


def ns_to_s(value: int | None) -> float | None:
    if not value:
        return None
    return value / 1_000_000_000


def fmt_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "-"
    return f"{value:.{digits}f}"


def available_models(client: httpx.Client) -> set[str]:
    response = client.get("/api/tags")
    response.raise_for_status()
    payload = response.json()
    return {item.get("name", "") for item in payload.get("models", [])}


def warmup_model(client: httpx.Client, model: str) -> None:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with OK."}],
        "stream": False,
        "think": False,
        "options": {
            "temperature": 0,
            "num_ctx": 512,
            "num_predict": 8,
        },
    }
    response = client.post("/api/chat", json=payload)
    response.raise_for_status()


def run_one(
    client: httpx.Client,
    model: str,
    question: BenchmarkQuestion,
    *,
    num_ctx: int,
    num_predict: int,
    temperature: float,
) -> BenchmarkResult:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_user_message(question)},
        ],
        "stream": False,
        "think": False,
        "options": {
            "num_ctx": num_ctx,
            "num_predict": num_predict,
            "temperature": temperature,
        },
    }

    start = time.perf_counter()
    response = client.post("/api/chat", json=payload)
    response.raise_for_status()
    wall_time_s = time.perf_counter() - start

    data = response.json()
    answer = data.get("message", {}).get("content", "").strip()
    eval_count = data.get("eval_count")
    eval_duration_s = ns_to_s(data.get("eval_duration"))
    tokens_per_second = None
    if eval_count and eval_duration_s and eval_duration_s > 0:
        tokens_per_second = eval_count / eval_duration_s

    return BenchmarkResult(
        model=model,
        question_slug=question.slug,
        topic=question.topic,
        wall_time_s=wall_time_s,
        total_duration_s=ns_to_s(data.get("total_duration")),
        load_duration_s=ns_to_s(data.get("load_duration")),
        prompt_eval_count=data.get("prompt_eval_count"),
        eval_count=eval_count,
        eval_duration_s=eval_duration_s,
        tokens_per_second=tokens_per_second,
        answer=answer,
        source_note=question.source_note,
    )


def summarize_by_model(results: list[BenchmarkResult]) -> list[dict]:
    grouped: dict[str, list[BenchmarkResult]] = {}
    for result in results:
        grouped.setdefault(result.model, []).append(result)

    summary = []
    for model, items in grouped.items():
        wall_times = [item.wall_time_s for item in items]
        token_rates = [item.tokens_per_second for item in items if item.tokens_per_second is not None]
        summary.append(
            {
                "model": model,
                "runs": len(items),
                "avg_wall_time_s": statistics.mean(wall_times),
                "median_wall_time_s": statistics.median(wall_times),
                "avg_tokens_per_second": statistics.mean(token_rates) if token_rates else None,
            }
        )

    summary.sort(key=lambda item: item["avg_wall_time_s"])
    return summary


def write_markdown_report(
    report_path: Path,
    *,
    args: argparse.Namespace,
    results: list[BenchmarkResult],
    model_summary: list[dict],
) -> None:
    grouped: dict[str, list[BenchmarkResult]] = {}
    for result in results:
        grouped.setdefault(result.question_slug, []).append(result)

    with report_path.open("w", encoding="utf-8") as handle:
        handle.write("# Ollama Benchmark Report\n\n")
        handle.write(f"- Generated: {datetime.now().isoformat(timespec='seconds')}\n")
        handle.write(f"- Models: {', '.join(args.models)}\n")
        handle.write(f"- Repeat per question: {args.repeat}\n")
        handle.write(f"- num_ctx: {args.num_ctx}\n")
        handle.write(f"- num_predict: {args.num_predict}\n")
        handle.write(f"- temperature: {args.temperature}\n\n")

        handle.write("## Model Speed Summary\n\n")
        handle.write("| Model | Runs | Avg wall time (s) | Median wall time (s) | Avg tokens/s |\n")
        handle.write("|---|---:|---:|---:|---:|\n")
        for item in model_summary:
            handle.write(
                f"| {item['model']} | {item['runs']} | {fmt_float(item['avg_wall_time_s'])} | "
                f"{fmt_float(item['median_wall_time_s'])} | {fmt_float(item['avg_tokens_per_second'])} |\n"
            )

        for question in QUESTIONS:
            handle.write("\n")
            handle.write(f"## {question.slug}\n\n")
            handle.write(f"- Topic: {question.topic}\n")
            handle.write(f"- Source note: `{question.source_note}`\n")
            handle.write(f"- Prompt: {question.prompt}\n\n")

            for result in sorted(grouped.get(question.slug, []), key=lambda item: item.wall_time_s):
                handle.write(f"### {result.model}\n\n")
                handle.write(
                    f"- Wall time: {fmt_float(result.wall_time_s)} s\n"
                    f"- Total duration: {fmt_float(result.total_duration_s)} s\n"
                    f"- Load duration: {fmt_float(result.load_duration_s)} s\n"
                    f"- Prompt tokens: {result.prompt_eval_count or '-'}\n"
                    f"- Output tokens: {result.eval_count or '-'}\n"
                    f"- Output speed: {fmt_float(result.tokens_per_second)} tok/s\n\n"
                )
                handle.write("```text\n")
                handle.write((result.answer or "[empty response]").strip())
                handle.write("\n```\n")


def write_json_report(report_path: Path, results: list[BenchmarkResult]) -> None:
    payload = [asdict(result) for result in results]
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with httpx.Client(base_url=args.base_url, timeout=httpx.Timeout(180, connect=10)) as client:
        try:
            installed = available_models(client)
        except Exception as exc:
            print(f"Could not reach Ollama at {args.base_url}: {exc}", file=sys.stderr)
            return 1

        selected_models = [model for model in args.models if model in installed]
        missing_models = [model for model in args.models if model not in installed]

        if missing_models:
            print("Skipping missing models:", ", ".join(missing_models), file=sys.stderr)
        if not selected_models:
            print("No selected models are installed in Ollama.", file=sys.stderr)
            return 1

        if not args.skip_warmup:
            for model in selected_models:
                print(f"[warmup] {model}", flush=True)
                warmup_model(client, model)

        total_runs = len(selected_models) * len(QUESTIONS) * args.repeat
        counter = 0
        results: list[BenchmarkResult] = []

        for repeat_idx in range(args.repeat):
            for question in QUESTIONS:
                for model in selected_models:
                    counter += 1
                    print(
                        f"[{counter}/{total_runs}] model={model} question={question.slug} repeat={repeat_idx + 1}",
                        flush=True,
                    )
                    result = run_one(
                        client,
                        model,
                        question,
                        num_ctx=args.num_ctx,
                        num_predict=args.num_predict,
                        temperature=args.temperature,
                    )
                    results.append(result)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    markdown_path = output_dir / f"ollama_benchmark_{timestamp}.md"
    json_path = output_dir / f"ollama_benchmark_{timestamp}.json"
    model_summary = summarize_by_model(results)

    write_markdown_report(markdown_path, args=args, results=results, model_summary=model_summary)
    write_json_report(json_path, results)

    print(f"\nMarkdown report: {markdown_path}")
    print(f"JSON report: {json_path}")
    print("\nFastest average wall time:")
    for item in model_summary:
        print(
            f"- {item['model']}: avg {fmt_float(item['avg_wall_time_s'])} s, "
            f"avg {fmt_float(item['avg_tokens_per_second'])} tok/s"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
