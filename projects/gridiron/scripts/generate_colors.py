#!/usr/bin/env python3
"""
generate_colors.py — Algorithmically assign primary colors to all 130 programs.

Strategy:
  1. Build a dense grid of Lab colors filtered to valid sRGB.
  2. Per conglomerate, define a "preference region" (lightness band + hue bias)
     that gives the network its broadcast character.
  3. Use farthest-point sampling to select 26 maximally-separated colors
     from that region (guarantees ΔE₇₆ ≥ TARGET_DE between all pairs).
  4. Shuffle-assign to programs (preserving existing secondary colors).
  5. Patch the Brand tables in UNIVERSE-SEEDING.md in place.

Usage:
    uv run scripts/generate_colors.py           # dry-run (print only)
    uv run scripts/generate_colors.py --write   # patch the file
    uv run scripts/generate_colors.py --seed 42 # reproducible assignment
"""

from __future__ import annotations

import argparse
import math
import random
import re
import sys
from pathlib import Path

SEEDING_MD = Path(__file__).parent.parent / "_config" / "UNIVERSE-SEEDING.md"
TARGET_DE = 30.0
GRID_STEP = 4  # Lab grid resolution — finer = more candidates, slower

# Note: step=4 yields ~12k unique sRGB candidates; step=2 yields ~85k (slower build,
# useful if a preference region has < 3000 candidates after filtering).

# ── Color math ────────────────────────────────────────────────────────────────


