#!/usr/bin/env python3
"""
Generate the Phase 1 frequency table from classified.jsonl.

Outputs:
  - Pattern × model breakdown
  - Pattern × category breakdown
  - Top failure patterns overall
"""
import json
from collections import defaultdict
from pathlib import Path

INPUT = Path(__file__).parent / "classified.jsonl"

PATTERNS = ["ok", "wrap", "schema_drift", "truncated", "type_error", "hallucinated", "refusal", "error"]


def load() -> list[dict]:
    if not INPUT.exists():
        raise FileNotFoundError(f"{INPUT} not found — run classify.py first")
    return [json.loads(l) for l in INPUT.read_text().splitlines() if l.strip()]


def table(rows: list[dict], row_key: str, col_key: str, patterns: list[str]) -> None:
    """Print a cross-tab of row_key × col_key, values are pattern counts."""
    row_vals = sorted(set(r[row_key] for r in rows))
    col_vals = sorted(set(r[col_key] for r in rows))

    # counts[row][col][pattern]
    counts: dict = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    totals: dict = defaultdict(lambda: defaultdict(int))
    for r in rows:
        counts[r[row_key]][r[col_key]][r["pattern"]] += 1
        totals[r[row_key]][r[col_key]] += 1

    col_w = max(len(v) for v in col_vals) + 2

    # Header
    print(f"  {row_key:<22}", end="")
    for col in col_vals:
        print(f"  {col:>{col_w}}", end="")
    print()
    print("  " + "-" * (22 + (col_w + 2) * len(col_vals)))

    for rval in row_vals:
        print(f"  {rval:<22}", end="")
        for col in col_vals:
            n = counts[rval][col].get("ok", 0)
            t = totals[rval][col]
            if t == 0:
                print(f"  {'—':>{col_w}}", end="")
            else:
                pct = int(n / t * 100)
                print(f"  {f'{pct}% ok ({t})':>{col_w}}", end="")
        print()


def pattern_breakdown(rows: list[dict]) -> None:
    models = sorted(set(r["model"] for r in rows))
    counts: dict = defaultdict(lambda: defaultdict(int))
    totals: dict = defaultdict(int)

    for r in rows:
        counts[r["model"]][r["pattern"]] += 1
        totals[r["model"]] += 1

    col_w = max(len(m) for m in models) + 2
    print(f"  {'pattern':<18}", end="")
    for m in models:
        short = m.split(":")[0]
        print(f"  {short:>{col_w}}", end="")
    print(f"  {'overall':>{col_w}}")
    print("  " + "-" * (18 + (col_w + 2) * (len(models) + 1)))

    overall: dict[str, int] = defaultdict(int)
    grand_total = len(rows)
    for r in rows:
        overall[r["pattern"]] += 1

    for pat in PATTERNS:
        if not any(counts[m].get(pat, 0) for m in models):
            continue
        print(f"  {pat:<18}", end="")
        for m in models:
            n = counts[m].get(pat, 0)
            t = totals[m]
            pct = f"{n/t*100:.0f}%" if t else "—"
            print(f"  {pct:>{col_w}}", end="")
        n_all = overall.get(pat, 0)
        pct_all = f"{n_all/grand_total*100:.0f}%"
        print(f"  {pct_all:>{col_w}}")


def main():
    rows = load()
    print(f"\nPhase 1 results — {len(rows)} calls\n")

    print("── Pattern breakdown by model ──────────────────────────────")
    pattern_breakdown(rows)

    print()
    print("── Success rate by category ────────────────────────────────")
    cats = sorted(set(r["category"] for r in rows))
    models = sorted(set(r["model"] for r in rows))
    col_w = max(len(m.split(":")[0]) for m in models) + 2
    print(f"  {'category':<14}", end="")
    for m in models:
        print(f"  {m.split(':')[0]:>{col_w}}", end="")
    print()
    print("  " + "-" * (14 + (col_w + 2) * len(models)))
    for cat in cats:
        print(f"  {cat:<14}", end="")
        for m in models:
            subset = [r for r in rows if r["category"] == cat and r["model"] == m]
            n_ok = sum(1 for r in subset if r["pattern"] == "ok")
            pct = f"{n_ok/len(subset)*100:.0f}%" if subset else "—"
            print(f"  {pct:>{col_w}}", end="")
        print()

    # Fixable vs not
    fixable = {"wrap", "truncated", "type_error"}
    n_fixable = sum(1 for r in rows if r["pattern"] in fixable)
    n_unfixable = sum(1 for r in rows if r["pattern"] in {"hallucinated", "refusal", "schema_drift"})
    n_ok = sum(1 for r in rows if r["pattern"] == "ok")

    print()
    print("── Repair opportunity ──────────────────────────────────────")
    print(f"  ok              {n_ok:>4}  ({n_ok/len(rows)*100:.0f}%)")
    print(f"  fixable in proxy {n_fixable:>4}  ({n_fixable/len(rows)*100:.0f}%)  wrap / truncated / type_error")
    print(f"  model limitation {n_unfixable:>4}  ({n_unfixable/len(rows)*100:.0f}%)  refusal / hallucinated / schema_drift")
    print()


if __name__ == "__main__":
    main()
