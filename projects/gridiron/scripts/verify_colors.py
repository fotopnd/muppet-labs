#!/usr/bin/env python3
"""
verify_colors.py — Verify perceptual color distance between program primaries.

Rules checked:
  1. Intra-conglomerate: ΔE₇₆ ≥ 30 between every pair of programs in the same conglomerate.
  2. Cross-conglomerate: informational summary only (no hard constraint).

ΔE₇₆ uses CIE 1976 (L*a*b*) distance: sqrt((ΔL*)² + (Δa*)² + (Δb*)²).
Accurate enough for our threshold — CIEDE2000 improvements matter most below ΔE 10.

Usage:
    uv run scripts/verify_colors.py
    uv run scripts/verify_colors.py --threshold 25   # relax threshold for drafting

Parses colors directly from _config/UNIVERSE-SEEDING.md brand tables.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from pathlib import Path

SEEDING_MD = Path(__file__).parent.parent / "_config" / "UNIVERSE-SEEDING.md"
DEFAULT_THRESHOLD = 30.0

CONGLOMERATE_HEADERS = ["NCC", "SBC", "ACA", "MCC", "UAC"]


# ── Color math ────────────────────────────────────────────────────────────────


def hex_to_rgb(h: str) -> tuple[float, float, float]:
    h = h.strip().lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return r / 255.0, g / 255.0, b / 255.0


def _linearise(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def rgb_to_xyz(r: float, g: float, b: float) -> tuple[float, float, float]:
    r, g, b = _linearise(r), _linearise(g), _linearise(b)
    # sRGB → XYZ D65 (IEC 61966-2-1)
    x = r * 0.4124564 + g * 0.3575761 + b * 0.1804375
    y = r * 0.2126729 + g * 0.7151522 + b * 0.0721750
    z = r * 0.0193339 + g * 0.1191920 + b * 0.9503041
    return x, y, z


def _f(t: float) -> float:
    return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116


def xyz_to_lab(x: float, y: float, z: float) -> tuple[float, float, float]:
    # D65 white point
    xn, yn, zn = 0.95047, 1.00000, 1.08883
    fx, fy, fz = _f(x / xn), _f(y / yn), _f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b = 200 * (fy - fz)
    return L, a, b


def delta_e76(hex1: str, hex2: str) -> float:
    lab1 = xyz_to_lab(*rgb_to_xyz(*hex_to_rgb(hex1)))
    lab2 = xyz_to_lab(*rgb_to_xyz(*hex_to_rgb(hex2)))
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(lab1, lab2)))


# ── Markdown parser ───────────────────────────────────────────────────────────

# Matches brand table rows: | Name | `#RRGGBB` | `#RRGGBB` | ... |
_ROW = re.compile(r"^\|\s*([^|]+?)\s*\|\s*`(#[0-9A-Fa-f]{6})`\s*\|\s*`(#[0-9A-Fa-f]{6})`")
# Matches conglomerate section headers: #### NCC — ...
_HEADER = re.compile(r"^####\s+(NCC|SBC|ACA|MCC|UAC)\s*[—-]")


def parse_programs(path: Path) -> dict[str, list[tuple[str, str, str]]]:
    """Return {conglomerate: [(name, primary_hex, secondary_hex), ...]}."""
    data: dict[str, list[tuple[str, str, str]]] = {k: [] for k in CONGLOMERATE_HEADERS}
    current: str | None = None
    in_brand = False

    for line in path.read_text().splitlines():
        m = _HEADER.match(line)
        if m:
            current = m.group(1)
            in_brand = False
            continue

        if "**Brand**" in line or "Brand** " in line:
            in_brand = True
            continue

        # Reset when we hit the next section header at same level
        if line.startswith("####") and not _HEADER.match(line):
            in_brand = False

        if current and in_brand:
            rm = _ROW.match(line)
            if rm:
                name, primary, secondary = rm.group(1).strip(), rm.group(2), rm.group(3)
                # Skip header rows
                if name.lower() not in ("fictional name", "---"):
                    data[current].append((name, primary, secondary))

    return data


# ── Report ────────────────────────────────────────────────────────────────────


def run(threshold: float = DEFAULT_THRESHOLD) -> int:
    programs = parse_programs(SEEDING_MD)

    total_pairs = 0
    total_violations = 0

    all_violations: list[tuple[str, str, str, str, str, float]] = []

    print(f"\n{'═' * 68}")
    print(f"  Gridiron Color Verification  |  ΔE₇₆ threshold: {threshold}")
    print(f"{'═' * 68}\n")

    for conf in CONGLOMERATE_HEADERS:
        progs = programs[conf]
        if not progs:
            print(f"  {conf}: no programs found — check parsing\n")
            continue

        violations: list[tuple[str, str, str, str, float]] = []
        pairs = 0

        for i, (n1, p1, _) in enumerate(progs):
            for n2, p2, _ in progs[i + 1 :]:
                de = delta_e76(p1, p2)
                pairs += 1
                if de < threshold:
                    violations.append((n1, p1, n2, p2, de))
                    all_violations.append((conf, n1, p1, n2, p2, de))

        total_pairs += pairs
        total_violations += len(violations)

        status = "✅ PASS" if not violations else f"❌ FAIL ({len(violations)} pair{'s' if len(violations) != 1 else ''})"
        print(f"  {conf}  {status}  ({pairs} pairs checked, {len(progs)} programs)")

        if violations:
            violations.sort(key=lambda x: x[4])
            for n1, p1, n2, p2, de in violations[:10]:  # show worst 10
                print(f"    ΔE={de:5.1f}  {p1}  {n1[:24]:<24}  ×  {n2[:24]:<24}  {p2}")
        print()

    # Cross-conglomerate summary (informational)
    print(f"{'─' * 68}")
    print("  Cross-conglomerate pairs (informational — no hard constraint)")
    cross_close: list[tuple[str, str, str, str, str, str, float]] = []
    conf_items = [(c, p) for c in CONGLOMERATE_HEADERS for p in programs[c]]
    for i, (c1, (n1, p1, _)) in enumerate(conf_items):
        for c2, (n2, p2, _) in conf_items[i + 1 :]:
            if c1 == c2:
                continue
            de = delta_e76(p1, p2)
            if de < 10:  # only flag very close cross-conf pairs
                cross_close.append((c1, n1, p1, c2, n2, p2, de))

    if cross_close:
        cross_close.sort(key=lambda x: x[6])
        print(f"  ⚠️  {len(cross_close)} very close cross-conglomerate pair(s) (ΔE < 10):")
        for c1, n1, p1, c2, n2, p2, de in cross_close[:10]:
            print(f"    ΔE={de:5.1f}  [{c1}] {n1[:22]:<22}  ×  [{c2}] {n2[:22]:<22}")
    else:
        print("  No pairs with ΔE < 10 across conglomerates.")

    print(f"\n{'═' * 68}")
    verdict = "PASS" if total_violations == 0 else "FAIL"
    print(f"  Overall: {verdict}  |  {total_violations} violation(s) / {total_pairs} intra-conglomerate pairs")
    print(f"{'═' * 68}\n")

    return 1 if total_violations else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify program color ΔE distances.")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD)
    args = parser.parse_args()
    sys.exit(run(args.threshold))
