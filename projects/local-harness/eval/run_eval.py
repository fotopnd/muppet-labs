#!/usr/bin/env python3
"""
Phase 1 eval runner.

Usage:
  python eval/run_eval.py --smoke               # 5 tasks × 1 model, time projection
  python eval/run_eval.py                       # full run after smoke confirms estimate
  python eval/run_eval.py --models qwen2.5-coder:7b
"""
import argparse
import json
import sys
import time
from pathlib import Path

import requests

PROXY = "http://localhost:8080"
DEFAULT_MODELS = ["qwen2.5-coder:7b", "gemma2:9b"]
CORPUS_PATH = Path(__file__).parent / "corpus.json"
OUTPUT_PATH = Path(__file__).parent / "raw_outputs.jsonl"

TOOL_SCHEMAS = {
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the full contents of a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"}
                },
                "required": ["path"]
            }
        }
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file, creating it if it does not exist.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    "run_command": {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Run a shell command and return its output.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cmd": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["cmd"]
            }
        }
    },
    "search_files": {
        "type": "function",
        "function": {
            "name": "search_files",
            "description": "Search for files matching a pattern in a directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob or search pattern"},
                    "directory": {"type": "string", "description": "Directory to search in"}
                },
                "required": ["pattern", "directory"]
            }
        }
    }
}


def call(model: str, task: dict, timeout: int = 120) -> tuple[dict | None, float]:
    tools = [TOOL_SCHEMAS[t] for t in task["tools"]]
    payload = {
        "model": model,
        "stream": False,
        "tools": tools,
        "messages": [{"role": "user", "content": task["prompt"]}]
    }
    t0 = time.time()
    try:
        resp = requests.post(f"{PROXY}/v1/chat/completions", json=payload, timeout=timeout)
        elapsed = time.time() - t0
        if resp.ok:
            return resp.json(), elapsed
        else:
            return {"error": resp.text, "status": resp.status_code}, elapsed
    except Exception as e:
        elapsed = time.time() - t0
        return {"error": str(e)}, elapsed


def status_char(result: dict | None) -> str:
    if result is None or "error" in result:
        return "ERR(network)"
    choices = result.get("choices", [])
    if not choices:
        return "ERR(no choices)"
    msg = choices[0].get("message", {})
    tool_calls = msg.get("tool_calls")
    if tool_calls and isinstance(tool_calls, list) and tool_calls:
        return "ok"
    content = msg.get("content", "") or ""
    stripped = content.strip().lstrip("`").strip()
    try:
        parsed = json.loads(stripped)
        if "name" in parsed or "function" in parsed or "arguments" in parsed:
            return "ERR(wrap)"
    except Exception:
        pass
    if content.strip():
        return "ERR(refusal)"
    return "ERR(empty)"


def run_smoke(models: list[str]) -> dict[str, float]:
    """Run 5 tasks against each model, print results, return avg latency per model."""
    corpus = json.loads(CORPUS_PATH.read_text())
    tasks = corpus[:5]
    avgs: dict[str, float] = {}

    for model in models:
        print(f"\nSmoke test — {model}")
        print("-" * 60)
        latencies = []
        ok = True
        for i, task in enumerate(tasks, 1):
            result, elapsed = call(model, task)
            latencies.append(elapsed)
            status = status_char(result)
            print(f"  {i}/{len(tasks)}  {task['id']:<30}  {elapsed:5.1f}s  {status}")
            if "error" in status.lower() and i == 1:
                print(f"  ⚠  first call failed — model may not support tools, skipping remaining")
                ok = False
                break

        avg = sum(latencies) / len(latencies)
        avgs[model] = avg
        lo = int(len(corpus) * avg / 60)
        hi = int(len(corpus) * avg * 1.4 / 60)
        flag = " ⚠  check errors above" if not ok else ""
        print(f"  avg {avg:.1f}s/call → est. {lo}–{hi} min for 40 tasks{flag}")

    total_calls = len(corpus) * len(models)
    total_avg = sum(avgs.values()) / len(avgs)
    lo = int(total_calls * total_avg / 60)
    hi = int(total_calls * total_avg * 1.4 / 60)
    print(f"\n  total: {total_calls} calls across {len(models)} models → est. {lo}–{hi} min\n")

    return avgs


def run_full(models: list[str]) -> None:
    corpus = json.loads(CORPUS_PATH.read_text())
    total = len(corpus) * len(models)
    done = 0

    print(f"\nFull eval — {len(corpus)} tasks × {len(models)} models = {total} calls")
    print("-" * 60)

    with OUTPUT_PATH.open("w") as out:
        for model in models:
            for task in corpus:
                done += 1
                result, elapsed = call(model, task)
                status = status_char(result)
                print(f"  [{done:>3}/{total}]  {model}  {task['id']:<30}  {elapsed:5.1f}s  {status}")

                row = {
                    "task_id": task["id"],
                    "category": task["category"],
                    "model": model,
                    "latency_s": round(elapsed, 2),
                    "expected_tool": task["expected_tool"],
                    "check_params": task["check_params"],
                    "expected_params": task["expected_params"],
                    "tools_available": task["tools"],
                    "raw_response": result,
                }
                out.write(json.dumps(row) + "\n")

    print("-" * 60)
    print(f"  done → {OUTPUT_PATH}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run smoke test only (5 tasks × 1 model)")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="Models to test")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation after smoke test")
    args = parser.parse_args()

    # Confirm proxy is up
    try:
        requests.get(f"{PROXY}/v1/models", timeout=3)
    except Exception:
        print(f"ERROR: proxy not reachable at {PROXY}")
        print("Run:  ./target/debug/lh up")
        sys.exit(1)

    if args.smoke:
        run_smoke(args.models)
        return

    # Always run smoke first, then ask
    avgs = run_smoke(args.models)
    _ = avgs  # used for display only

    if not args.yes:
        ans = input("Proceed with full run? [y/N] ").strip().lower()
        if ans != "y":
            print("Aborted.")
            sys.exit(0)

    run_full(args.models)


if __name__ == "__main__":
    main()
