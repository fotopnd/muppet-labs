#!/usr/bin/env python3
"""
Classify raw_outputs.jsonl into failure patterns.
Writes classified.jsonl with a `pattern` field added to each row.

Patterns (mutually exclusive, first match wins):
  ok               tool_calls present, correct name, expected params match
  schema_drift     tool_calls present but wrong function name or missing required params
  truncated        tool_calls present but arguments field is not valid JSON
  type_error       tool_calls correct but param value has wrong type vs expected
  hallucinated     tool_calls present but function name not in available tools
  wrap             no tool_calls, but content contains JSON resembling a tool call
  refusal          no tool_calls, content is plain prose or empty
  error            HTTP failure or no response
"""
import json
import sys
from pathlib import Path

INPUT = Path(__file__).parent / "raw_outputs.jsonl"
OUTPUT = Path(__file__).parent / "classified.jsonl"


def classify_one(row: dict) -> str:
    resp = row.get("raw_response")
    if resp is None or "error" in resp:
        return "error"

    choices = resp.get("choices", [])
    if not choices:
        return "error"

    message = choices[0].get("message", {})
    tool_calls = message.get("tool_calls")
    content = message.get("content") or ""
    available = set(row.get("tools_available", []))
    expected = row.get("expected_tool", "")
    check_params = row.get("check_params", False)
    expected_params = row.get("expected_params", {})

    # --- tool_calls path ---
    if tool_calls and isinstance(tool_calls, list) and tool_calls:
        tc = tool_calls[0]
        fn = tc.get("function", {})
        name = fn.get("name", "")
        raw_args = fn.get("arguments", "{}")

        if name not in available:
            return "hallucinated"

        if name != expected:
            return "schema_drift"

        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError:
            return "truncated"

        if check_params:
            for key, exp_val in expected_params.items():
                if key not in args:
                    return "schema_drift"
                if type(args[key]) is not type(exp_val):
                    return "type_error"

        return "ok"

    # --- content path: look for a tool call embedded in prose/JSON ---
    stripped = content.strip()

    # Strip markdown code fences
    if stripped.startswith("```"):
        inner = stripped.strip("`").strip()
        if inner.lower().startswith("json"):
            inner = inner[4:].strip()
        stripped = inner

    # Try parsing content as JSON
    try:
        parsed = json.loads(stripped)
        if isinstance(parsed, dict):
            has_name = "name" in parsed
            has_args = "arguments" in parsed or "parameters" in parsed
            if has_name or has_args:
                return "wrap"
    except (json.JSONDecodeError, ValueError):
        pass

    # Plain prose or empty
    return "refusal"


def main():
    if not INPUT.exists():
        print(f"ERROR: {INPUT} not found — run run_eval.py first")
        sys.exit(1)

    rows = [json.loads(line) for line in INPUT.read_text().splitlines() if line.strip()]
    classified = []
    counts: dict[str, int] = {}

    for row in rows:
        pattern = classify_one(row)
        row["pattern"] = pattern
        classified.append(row)
        counts[pattern] = counts.get(pattern, 0) + 1

    OUTPUT.write_text("\n".join(json.dumps(r) for r in classified) + "\n")

    print(f"Classified {len(classified)} results → {OUTPUT}")
    print()
    total = len(classified)
    for pat, n in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * int(n / total * 40)
        print(f"  {pat:<18} {n:>4}  {n/total*100:5.1f}%  {bar}")


if __name__ == "__main__":
    main()
