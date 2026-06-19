"""Identify document_library coverage gaps for measurement.

Queries the live DB and outputs the card specs needed to reach
TARGET_CARDS_PER_TUPLE in every (harm_category, strategy, generation_model)
tuple. Emits a JSON manifest ready for hand-authoring or LLM generation.

Usage
-----
  uv run coverage-gaps                    # report only
  uv run coverage-gaps --json             # write gap_manifest.json
  uv run coverage-gaps --target 3         # target 3 cards/tuple (default 2)
  uv run coverage-gaps --cap 4            # flag tuples with > 4 cards
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import text

from year_zero.database import session_factory

# Standard model → tier mapping used throughout the seed library.
MODEL_TIER: dict[str, int] = {
    "gemma2:9b":    1,
    "qwen2.5:7b":   2,
    "llama3.1:8b":  3,
}

# GORK verdict logic by tier:
#   tier 1 — inverted: gork_verdict = NOT is_harmful (always wrong)
#   tier 2 — semi-correct: gork_verdict = is_harmful (but confidence ~0.55–0.70)
#   tier 3 — mostly correct: gork_verdict = is_harmful (confidence ~0.75–0.92)

PHASE_MIX = {"none": 0.10, "tier_1": 0.48, "tier_2": 0.21, "tier_3": 0.21}

OUT_PATH = Path(__file__).parent / "gap_manifest.json"


def gork_verdict_for(generation_tier: int, is_harmful: bool) -> bool:
    if generation_tier == 1:
        return not is_harmful   # inverted — always wrong
    return is_harmful           # tier 2/3 — correct


def gork_confidence_for(generation_tier: int) -> tuple[float, float]:
    """Return (lo, hi) confidence range to guide hand-authoring."""
    if generation_tier == 1:
        return (0.60, 0.82)
    if generation_tier == 2:
        return (0.52, 0.72)
    return (0.72, 0.93)


async def fetch_tuples() -> list[dict]:
    """Return one row per (harm_category, strategy, generation_model) tuple."""
    async with session_factory() as db:
        rows = (await db.execute(text("""
            SELECT
                harm_category,
                strategy,
                generation_model,
                COUNT(*)                                         AS n,
                SUM(CASE WHEN is_harmful     THEN 1 ELSE 0 END) AS n_harmful,
                SUM(CASE WHEN NOT is_harmful THEN 1 ELSE 0 END) AS n_benign
            FROM document_library
            GROUP BY harm_category, strategy, generation_model
            ORDER BY harm_category, strategy, generation_model
        """))).fetchall()

    return [
        {
            "harm_category":    r[0],
            "strategy":         r[1],
            "generation_model": r[2],
            "n":                r[3],
            "n_harmful":        r[4],
            "n_benign":         r[5],
        }
        for r in rows
    ]


def build_gap_specs(
    tuples: list[dict],
    target: int,
    cap: int,
) -> tuple[list[dict], list[dict]]:
    """Return (gap_specs, over_cap_tuples)."""
    gaps: list[dict] = []
    over: list[dict] = []

    for t in tuples:
        cat   = t["harm_category"]
        strat = t["strategy"]
        model = t["generation_model"]
        n     = t["n"]
        tier  = MODEL_TIER.get(model, 2)

        if n > cap:
            over.append({**t, "excess": n - cap})

        needed = max(0, target - n)
        if needed == 0:
            continue

        # Determine is_harmful for each gap card to balance within tuple.
        # Start from the under-represented label.
        nh, nb = t["n_harmful"], t["n_benign"]
        for _ in range(needed):
            # Always fill the smaller bucket first.
            is_harmful = (nh <= nb)
            gv         = gork_verdict_for(tier, is_harmful)
            conf_lo, conf_hi = gork_confidence_for(tier)
            gaps.append({
                "harm_category":    cat,
                "strategy":         strat,
                "generation_model": model,
                "generation_tier":  tier,
                "is_harmful":       is_harmful,
                "gork_verdict":     gv,
                "verdict_correct":  (gv == is_harmful),
                "gork_confidence_range": [conf_lo, conf_hi],
                "target_condition_mix": PHASE_MIX,
                "phase": 1,
                "is_calibration": False,
                "needs_review": False,
            })
            if is_harmful:
                nh += 1
            else:
                nb += 1

    return gaps, over


def print_report(
    tuples: list[dict],
    gaps: list[dict],
    over: list[dict],
    target: int,
    cap: int,
) -> None:
    total   = sum(t["n"] for t in tuples)
    n_short = sum(1 for t in tuples if t["n"] < target)

    print(f"\n{'─'*72}")
    print(f"  Coverage report — target {target} cards/tuple, cap {cap}")
    print(f"  Pool: {total} cards across {len(tuples)} tuples")
    print(f"  Tuples below target ({target}): {n_short} / {len(tuples)}")
    print(f"  Gap cards needed: {len(gaps)}")
    print(f"{'─'*72}")

    # Per-tuple table
    print(f"\n  {'category':<22}  {'attack':<22}  {'model':<14}  {'n':>3}  {'H':>2}  {'B':>2}  {'gap':>4}")
    print(f"  {'─'*22}  {'─'*22}  {'─'*14}  {'─'*3}  {'─'*2}  {'─'*2}  {'─'*4}")
    for t in sorted(tuples, key=lambda x: x["n"]):
        gap      = max(0, target - t["n"])
        flag     = " ▲" if t["n"] > cap else ("  !" if gap > 0 else "")
        model_s  = t["generation_model"].split(":")[0]
        strat_s  = t["strategy"][:22]
        print(f"  {t['harm_category']:<22}  {strat_s:<22}  {model_s:<14}  {t['n']:>3}  {t['n_harmful']:>2}  {t['n_benign']:>2}  {gap:>4}{flag}")

    if over:
        print(f"\n  Over-cap tuples (>{cap} cards) — consider archiving excess:")
        for t in over:
            model_s = t["generation_model"].split(":")[0]
            print(f"    {t['harm_category']} / {t['strategy']} / {model_s}  →  {t['n']} cards ({t['excess']} over cap)")

    print()

    # Gap summary by model
    by_model: dict[str, int] = {}
    for g in gaps:
        by_model[g["generation_model"]] = by_model.get(g["generation_model"], 0) + 1
    if by_model:
        print("  Gap cards by model:")
        for model, count in sorted(by_model.items()):
            print(f"    {model:<16} {count:>3} cards to write")

    # Gap summary by category
    by_cat: dict[str, int] = {}
    for g in gaps:
        by_cat[g["harm_category"]] = by_cat.get(g["harm_category"], 0) + 1
    if by_cat:
        print("  Gap cards by category:")
        for cat, count in sorted(by_cat.items(), key=lambda x: -x[1]):
            print(f"    {cat:<26} {count:>3} cards to write")

    print(f"\n  Total: {len(gaps)} gap cards → pool size after fill: {total + len(gaps)}")
    print(f"{'─'*72}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Coverage gap analysis for document_library")
    parser.add_argument("--target", type=int, default=2,
                        help="Target cards per tuple (default: 2)")
    parser.add_argument("--cap", type=int, default=4,
                        help="Flag tuples with more than this many cards (default: 4)")
    parser.add_argument("--json", action="store_true",
                        help=f"Write gap manifest to {OUT_PATH}")
    args = parser.parse_args()

    try:
        tuples = asyncio.run(fetch_tuples())
    except Exception as exc:
        print(f"ERROR: Could not reach database — {exc}", file=sys.stderr)
        sys.exit(1)

    if not tuples:
        print("No cards found. Run `uv run seed-library` first.", file=sys.stderr)
        sys.exit(1)

    gaps, over = build_gap_specs(tuples, target=args.target, cap=args.cap)
    print_report(tuples, gaps, over, target=args.target, cap=args.cap)

    if args.json:
        manifest = {
            "target_per_tuple": args.target,
            "gap_count": len(gaps),
            "over_cap_count": len(over),
            "over_cap_tuples": over,
            "gap_specs": gaps,
        }
        OUT_PATH.write_text(json.dumps(manifest, indent=2))
        print(f"  Manifest written to {OUT_PATH}\n")


if __name__ == "__main__":
    main()
