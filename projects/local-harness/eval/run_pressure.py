#!/usr/bin/env python3
"""
Context pressure eval runner.

Usage:
  python eval/run_pressure.py --smoke
  python eval/run_pressure.py
  python eval/run_pressure.py --models qwen2.5:7b llama3.1:8b
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

PROXY = "http://localhost:8080"
DEFAULT_MODELS = ["qwen2.5-coder:7b", "qwen2.5:7b", "llama3.1:8b", "mistral:7b"]
TASKS_PATH = Path(__file__).parent / "pressure_tasks.json"
OUTPUT_PATH = Path(__file__).parent / "pressure_raw.jsonl"

TOOL_SCHEMAS = {
    "read_file": {"type": "function", "function": {"name": "read_file", "description": "Read the full contents of a file at the given path.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]}}},
    "write_file": {"type": "function", "function": {"name": "write_file", "description": "Write content to a file.", "parameters": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}}},
    "run_command": {"type": "function", "function": {"name": "run_command", "description": "Run a shell command and return its output.", "parameters": {"type": "object", "properties": {"cmd": {"type": "string"}}, "required": ["cmd"]}}},
    "search_files": {"type": "function", "function": {"name": "search_files", "description": "Search for files matching a pattern.", "parameters": {"type": "object", "properties": {"pattern": {"type": "string"}, "directory": {"type": "string"}}, "required": ["pattern", "directory"]}}},
}


def build_messages(task: dict) -> list[dict]:
    messages = []
    if task.get("context_prefix"):
        # Inject file context as a prior user/assistant exchange
        messages.append({"role": "user", "content": "Here is the project context for our session:"})
        messages.append({"role": "assistant", "content": task["context_prefix"]})
    messages.append({"role": "user", "content": task["prompt"]})
    return messages


def call_once(model: str, task: dict, messages: list[dict], timeout: int = 120) -> tuple[dict | None, float]:
    tools = [TOOL_SCHEMAS[t] for t in task["tools"]]
    payload = {"model": model, "stream": False, "tools": tools, "messages": messages}
    if task.get("system"):
        payload["system"] = task["system"]
    t0 = time.time()
    try:
        resp = requests.post(f"{PROXY}/v1/chat/completions", json=payload, timeout=timeout)
        elapsed = time.time() - t0
        return (resp.json() if resp.ok else {"error": resp.text, "status": resp.status_code}), elapsed
    except Exception as e:
        return {"error": str(e)}, time.time() - t0


def extract_tool_call(result: dict) -> dict | None:
    """Return {name, arguments_raw} from tool_calls if present."""
    choices = result.get("choices", [])
    if not choices:
        return None
    msg = choices[0].get("message", {})
    tcs = msg.get("tool_calls")
    if tcs and isinstance(tcs, list) and tcs:
        fn = tcs[0].get("function", {})
        return {"name": fn.get("name", ""), "arguments_raw": fn.get("arguments", "{}")}
    return None


def call_multiturn(model: str, task: dict, timeout: int = 120) -> tuple[dict, dict | None, float]:
    """Run turn 1, inject fake result, run turn 2. Returns (turn1_result, turn2_result, total_elapsed)."""
    t0 = time.time()
    messages = build_messages(task)

    result1, _ = call_once(model, task, messages, timeout)
    tc = extract_tool_call(result1) if result1 and "error" not in result1 else None

    if tc is None:
        return result1, None, time.time() - t0

    # Build turn 2: append assistant tool call + fake tool result + follow-up
    tool_call_msg = {
        "role": "assistant",
        "content": None,
        "tool_calls": [{"id": "call_0", "type": "function", "function": {"name": tc["name"], "arguments": tc["arguments_raw"]}}],
    }
    tool_result_msg = {
        "role": "tool",
        "tool_call_id": "call_0",
        "content": task.get("fake_tool_result", "Done."),
    }
    messages2 = messages + [tool_call_msg, tool_result_msg, {"role": "user", "content": task["turn2_prompt"]}]

    # For turn 2, update expected tool
    task2 = {**task, "expected_tool": task["turn2_expected_tool"], "check_params": False}
    result2, _ = call_once(model, task2, messages2, timeout)

    return result1, result2, time.time() - t0


def status_char(result: dict | None) -> str:
    if result is None or "error" in result:
        return "ERR"
    choices = result.get("choices", [])
    if not choices:
        return "ERR"
    msg = choices[0].get("message", {})
    tool_calls = msg.get("tool_calls")
    if tool_calls and isinstance(tool_calls, list) and tool_calls:
        return "ok"
    content = (msg.get("content") or "").strip().lstrip("`").strip()
    try:
        parsed = json.loads(content)
        if "name" in parsed or "function" in parsed or "arguments" in parsed:
            return "wrap"
    except Exception:
        pass
    return "ERR(refusal)" if content else "ERR(empty)"


def run_smoke(models: list[str], tasks: list[dict]) -> None:
    # 4 tasks: one per condition, single-turn only
    sample = [t for t in tasks if not t["multiturn"]]
    conditions = ["bare", "sysprompt", "context_sm", "context_lg"]
    sample_tasks = []
    for cond in conditions:
        match = next((t for t in sample if t["condition"] == cond), None)
        if match:
            sample_tasks.append(match)

    for model in models:
        print(f"\nSmoke — {model}")
        print("-" * 60)
        for task in sample_tasks:
            messages = build_messages(task)
            result, elapsed = call_once(model, task, messages)
            status = status_char(result)
            print(f"  {task['condition']:<14}  {elapsed:5.1f}s  {status}")
            if status == "ERR" and task["condition"] == "bare":
                print("  ⚠  failed on bare — model may be down, skipping")
                break


def run_full(models: list[str], tasks: list[dict]) -> None:
    single = [t for t in tasks if not t["multiturn"]]
    multi = [t for t in tasks if t["multiturn"]]
    total = (len(single) + len(multi) * 2) * len(models)
    done = 0

    print(f"\nPressure eval — {len(single)} single-turn × 4 conditions + {len(multi)} chains × {len(models)} models")
    print("-" * 70)

    with OUTPUT_PATH.open("w") as out:
        for model in models:
            # Single-turn
            for task in single:
                done += 1
                messages = build_messages(task)
                result, elapsed = call_once(model, task, messages)
                status = status_char(result)
                print(f"  [{done:>3}]  {model:<20}  {task['condition']:<14}  {task['base_id']:<22}  {elapsed:5.1f}s  {status}")
                row = {
                    "task_id": task["id"], "base_id": task["base_id"],
                    "category": task["category"], "condition": task["condition"],
                    "model": model, "latency_s": round(elapsed, 2),
                    "expected_tool": task["expected_tool"],
                    "check_params": task["check_params"],
                    "expected_params": task["expected_params"],
                    "tools_available": task["tools"],
                    "turn": 1, "raw_response": result,
                }
                out.write(json.dumps(row) + "\n")

            # Multi-turn
            for task in multi:
                done += 2
                result1, result2, elapsed = call_multiturn(model, task)
                s1 = status_char(result1)
                s2 = status_char(result2) if result2 is not None else "ERR(no_turn2)"
                print(f"  [{done-1:>3}]  {model:<20}  {'multiturn_t1':<14}  {task['id']:<22}  {elapsed:5.1f}s  {s1} → {s2}")
                for turn_n, result, expected in [(1, result1, task["expected_tool"]), (2, result2, task["turn2_expected_tool"])]:
                    row = {
                        "task_id": f"{task['id']}_t{turn_n}", "base_id": task["id"],
                        "category": "multiturn", "condition": task["condition"],
                        "model": model, "latency_s": round(elapsed / 2, 2),
                        "expected_tool": expected,
                        "check_params": False, "expected_params": {},
                        "tools_available": task["tools"],
                        "turn": turn_n, "raw_response": result,
                    }
                    out.write(json.dumps(row) + "\n")

    print("-" * 70)
    print(f"  done → {OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--yes", "-y", action="store_true")
    args = parser.parse_args()

    try:
        requests.get(f"{PROXY}/v1/models", timeout=3)
    except Exception:
        print(f"ERROR: proxy not reachable at {PROXY}. Run: ./target/debug/lh up")
        sys.exit(1)

    if not TASKS_PATH.exists():
        print(f"ERROR: {TASKS_PATH} not found — run: python eval/pressure_corpus.py")
        sys.exit(1)

    tasks = json.loads(TASKS_PATH.read_text())
    print(f"Loaded {len(tasks)} pressure tasks")

    if args.smoke:
        run_smoke(args.models, tasks)
        return

    run_smoke(args.models, tasks)

    if not args.yes:
        ans = input("\nProceed with full run? [y/N] ").strip().lower()
        if ans != "y":
            print("Aborted.")
            sys.exit(0)

    run_full(args.models, tasks)


if __name__ == "__main__":
    main()
