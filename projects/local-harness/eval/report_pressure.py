#!/usr/bin/env python3
"""
Report for context pressure eval.
Reads pressure_raw.jsonl (classify.py not needed — status is simpler here).
"""
import json
from collections import defaultdict
from pathlib import Path

INPUT = Path(__file__).parent / "pressure_raw.jsonl"
CONDITIONS = ["bare", "sysprompt", "context_sm", "context_lg", "context_sm"]  # last = multiturn


def classify(row: dict) -> str:
    resp = row.get("raw_response")
    if not resp or "error" in resp:
        return "error"
    choices = resp.get("choices", [])
    if not choices:
        return "error"
    msg = choices[0].get("message", {})
    tcs = msg.get("tool_calls")
    if tcs and isinstance(tcs, list) and tcs:
        fn = tcs[0].get("function", {})
        name = fn.get("name", "")
        expected = row.get("expected_tool", "")
        available = set(row.get("tools_available", []))
        if name not in available:
            return "hallucinated"
        if name != expected:
            return "schema_drift"
        raw_args = fn.get("arguments", "{}")
        try:
            json.loads(raw_args)
        except json.JSONDecodeError:
            return "truncated"
        return "ok"
    content = (msg.get("content") or "").strip().lstrip("`").strip()
    try:
        parsed = json.loads(content)
        if isinstance(parsed, dict) and ("name" in parsed or "arguments" in parsed):
            return "wrap"
    except Exception:
        pass
    return "refusal" if content else "error"


def pct(n, t):
    return f"{n/t*100:.0f}%" if t else "—"


def main():
    rows = [json.loads(l) for l in INPUT.read_text().splitlines() if l.strip()]
    for row in rows:
        row["pattern"] = classify(row)

    models = sorted(set(r["model"] for r in rows))
    model_short = {m: m.split(":")[0] for m in models}
    col_w = max(len(s) for s in model_short.values()) + 2

    print(f"\nContext pressure results — {len(rows)} calls\n")

    # ── Compliance by condition ──────────────────────────────────
    print("── Compliance by condition (% ok) ─────────────────────────")
    print(f"  {'condition':<16}", end="")
    for m in models:
        print(f"  {model_short[m]:>{col_w}}", end="")
    print()
    print("  " + "-" * (16 + (col_w + 2) * len(models)))

    single_conditions = ["bare", "sysprompt", "context_sm", "context_lg"]
    for cond in single_conditions:
        print(f"  {cond:<16}", end="")
        for m in models:
            subset = [r for r in rows if r["condition"] == cond and r["model"] == m and r["category"] != "multiturn"]
            n_ok = sum(1 for r in subset if r["pattern"] == "ok")
            print(f"  {pct(n_ok, len(subset)):>{col_w}}", end="")
        print()

    # Multi-turn rows
    print(f"  {'multiturn_t1':<16}", end="")
    for m in models:
        subset = [r for r in rows if r["category"] == "multiturn" and r["model"] == m and r["turn"] == 1]
        n_ok = sum(1 for r in subset if r["pattern"] == "ok")
        print(f"  {pct(n_ok, len(subset)):>{col_w}}", end="")
    print()

    print(f"  {'multiturn_t2':<16}", end="")
    for m in models:
        subset = [r for r in rows if r["category"] == "multiturn" and r["model"] == m and r["turn"] == 2]
        n_ok = sum(1 for r in subset if r["pattern"] == "ok")
        print(f"  {pct(n_ok, len(subset)):>{col_w}}", end="")
    print()

    # ── Failure patterns per model ───────────────────────────────
    print("\n── Failure breakdown (non-ok patterns, all single-turn conditions) ──")
    single_rows = [r for r in rows if r["category"] != "multiturn"]
    patterns = sorted(set(r["pattern"] for r in single_rows if r["pattern"] != "ok"))
    print(f"  {'pattern':<16}", end="")
    for m in models:
        print(f"  {model_short[m]:>{col_w}}", end="")
    print()
    print("  " + "-" * (16 + (col_w + 2) * len(models)))
    for pat in ["ok"] + patterns:
        print(f"  {pat:<16}", end="")
        for m in models:
            subset = [r for r in single_rows if r["model"] == m]
            n = sum(1 for r in subset if r["pattern"] == pat)
            t = len(subset)
            print(f"  {pct(n, t):>{col_w}}", end="")
        print()

    # ── Delta: bare → context_lg ─────────────────────────────────
    print("\n── Compliance delta: bare → context_lg ─────────────────────")
    for m in models:
        bare = [r for r in rows if r["condition"] == "bare" and r["model"] == m and r["category"] != "multiturn"]
        lg = [r for r in rows if r["condition"] == "context_lg" and r["model"] == m and r["category"] != "multiturn"]
        n_bare = sum(1 for r in bare if r["pattern"] == "ok")
        n_lg = sum(1 for r in lg if r["pattern"] == "ok")
        delta = (n_lg / len(lg) * 100 - n_bare / len(bare) * 100) if bare and lg else 0
        sign = "+" if delta >= 0 else ""
        print(f"  {model_short[m]:<20}  bare={pct(n_bare, len(bare))}  context_lg={pct(n_lg, len(lg))}  delta={sign}{delta:.0f}pp")

    print()


if __name__ == "__main__":
    main()