def _linearise(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _delinearise(c: float) -> float:
    return c * 12.92 if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.strip().lstrip("#")
    return int(h[0:2], 16) / 255, int(h[2:4], 16) / 255, int(h[4:6], 16) / 255


def _f(t: float) -> float:
    return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116


def _finv(t: float) -> float:
    return t**3 if t > 0.206897 else (t - 16 / 116) / 7.787


def rgb_to_lab(r: float, g: float, b: float) -> tuple[float, float, float]:
    r, g, b = _linearise(r), _linearise(g), _linearise(b)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    fx, fy, fz = _f(x / xn), _f(y / yn), _f(z / zn)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def lab_to_hex(L: float, a: float, b: float) -> str | None:
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    fy = (L + 16) / 116
    fx = a / 500 + fy
    fz = fy - b / 200
    x = _finv(fx) * xn
    y = _finv(fy) * yn
    z = _finv(fz) * zn
    # XYZ → linear sRGB
    r =  x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g =  x * -0.9692660 + y * 1.8760108 + z *  0.0415560
    bv = x *  0.0556434 + y * -0.2040259 + z *  1.0572252
    if any(c < -0.001 or c > 1.001 for c in (r, g, bv)):
        return None
    r, g, bv = (_delinearise(max(0.0, min(1.0, c))) for c in (r, g, bv))
    return "#{:02X}{:02X}{:02X}".format(int(r * 255), int(g * 255), int(bv * 255))


def delta_e76(lab1: tuple, lab2: tuple) -> float:
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


# ── Candidate grid ────────────────────────────────────────────────────────────


def build_candidate_grid(step: int = GRID_STEP) -> list[tuple[float, float, float, str]]:
    """Return list of (L*, a*, b*, hex) for all valid sRGB points on the Lab grid.

    Lab coordinates are QUANTIZED from hex (hex → rgb → lab) so that ΔE computed
    here matches exactly what verify_colors.py will compute from the same hex string.
    Deduplicates by hex — multiple grid Lab points that round to the same 8-bit hex
    are kept only once to prevent the farthest-point algorithm from assigning the
    same visible color to two programs.
    """
    seen: set[str] = set()
    candidates = []
    for li in range(10, 91, step):
        for ai in range(-80, 81, step):
            for bi in range(-80, 81, step):
                h = lab_to_hex(float(li), float(ai), float(bi))
                if h is None or h in seen:
                    continue
                seen.add(h)
                # Re-derive Lab from the actual hex so ΔE matches verify_colors.py
                lab = rgb_to_lab(*hex_to_rgb(h))
                candidates.append((*lab, h))
    return candidates


# ── Conglomerate aesthetic preferences ───────────────────────────────────────
# Each entry: (L_min, L_max, a_min, a_max, b_min, b_max, description)
# These are soft preference windows — farthest-point sampling happens WITHIN
# the filtered set, so colors will be spread across the full preference region.

CONGLOMERATE_PREFS: dict[str, tuple] = {
    # L 18–82 on all conglomerates: avoids near-black (obscured on dark BG) and
    # near-white (obscured on light BG). Bias is on the a/b axes only.
    #
    # Cool: excludes warm yellows (b > 45); all blues, purples, greens, teals in range.
    "NCC": (18, 82, -80, 80, -80, 45, "cool: navy · teal · indigo · slate · medium blue"),
    # Warm vivid: excludes cool pure blues (a < -30, b < -35); warm/vivid half.
    "SBC": (18, 82, -30, 80, -35, 80, "warm vivid: crimson · gold · amber · deep green"),
    # Prestige dark: full hue range, L capped at 70 for richer/darker aesthetic.
    "ACA": (18, 70, -80, 80, -80, 80, "prestige dark: full hue range · medium-dark"),
    # Traditional/earthy: includes slate + warm neutrals (b ≥ -32); broader than before.
    "MCC": (18, 82, -50, 80, -32, 80, "traditional: gold · burgundy · earth · slate"),
    # Patriotic: broad; excludes pure warm yellow only (b > 60).
    "UAC": (18, 82, -80, 80, -80, 60, "patriotic: red · navy · silver · regional"),
}

# ── Conglomerate brand secondary colors ───────────────────────────────────────
# Each team's secondary is the conglomerate broadcast network's accent color.
# This reinforces network identity and guarantees primary ≠ secondary.
# Sources: resources/writing-voice.md Brand Palettes section.

CONGLOMERATE_SECONDARY: dict[str, str] = {
    "NCC": "#00F0FF",  # TCB High-Contrast Cyan
    "SBC": "#FFD700",  # ISG High-Visibility Yellow
    "ACA": "#C5A059",  # STN Burnished Gold
    "MCC": "#2F4F4F",  # CHBA Dark Slate
    "UAC": "#CD2626",  # FPC Stadium Red
}


def filter_candidates(
    candidates: list[tuple[float, float, float, str]],
    L_min: float, L_max: float,
    a_min: float, a_max: float,
    b_min: float, b_max: float,
) -> list[tuple[float, float, float, str]]:
    return [
        c for c in candidates
        if L_min <= c[0] <= L_max and a_min <= c[1] <= a_max and b_min <= c[2] <= b_max
    ]


# ── Farthest-point sampling ───────────────────────────────────────────────────


def farthest_point_sample(
    candidates: list[tuple[float, float, float, str]],
    n: int,
    seed_color: tuple[float, float, float, str] | None = None,
    rng: random.Random | None = None,
) -> list[tuple[float, float, float, str]]:
    """
    Greedy farthest-point sampling: iteratively pick the candidate that
    maximises minimum distance to all already-selected colors.
    Guarantees pairwise ΔE ≥ the smallest gap in the selected set.
    """
    if rng is None:
        rng = random.Random(0)
    if not candidates:
        raise ValueError("No candidates in preference region — widen the filter.")

    pool = list(candidates)
    selected: list[tuple[float, float, float, str]] = []

    if seed_color is None:
        # Start from a random corner of the preference region
        seed_color = rng.choice(pool)
    selected.append(seed_color)
    pool.remove(seed_color)

    # min_dist[i] = minimum ΔE from pool[i] to any selected color
    min_dists = [delta_e76(c[:3], selected[0][:3]) for c in pool]

    for _ in range(n - 1):
        # Pick the candidate with the largest minimum distance to selected set
        best_idx = max(range(len(pool)), key=lambda i: min_dists[i])
        chosen = pool.pop(best_idx)
        selected.append(chosen)
        # Update min_dists for remaining pool
        chosen_lab = chosen[:3]
        del min_dists[best_idx]
        for i, c in enumerate(pool):
            d = delta_e76(c[:3], chosen_lab)
            if d < min_dists[i]:
                min_dists[i] = d

    return selected


# ── Markdown parser / patcher ─────────────────────────────────────────────────

_ROW_RE = re.compile(r"^(\|\s*)([^|]+?)(\s*\|\s*)`(#[0-9A-Fa-f]{6})`(\s*\|\s*)`(#[0-9A-Fa-f]{6})`(.*)")
_HEADER_RE = re.compile(r"^####\s+(NCC|SBC|ACA|MCC|UAC)\s*[—-]")
CONFS = ["NCC", "SBC", "ACA", "MCC", "UAC"]


def parse_brand_rows(path: Path) -> dict[str, list[tuple[int, str, str, str]]]:
    """Return {conf: [(line_idx, name, primary, secondary), ...]}"""
    data: dict[str, list] = {c: [] for c in CONFS}
    current: str | None = None
    in_brand = False
    lines = path.read_text().splitlines()

    for i, line in enumerate(lines):
        m = _HEADER_RE.match(line)
        if m:
            current = m.group(1)
            in_brand = False
            continue
        if "**Brand**" in line or "Brand** " in line:
            in_brand = True
            continue
        if current and in_brand:
            rm = _ROW_RE.match(line)
            if rm:
                name = rm.group(2).strip()
                if name.lower() not in ("fictional name", "---") and not name.startswith("-"):
                    data[current].append((i, name, rm.group(4), rm.group(6)))

    return data


def patch_file(path: Path, replacements: dict[int, tuple[str, str]]) -> str:
    """Return patched file content. replacements: {line_idx: (new_primary, new_secondary)}"""
    lines = path.read_text().splitlines(keepends=True)
    for idx, (new_primary, new_secondary) in replacements.items():
        line = lines[idx]
        # Replace both hex values in one pass using a lambda to avoid
        # the second sub clobbering the first replacement.
        # Matches: `#XXXXXX` <separator> `#YYYYYY`
        line = re.sub(
            r"(`#[0-9A-Fa-f]{6}`)(\s*\|\s*)(`#[0-9A-Fa-f]{6}`)",
            lambda m, p=new_primary, s=new_secondary: f"`{p}`{m.group(2)}`{s}`",
            line,
            count=1,
        )
        lines[idx] = line
    return "".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────


def run(write: bool = False, seed: int = 0) -> int:
    rng = random.Random(seed)

    print("\nBuilding Lab color grid…", end=" ", flush=True)
    candidates = build_candidate_grid(GRID_STEP)
    print(f"{len(candidates):,} valid sRGB points")

    brand_rows = parse_brand_rows(SEEDING_MD)
    replacements: dict[int, tuple[str, str]] = {}

    overall_ok = True

    for conf in CONFS:
        rows = brand_rows[conf]
        if not rows:
            print(f"  {conf}: ⚠️  no brand rows found — skipping")
            continue

        L_min, L_max, a_min, a_max, b_min, b_max, desc = CONGLOMERATE_PREFS[conf]
        pool = filter_candidates(candidates, L_min, L_max, a_min, a_max, b_min, b_max)

        print(f"\n  {conf}  ({desc})")
        print(f"    Preference region: {len(pool):,} candidates  →  selecting {len(rows)} colors")

        if len(pool) < len(rows):
            print(f"    ❌ Not enough candidates ({len(pool)} < {len(rows)}) — widen preference region")
            overall_ok = False
            continue

        # Shuffle pool so seed affects which branch of equal-distance candidates wins
        rng.shuffle(pool)
        selected = farthest_point_sample(pool, len(rows), rng=rng)

        # Shuffle assignment so program order doesn't bias color allocation
        assignment = list(selected)
        rng.shuffle(assignment)

        # Verify minimum pairwise ΔE in the selected set
        min_de = float("inf")
        worst_pair: tuple = ("", "")
        for i in range(len(selected)):
            for j in range(i + 1, len(selected)):
                de = delta_e76(selected[i][:3], selected[j][:3])
                if de < min_de:
                    min_de = de
                    worst_pair = (selected[i][3], selected[j][3])

        status = "✅" if min_de >= TARGET_DE else "⚠️ "
        print(f"    {status} min ΔE = {min_de:.1f}  (worst pair: {worst_pair[0]} × {worst_pair[1]})")
        if min_de < TARGET_DE:
            overall_ok = False

        new_secondary = CONGLOMERATE_SECONDARY[conf]
        for (line_idx, name, old_primary, old_secondary), color in zip(rows, assignment):
            new_hex = color[3]
            replacements[line_idx] = (new_hex, new_secondary)
            if not write:
                primary_changed = old_primary.upper() != new_hex.upper()
                secondary_changed = old_secondary.upper() != new_secondary.upper()
                if primary_changed or secondary_changed:
                    print(f"    {name[:32]:<32}  {old_primary} → {new_hex}  |  sec {old_secondary} → {new_secondary}")

    if write:
        patched = patch_file(SEEDING_MD, replacements)
        SEEDING_MD.write_text(patched)
        print(f"\n  ✅ Patched {SEEDING_MD.name} ({len(replacements)} programs updated — primary + conglomerate secondary)")
        print("  Run verify_colors.py to confirm.\n")
    else:
        total_changes = sum(
            1 for (line_idx, _, old_p, _) in [r for rows in brand_rows.values() for r in rows]
            if line_idx in replacements and replacements[line_idx][0].upper() != old_p.upper()
        )
        print(f"\n  Dry run — {total_changes} primaries would change. Pass --write to apply.\n")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Patch UNIVERSE-SEEDING.md in place")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed for reproducibility")
    args = parser.parse_args()
    sys.exit(run(write=args.write, seed=args.seed))
