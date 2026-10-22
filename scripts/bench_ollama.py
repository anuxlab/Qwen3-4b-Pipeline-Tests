"""Robust Ollama/Qwen benchmark runner. Does not require model-specific tokenizer packages."""
from __future__ import annotations
import argparse, json, os, platform, statistics, subprocess, time, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import psutil
import requests

OLLAMA = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
SCHEMA_VERSION = 2


def parse_ints(value: str, name: str, minimum: int = 1) -> list[int]:
    try:
        vals = sorted(set(int(x.strip()) for x in value.split(",") if x.strip()))
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"{name} must be comma-separated integers") from exc
    if not vals or any(x < minimum for x in vals):
        raise argparse.ArgumentTypeError(f"{name} values must be >= {minimum}")
    return vals


def ollama_request(path: str, body: dict[str, Any], timeout: int = 900) -> dict[str, Any]:
    response = requests.post(f"{OLLAMA}{path}", json=body, timeout=timeout)
    response.raise_for_status()
    return response.json()


def model_info(model: str) -> dict[str, Any]:
    try:
        d = ollama_request("/api/show", {"model": model}, timeout=45)
        details = d.get("details") or {}
        return {
            "family": details.get("family"), "families": details.get("families"),
            "parameter_size": details.get("parameter_size"),
            "quantization": details.get("quantization_level"), "format": details.get("format"),
            "modelfile": d.get("modelfile"), "template": d.get("template"),
            "capabilities": d.get("capabilities"), "metadata_error": None,
        }
    except Exception as exc:
        return {"metadata_error": f"{type(exc).__name__}: {exc}"}


def make_long_context_prompt(target_tokens: int, sentinel: str = "ORCHID") -> str:
    """Build a long prompt near a character/token heuristic; actual count is reported by Ollama."""
    intro = (
        "Read the complete passage. It contains a marker assigned to a fictional research run. "
        "Ignore all other words that resemble labels. At the end, return only the exact marker.\n\n"
    )
    # Keep the target answer in a single explicit fact near the middle, not in the repeated filler.
    fact = f"FACT FOR THIS RUN: the unique marker is {sentinel}.\n\n"
    filler = "A neutral archive note describes a river, a valley, a bridge, and seasonal rainfall. "
    desired_chars = max(0, int(target_tokens * 3.7) - len(intro) - len(fact) - 100)
    body = (filler * (desired_chars // len(filler) + 1))[:desired_chars]
    # The marker appears only in the fact and question, avoiding accidental scoring from filler.
    return intro + body + "\n\n" + fact + f"Question: What is the unique marker? Return only {sentinel} or the marker itself."


def make_position_prompt(target_tokens: int, position: str) -> tuple[str, str]:
    """Build a needle-in-a-haystack prompt with the answer at the requested position."""
    needle = "X7-ORCHID-29"
    pre = "You will read an archive. Find the exact archive code stated in one note. Return only that code.\n\n"
    post = "\n\nQuestion: What is the exact archive code? Return only the code."
    filler = "Routine archive entry: the weather was mild, the river level was stable, and the bridge remained open. "
    desired = max(300, int(target_tokens * 3.7) - len(pre) - len(post) - 100)
    body = (filler * (desired // len(filler) + 1))[:desired]
    note = f"SPECIAL NOTE: archive code = {needle}.\n"
    if position == "beginning": offset = 0
    elif position == "middle": offset = len(body) // 2
    else: offset = len(body)
    body = body[:offset] + note + body[offset:]
    return pre + body + post, needle


def extract_answer(data: dict[str, Any]) -> tuple[str, str | None]:
    """Extract user-facing answer across Ollama versions and Qwen think-tag formats.

    Ollama versions/models may return reasoning in ``message.thinking``, or embed
    <think>...</think> inside ``message.content``. Never score an unfinished
    think-only response as the final answer.
    """
    import re
    message = data.get("message") or {}
    content = message.get("content")
    if content is None:
        content = data.get("response", "")
    raw_content = str(content or "").strip()
    thinking_parts = [str(message.get("thinking") or data.get("thinking") or "").strip()]
    # Pull complete thinking blocks out of content, retaining the text after </think>.
    block_pattern = re.compile(r"<think>(.*?)</think>", flags=re.I | re.S)
    thinking_parts.extend(x.strip() for x in block_pattern.findall(raw_content) if x.strip())
    cleaned = block_pattern.sub("", raw_content).strip()
    # An open <think> with no closing tag means the output cap likely interrupted
    # reasoning before a user-facing answer was produced.
    if re.search(r"<think>", cleaned, flags=re.I) and not re.search(r"</think>", raw_content, flags=re.I):
        open_thought = re.split(r"<think>", cleaned, maxsplit=1, flags=re.I)[-1].strip()
        if open_thought:
            thinking_parts.append(open_thought)
        cleaned = ""
    # Some templates put the final answer after an explicit </think> delimiter.
    if "</think>" in raw_content.lower():
        idx = raw_content.lower().rfind("</think>")
        tail = raw_content[idx + len("</think>"):].strip()
        if tail:
            cleaned = tail
    thinking = "\\n".join(x for x in thinking_parts if x).strip() or None
    return cleaned, thinking




def ollama_process_memory() -> dict[str, float | None]:
    """Best-effort memory snapshot for Ollama server/runner processes, not Python itself."""
    rss = 0
    uss = 0
    matched = False
    for proc in psutil.process_iter(["name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            cmdline = " ".join(proc.info.get("cmdline") or []).lower()
            if not (name.startswith("ollama") or "ollama runner" in cmdline or "ollama serve" in cmdline):
                continue
            matched = True
            rss += proc.memory_info().rss
            try:
                uss += proc.memory_full_info().uss
            except (psutil.AccessDenied, AttributeError, OSError):
                pass
        except (psutil.NoSuchProcess, psutil.AccessDenied, OSError):
            continue
    return {
        "ollama_process_rss_gb": round(rss / 2**30, 3) if matched else None,
        "ollama_process_uss_gb": round(uss / 2**30, 3) if matched and uss else None,
    }


def generate(model: str, prompt: str, ctx: int, output_cap: int, timeout: int) -> dict[str, Any]:
    start = time.perf_counter()
    data = ollama_request("/api/chat", {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        # Explicitly disable Qwen3 thinking where supported so answer text is returned in content.
        "think": False,
        "options": {"num_predict": output_cap, "temperature": 0, "top_p": 1,
                     "num_ctx": ctx, "seed": 42},
    }, timeout=timeout)
    wall = time.perf_counter() - start
    answer, thinking = extract_answer(data)
    prompt_count = data.get("prompt_eval_count")
    completion_count = int(data.get("eval_count") or 0)
    eval_ns = int(data.get("eval_duration") or 0)
    prompt_ns = int(data.get("prompt_eval_duration") or 0)
    load_ns = int(data.get("load_duration") or 0)
    done_reason = data.get("done_reason")
    # Ollama may return no done_reason on some versions. Don't infer a truncation unless count hits cap.
    return {
        "status": "ok", "model": model, "context_requested": ctx,
        "output_limit_requested": output_cap, "prompt_tokens_actual": prompt_count,
        "completion_tokens_actual": completion_count,
        "context_utilization": round(prompt_count / ctx, 4) if isinstance(prompt_count, int) and ctx else None,
        "context_fit": (prompt_count is not None and prompt_count + output_cap <= ctx),
        "wall_latency_sec": round(wall, 4),
        "prompt_eval_sec": round(prompt_ns / 1e9, 4) if prompt_ns else None,
        "generation_sec": round(eval_ns / 1e9, 4) if eval_ns else None,
        "load_sec": round(load_ns / 1e9, 4) if load_ns else None,
        "time_to_first_token_proxy_sec": round((load_ns + prompt_ns) / 1e9, 4) if load_ns or prompt_ns else None,
        "generation_tokens_per_sec": round(completion_count / (eval_ns / 1e9), 3) if eval_ns else None,
        "done_reason": done_reason,
        "output_cap_reached": completion_count >= output_cap,
        "answer_text": answer, "thinking_present": bool(thinking),
        "response_excerpt": answer[:300],
        "raw_content_excerpt": str((data.get("message") or {}).get("content") or data.get("response") or "")[:500],
        "thinking_excerpt": (thinking or "")[:500] or None,
        "answer_status": "final_answer_present" if answer else "thinking_only_or_empty",
        **ollama_process_memory(),
        "ollama_total_duration_sec": round(int(data.get("total_duration") or 0) / 1e9, 4) or None,
    }


def quality_cases() -> list[dict[str, Any]]:
    return [
        {"id":"qa_capital_france", "prompt":"What is the capital of France? Answer with only the city name.", "expected":["paris"], "kind":"exact_match"},
        {"id":"qa_bat_ball", "prompt":"A bat and ball cost $1.10 total. The bat costs $1.00 more than the ball. How much does the ball cost? Answer only as a dollar amount.", "expected":["$0.05", "0.05"], "kind":"contains_any"},
        {"id":"instruction_three_colors", "prompt":"Return exactly three primary colors as a JSON array of three strings, no other text.", "expected":["red", "yellow", "blue"], "kind":"contains_all"},
        {"id":"structured_json", "prompt":"Return valid JSON only with keys \"status\" and \"count\", values \"ok\" and 3.", "expected":{"status":"ok","count":3}, "kind":"json_equal"},
        {"id":"long_context_retrieval", "prompt":"Notes: Site A opened in 1984. Site B opened in 1997. Site C opened in 2011. Which year did Site B open? Answer with only the year.", "expected":["1997"], "kind":"contains_any"},
    ]


def score_quality(case: dict[str, Any], answer: str) -> tuple[bool, str | None]:
    import re
    text = answer.strip()
    low = text.lower()
    if case["kind"] == "exact_match":
        ok = low.strip(" .\n\t") in case["expected"]
    elif case["kind"] == "contains_any":
        ok = any(x.lower() in low for x in case["expected"])
    elif case["kind"] == "contains_all":
        ok = all(x in low for x in case["expected"])
    elif case["kind"] == "json_equal":
        try:
            cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
            got = json.loads(cleaned)
            ok = got == case["expected"]
        except Exception:
            ok = False
    else:
        ok = False
    return bool(ok), case["kind"]


def hardware_info() -> dict[str, Any]:
    try:
        ollama_version = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        ollama_version = None
    vm = psutil.virtual_memory()
    return {"python": platform.python_version(), "platform": platform.platform(),
            "cpu_count_logical": psutil.cpu_count(), "ram_total_gb": round(vm.total / 2**30, 2),
            "ram_available_gb_at_start": round(vm.available / 2**30, 2), "ollama_version": ollama_version,
            "ollama_host": OLLAMA}


def run(args: argparse.Namespace) -> dict[str, Any]:
    contexts = parse_ints(args.contexts, "contexts", 128)
    inputs = parse_ints(args.input_targets, "input-targets", 16)
    outputs = parse_ints(args.output_limits, "output-limits", 1)
    model = args.model
    info = model_info(model)
    cases: list[dict[str, Any]] = []
    # Input targets are heuristic. Run all combinations but mark impossible budgets as skipped.
    for ctx in contexts:
        for inp in inputs:
            for out in outputs:
                cases.append({"kind":"context_matrix", "context":ctx, "input_target":inp, "output_cap":out})
    if args.max_cases and args.max_cases > 0:
        cases = cases[:args.max_cases]
    results: list[dict[str, Any]] = []
    for index, spec in enumerate(cases, 1):
        case_id = f"ctx{spec['context']}_target{spec['input_target']}_out{spec['output_cap']}"
        # Prompt targets are approximate, so reserve a conservative safety margin; validate actual tokens post-call.
        estimated_input = spec["input_target"]
        if estimated_input + spec["output_cap"] + args.context_safety_margin > spec["context"]:
            results.append({"case_id":case_id, "kind":"context_matrix", "status":"skipped_budget",
                "model":model, "context_requested":spec["context"], "input_target_tokens":estimated_input,
                "output_limit_requested":spec["output_cap"], "error":"Requested input + output cap + safety margin exceeds context setting."})
            continue
        for repetition in range(1, args.repeats + 1):
            try:
                prompt = make_long_context_prompt(spec["input_target"], sentinel="ORCHID")
                r = generate(model, prompt, spec["context"], spec["output_cap"], args.timeout)
                r.update({"case_id":case_id, "kind":"context_matrix", "repeat":repetition,
                    "input_target_tokens":spec["input_target"],
                    "input_target_error_tokens": (r.get("prompt_tokens_actual") - spec["input_target"]) if isinstance(r.get("prompt_tokens_actual"), int) else None,
                    "sentinel_answer_correct": r.get("answer_text", "").strip().upper().strip(" .!\n\t") == "ORCHID",
                    "answer_scoring_note":"Exact sentinel match only; this is a smoke check, not general language quality."})
                # A returned response that exceeded the requested context budget is not counted as a valid fit.
                if isinstance(r.get("prompt_tokens_actual"), int) and r["prompt_tokens_actual"] + spec["output_cap"] > spec["context"]:
                    r["context_fit"] = False
                    r["context_validation_warning"] = "Actual prompt tokens + requested output cap exceed context setting."
            except Exception as exc:
                r = {"case_id":case_id, "kind":"context_matrix", "repeat":repetition, "status":"error", "model":model,
                     "context_requested":spec["context"], "input_target_tokens":spec["input_target"],
                     "output_limit_requested":spec["output_cap"], "error":f"{type(exc).__name__}: {exc}"}
            results.append(r)
            print(json.dumps(r, ensure_ascii=False), flush=True)
    if args.quality_suite:
        for case in quality_cases():
            for repetition in range(1, args.repeats + 1):
                try:
                    r = generate(model, case["prompt"], args.quality_context, args.quality_output_cap, args.timeout)
                    correct, scoring = score_quality(case, r.get("answer_text", ""))
                    r.update({"case_id":case["id"], "kind":"quality", "repeat":repetition,
                              "answer_correct":correct, "scoring_method":scoring,
                              "expected_answer":case["expected"]})
                except Exception as exc:
                    r = {"case_id":case["id"], "kind":"quality", "repeat":repetition, "status":"error", "model":model,
                         "error":f"{type(exc).__name__}: {exc}"}
                results.append(r)
                print(json.dumps(r, ensure_ascii=False), flush=True)
    if args.position_suite:
        # Probe retrieval at multiple positions at the largest requested context/input budget.
        ctx = max(contexts)
        out_cap = min(outputs)
        eligible = [x for x in inputs if x + out_cap + args.context_safety_margin <= ctx]
        target = max(eligible) if eligible else max(16, ctx - out_cap - args.context_safety_margin)
        for position in ("beginning", "middle", "end"):
            for repetition in range(1, args.repeats + 1):
                case_id = f"needle_{position}_ctx{ctx}_target{target}"
                try:
                    prompt, expected = make_position_prompt(target, position)
                    r = generate(model, prompt, ctx, out_cap, args.timeout)
                    answer = r.get("answer_text", "").strip().upper().strip(" .!\n\t`*")
                    r.update({"case_id":case_id, "kind":"position_retrieval", "position":position, "repeat":repetition,
                              "input_target_tokens":target, "expected_answer":expected,
                              "answer_correct":answer == expected,
                              "input_target_error_tokens":(r.get("prompt_tokens_actual") - target) if isinstance(r.get("prompt_tokens_actual"),int) else None})
                except Exception as exc:
                    r = {"case_id":case_id, "kind":"position_retrieval", "position":position, "repeat":repetition,
                         "status":"error", "model":model, "error":f"{type(exc).__name__}: {exc}"}
                results.append(r)
                print(json.dumps(r, ensure_ascii=False), flush=True)
    if args.output_cap_suite:
        # Ask for sustained output; this measures whether the runtime respects each output ceiling.
        ctx = max(contexts)
        for cap in outputs:
            for repetition in range(1, args.repeats + 1):
                case_id = f"output_cap_probe_{cap}"
                try:
                    prompt = "Write a long numbered list of short, distinct facts. Continue until stopped. Do not summarize or stop early. Start with item 1."
                    r = generate(model, prompt, ctx, cap, args.timeout)
                    r.update({"case_id":case_id, "kind":"output_cap_probe", "repeat":repetition,
                              "output_limit_requested":cap, "output_cap_respected":r.get("completion_tokens_actual",0) <= cap,
                              "likely_cap_limited":r.get("completion_tokens_actual",0) >= cap})
                except Exception as exc:
                    r = {"case_id":case_id, "kind":"output_cap_probe", "repeat":repetition, "status":"error", "model":model,
                         "output_limit_requested":cap, "error":f"{type(exc).__name__}: {exc}"}
                results.append(r)
                print(json.dumps(r, ensure_ascii=False), flush=True)
    process = psutil.Process(os.getpid())
    try: process_uss = round(process.memory_full_info().uss / 2**30, 3)
    except Exception: process_uss = None
    return {"schema_version":SCHEMA_VERSION, "run_id":str(uuid.uuid4()), "timestamp_utc":datetime.now(timezone.utc).isoformat(),
        "method":"ollama_chat", "model":model, "model_info":info, "runtime":hardware_info(),
        "process_memory_uss_gb_after":process_uss,
        "test_plan":{"contexts":contexts, "input_targets_approximate":inputs, "output_limits":outputs,
          "repeats":args.repeats, "quality_suite_enabled":args.quality_suite, "position_suite_enabled":args.position_suite, "output_cap_suite_enabled":args.output_cap_suite, "context_safety_margin":args.context_safety_margin,
          "cases_planned":len(cases), "results_recorded":len(results), "note":"Input target uses a character/token heuristic. Actual prompt_eval_count is authoritative."},
        "results":results}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--model", required=True)
    ap.add_argument("--contexts", default="512,1024,2048,4096,8192")
    ap.add_argument("--input-targets", default="128,512,1024,2048,4096")
    ap.add_argument("--output-limits", default="32,128,512")
    ap.add_argument("--output-json", default="results/result.json")
    ap.add_argument("--max-cases", type=int, default=0, help="Cap matrix cases for smoke tests; 0 means all")
    ap.add_argument("--repeats", type=int, default=2)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--context-safety-margin", type=int, default=32)
    ap.add_argument("--quality-suite", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--position-suite", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--output-cap-suite", action=argparse.BooleanOptionalAction, default=True)
    ap.add_argument("--quality-context", type=int, default=2048)
    ap.add_argument("--quality-output-cap", type=int, default=128)
    args = ap.parse_args()
    if args.repeats < 1: ap.error("--repeats must be >= 1")
    if args.max_cases < 0: ap.error("--max-cases must be >= 0")
    payload = run(args)
    path = Path(args.output_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    ok = sum(r.get("status") == "ok" for r in payload["results"])
    failed = sum(r.get("status") == "error" for r in payload["results"])
    print(f"Wrote {path}: {ok} successful, {failed} failed, {len(payload['results'])} total records")
    return 0 if ok and not failed else (2 if failed or not ok else 0)

if __name__ == "__main__":
    raise SystemExit(main())
