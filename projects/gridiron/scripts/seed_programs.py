"""seed_programs.py — parse UNIVERSE-SEEDING.md and load all 130 programs + 5 conglomerates.

Usage:
    uv run scripts/seed_programs.py [--db-url URL] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Conglomerate seed data (from brief)
# ---------------------------------------------------------------------------

CONGLOMERATES = [
    {"code": "NCC", "full_name": "National Collegiate Conference", "network": "TCB Sports Network",
     "region": "Great Lakes → Pacific", "primary_color": "#0A192F", "secondary_color": "#F5F7FA", "tertiary_color": "#00F0FF"},
    {"code": "SBC", "full_name": "Southern Broadcast Coalition", "network": "ISG Sports Network",
     "region": "Deep South / TX / Plains", "primary_color": "#8B0000", "secondary_color": "#FFD700", "tertiary_color": "#1C1C1C"},
    {"code": "ACA", "full_name": "American College Alliance", "network": "STN Broadcast Group",
     "region": "Eastern Seaboard", "primary_color": "#0B0C10", "secondary_color": "#C5A059", "tertiary_color": "#FFFDD0"},
    {"code": "MCC", "full_name": "Midwestern Collegiate Conference", "network": "CHBA Sports",
     "region": "Interior / Rust Belt / Plains", "primary_color": "#DAA520", "secondary_color": "#2F4F4F", "tertiary_color": "#FFFFFF"},
    {"code": "UAC", "full_name": "United American Conference", "network": "FPC Americana Network",
     "region": "Nationwide mid-major", "primary_color": "#104E8B", "secondary_color": "#CD2626", "tertiary_color": "#F0F0F0"},
]

# Elo seed range by prestige level (from UNIVERSE-SEEDING.md Section 1)
ELO_RANGES: dict[int, tuple[int, int]] = {
    5: (1650, 1750),
    4: (1550, 1649),
    3: (1450, 1549),
    2: (1350, 1449),
    1: (1250, 1349),
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class ConglomerateRow:
    code: str
    full_name: str
    network: str


@dataclass
class ProgramRow:
    conglomerate_code: str
    name: str
    emoji: str
    mascot: str
    city: str
    tier: int
    prestige: int
    elo_seed_min: int
    elo_seed_max: int
    founded_year: int
    primary_color: str
    secondary_color: str
    stadium_name: str
    stadium_cap: int | None


# ---------------------------------------------------------------------------
# Markdown parser
# ---------------------------------------------------------------------------

# Map section heading substrings to conglomerate codes
SECTION_CODES = {
    "NCC": "NCC",
    "SBC": "SBC",
    "ACA": "ACA",
    "MCC": "MCC",
    "UAC": "UAC",
}

# Regex to match a markdown table row (starts with |, ends with |)
TABLE_ROW_RE = re.compile(r"^\|(.+)\|$")
# Regex to match hex color like `#RRGGBB`
HEX_RE = re.compile(r"`(#[0-9A-Fa-f]{6})`")
# Strip backtick-wrapped content
BACKTICK_RE = re.compile(r"`([^`]+)`")
# Section heading that identifies a conglomerate block
SECTION_HEADING_RE = re.compile(r"^####\s+(NCC|SBC|ACA|MCC|UAC)\b")
# Identity table marker
IDENTITY_HEADER_RE = re.compile(r"Real Name.*Fictional Name.*Emoji.*Mascot", re.IGNORECASE)
# Brand table marker
BRAND_HEADER_RE = re.compile(r"Fictional Name.*Primary.*Secondary.*Stadium.*Est\.", re.IGNORECASE)


def split_row(line: str) -> list[str]:
    """Split a markdown table row into cleaned cells."""
    # Strip outer pipes and split
    cells = line.strip("|").split("|")
    return [c.strip() for c in cells]


def is_separator(line: str) -> bool:
    """True if line is a markdown table separator (|---|---|...)."""
    stripped = line.strip()
    return bool(re.match(r"^\|[-| :]+\|$", stripped))


def parse_hex(cell: str) -> str:
    """Extract #RRGGBB from a cell that may contain backtick-wrapped hex."""
    m = HEX_RE.search(cell)
    if m:
        return m.group(1)
    # Also try plain match
    m2 = re.search(r"#[0-9A-Fa-f]{6}", cell)
    if m2:
        return m2.group(0)
    return cell.strip()


def parse_stadium_cap(cell: str) -> int | None:
    """Parse capacity from identity table Cap column. Returns None if empty/missing."""
    cleaned = cell.strip()
    if not cleaned or cleaned == "-":
        return None
    # Remove commas and parse
    try:
        return int(cleaned.replace(",", ""))
    except ValueError:
        return None


def _randomise_cap(raw_cap: int | None) -> int | None:
    if raw_cap is None:
        return None
    factor = 1.0 + random.uniform(-0.10, 0.10)
    return round(raw_cap * factor)


def parse_programs_from_markdown(md_path: Path) -> list[ProgramRow]:
    """Parse UNIVERSE-SEEDING.md and return all 130 ProgramRow objects."""
    lines = md_path.read_text().splitlines()

    programs: list[ProgramRow] = []
    current_conglomerate: str | None = None

    # Per-conglomerate buffers
    identity_rows: list[dict] = []
    brand_rows: list[dict] = []

    # State machine
    mode: str = "none"  # none | identity_header | identity | brand_header | brand

    def flush_conglomerate() -> None:
        """Join identity and brand rows and extend `programs`."""
        if not current_conglomerate or not identity_rows:
            return

        # Build lookup from fictional name -> brand info
        brand_by_name: dict[str, dict] = {r["name"]: r for r in brand_rows}

        for id_row in identity_rows:
            fname = id_row["name"]
            brand = brand_by_name.get(fname)
            if brand is None:
                raise ValueError(
                    f"Brand data missing for program '{fname}' in {current_conglomerate}"
                )

            prestige = id_row["prestige"]
            elo_min, elo_max = ELO_RANGES[prestige]

            programs.append(
                ProgramRow(
                    conglomerate_code=current_conglomerate,
                    name=fname,
                    emoji=id_row["emoji"],
                    mascot=id_row["mascot"],
                    city=id_row["city"],
                    tier=id_row["tier"],
                    prestige=prestige,
                    elo_seed_min=elo_min,
                    elo_seed_max=elo_max,
                    founded_year=brand["founded_year"],
                    primary_color=brand["primary"],
                    secondary_color=brand["secondary"],
                    stadium_name=brand["stadium"],
                    stadium_cap=_randomise_cap(id_row.get("cap")),
                )
            )

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # Detect new conglomerate section
        m = SECTION_HEADING_RE.match(stripped)
        if m:
            # Flush previous conglomerate data
            flush_conglomerate()
            current_conglomerate = m.group(1)
            identity_rows = []
            brand_rows = []
            mode = "none"
            i += 1
            continue

        if current_conglomerate is None:
            i += 1
            continue

        # Detect identity table header
        if mode in ("none", "brand") and IDENTITY_HEADER_RE.search(stripped):
            mode = "identity_header"
            i += 1
            continue

        # Skip separator after header
        if mode == "identity_header":
            if is_separator(stripped):
                mode = "identity"
                i += 1
                continue
            i += 1
            continue

        # Parse identity rows
        if mode == "identity":
            if TABLE_ROW_RE.match(stripped):
                if not is_separator(stripped):
                    cells = split_row(stripped)
                    # Columns: Real Name | ST | Cap | P | Tier | Fictional Name | Emoji | Mascot | Fictional City
                    if len(cells) >= 9:
                        try:
                            prestige_val = int(cells[3])
                            tier_val = int(cells[4])
                            identity_rows.append({
                                "name": cells[5],
                                "emoji": cells[6],
                                "mascot": cells[7],
                                "city": cells[8],
                                "tier": tier_val,
                                "prestige": prestige_val,
                                "cap": parse_stadium_cap(cells[2]),
                            })
                        except (ValueError, IndexError) as e:
                            # Skip header/malformed rows
                            pass
            else:
                # End of identity table
                mode = "none"
            i += 1
            continue

        # Detect brand table header
        if mode == "none" and BRAND_HEADER_RE.search(stripped):
            mode = "brand_header"
            i += 1
            continue

        if mode == "brand_header":
            if is_separator(stripped):
                mode = "brand"
                i += 1
                continue
            i += 1
            continue

        # Parse brand rows
        if mode == "brand":
            if TABLE_ROW_RE.match(stripped):
                if not is_separator(stripped):
                    cells = split_row(stripped)
                    # Columns: Fictional Name | Primary | Secondary | Stadium | Est.
                    if len(cells) >= 5:
                        try:
                            # Strip ★ from stadium name
                            stadium_raw = cells[3].replace("★", "").strip()
                            founded_str = cells[4].strip()
                            founded_year = int(founded_str)
                            brand_rows.append({
                                "name": cells[0],
                                "primary": parse_hex(cells[1]),
                                "secondary": parse_hex(cells[2]),
                                "stadium": stadium_raw,
                                "founded_year": founded_year,
                            })
                        except (ValueError, IndexError):
                            pass
            else:
                mode = "none"
            i += 1
            continue

        i += 1

    # Flush the last conglomerate
    flush_conglomerate()
    return programs


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_programs(programs: list[ProgramRow]) -> list[str]:
    """Return a list of validation errors (empty = all good)."""
    errors: list[str] = []

    # Total count
    if len(programs) != 130:
        errors.append(f"Expected 130 programs, got {len(programs)}")

    # Per-conglomerate checks
    by_conf: dict[str, list[ProgramRow]] = {}
    for p in programs:
        by_conf.setdefault(p.conglomerate_code, []).append(p)

    if len(by_conf) != 5:
        errors.append(f"Expected 5 conglomerates, got {len(by_conf)}: {list(by_conf.keys())}")

    for code, rows in by_conf.items():
        if len(rows) != 26:
            errors.append(f"{code}: expected 26 programs, got {len(rows)}")
        tier1 = [r for r in rows if r.tier == 1]
        tier2 = [r for r in rows if r.tier == 2]
        if len(tier1) != 13:
            errors.append(f"{code}: expected 13 tier-1, got {len(tier1)}")
        if len(tier2) != 13:
            errors.append(f"{code}: expected 13 tier-2, got {len(tier2)}")

    # Uniqueness
    names = [p.name for p in programs]
    if len(set(names)) != len(names):
        dupes = [n for n in names if names.count(n) > 1]
        errors.append(f"Duplicate program names: {set(dupes)}")

    emojis = [p.emoji for p in programs]
    if len(set(emojis)) != len(emojis):
        dupes = [e for e in emojis if emojis.count(e) > 1]
        errors.append(f"Duplicate emoji values: {set(dupes)}")

    mascots = [p.mascot for p in programs]
    if len(set(mascots)) != len(mascots):
        dupes = [m for m in mascots if mascots.count(m) > 1]
        errors.append(f"Duplicate mascot values: {set(dupes)}")

    # Tier values
    bad_tiers = [p.name for p in programs if p.tier not in (1, 2)]
    if bad_tiers:
        errors.append(f"Invalid tier values for: {bad_tiers}")

    # Required string fields non-empty
    for p in programs:
        for field in ("name", "emoji", "mascot", "city", "primary_color", "secondary_color", "stadium_name"):
            val = getattr(p, field)
            if not val or not val.strip():
                errors.append(f"Program '{p.name}' has empty field: {field}")

    return errors


# ---------------------------------------------------------------------------
# Database insertion
# ---------------------------------------------------------------------------


def get_sync_url(db_url: str) -> str:
    """Convert asyncpg URL to sync psycopg2 or sync postgresql URL."""
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return db_url


def seed(db_url: str, programs: list[ProgramRow], dry_run: bool) -> None:
    """Insert conglomerates and programs into the database."""
    sync_url = get_sync_url(db_url)
    engine = create_engine(sync_url, echo=False)

    if dry_run:
        print("[dry-run] Skipping database insertion.")
        return

    with engine.begin() as conn:
        # Insert conglomerates
        print("Inserting conglomerates...")
        conf_id_map: dict[str, int] = {}
        for c in CONGLOMERATES:
            result = conn.execute(
                text(
                    "INSERT INTO conglomerates (code, full_name, network, region, primary_color, secondary_color, tertiary_color) "
                    "VALUES (:code, :full_name, :network, :region, :primary_color, :secondary_color, :tertiary_color) "
                    "ON CONFLICT (code) DO UPDATE SET full_name=EXCLUDED.full_name, network=EXCLUDED.network, "
                    "region=EXCLUDED.region, primary_color=EXCLUDED.primary_color, "
                    "secondary_color=EXCLUDED.secondary_color, tertiary_color=EXCLUDED.tertiary_color "
                    "RETURNING id"
                ),
                {"code": c["code"], "full_name": c["full_name"], "network": c["network"],
                 "region": c["region"], "primary_color": c["primary_color"],
                 "secondary_color": c["secondary_color"], "tertiary_color": c["tertiary_color"]},
            )
            row = result.fetchone()
            conf_id_map[c["code"]] = row[0]
            print(f"  {c['code']}: id={row[0]}")

        # Insert programs per conglomerate
        for code in ["NCC", "SBC", "ACA", "MCC", "UAC"]:
            conf_programs = [p for p in programs if p.conglomerate_code == code]
            print(f"\nInserting {len(conf_programs)} programs for {code}...")
            for p in conf_programs:
                conn.execute(
                    text(
                        "INSERT INTO programs ("
                        "  conglomerate_id, name, emoji, mascot, city, tier,"
                        "  elo_seed_min, elo_seed_max, prestige, founded_year,"
                        "  primary_color, secondary_color, stadium_name, stadium_cap"
                        ") VALUES ("
                        "  :conglomerate_id, :name, :emoji, :mascot, :city, :tier,"
                        "  :elo_seed_min, :elo_seed_max, :prestige, :founded_year,"
                        "  :primary_color, :secondary_color, :stadium_name, :stadium_cap"
                        ") ON CONFLICT (name) DO UPDATE SET"
                        "  emoji=EXCLUDED.emoji, mascot=EXCLUDED.mascot,"
                        "  city=EXCLUDED.city, tier=EXCLUDED.tier,"
                        "  elo_seed_min=EXCLUDED.elo_seed_min, elo_seed_max=EXCLUDED.elo_seed_max,"
                        "  prestige=EXCLUDED.prestige, founded_year=EXCLUDED.founded_year,"
                        "  primary_color=EXCLUDED.primary_color, secondary_color=EXCLUDED.secondary_color,"
                        "  stadium_name=EXCLUDED.stadium_name, stadium_cap=EXCLUDED.stadium_cap"
                    ),
                    {
                        "conglomerate_id": conf_id_map[code],
                        "name": p.name,
                        "emoji": p.emoji,
                        "mascot": p.mascot,
                        "city": p.city,
                        "tier": p.tier,
                        "elo_seed_min": p.elo_seed_min,
                        "elo_seed_max": p.elo_seed_max,
                        "prestige": p.prestige,
                        "founded_year": p.founded_year,
                        "primary_color": p.primary_color,
                        "secondary_color": p.secondary_color,
                        "stadium_name": p.stadium_name,
                        "stadium_cap": p.stadium_cap,
                    },
                )
                print(f"  ✓ {p.name}")

    print("\nDatabase insertion complete.")


def validate_db(db_url: str) -> list[str]:
    """Run post-insert DB validation. Returns list of errors."""
    sync_url = get_sync_url(db_url)
    engine = create_engine(sync_url, echo=False)
    errors: list[str] = []

    with engine.connect() as conn:
        # 1. Conglomerates count
        result = conn.execute(text("SELECT COUNT(*) FROM conglomerates"))
        count = result.scalar()
        if count != 5:
            errors.append(f"DB: conglomerates table has {count} rows, expected 5")
        else:
            print(f"[ok] conglomerates: {count} rows")

        # 2. Programs count
        result = conn.execute(text("SELECT COUNT(*) FROM programs"))
        count = result.scalar()
        if count != 130:
            errors.append(f"DB: programs table has {count} rows, expected 130")
        else:
            print(f"[ok] programs: {count} rows")

        # 3. No NULLs in required fields
        required_fields = [
            "name", "emoji", "mascot", "city", "tier",
            "elo_seed_min", "elo_seed_max", "prestige", "founded_year",
            "primary_color", "secondary_color", "stadium_name",
        ]
        for field in required_fields:
            result = conn.execute(
                text(f"SELECT COUNT(*) FROM programs WHERE {field} IS NULL")
            )
            null_count = result.scalar()
            if null_count > 0:
                errors.append(f"DB: {null_count} NULL values in programs.{field}")
            else:
                print(f"[ok] programs.{field}: no NULLs")

        # 4. Emoji uniqueness
        result = conn.execute(
            text(
                "SELECT emoji, COUNT(*) c FROM programs GROUP BY emoji HAVING COUNT(*) > 1"
            )
        )
        dupes = result.fetchall()
        if dupes:
            errors.append(f"DB: duplicate emoji values: {[(d[0], d[1]) for d in dupes]}")
        else:
            print("[ok] emoji: all unique")

        # 5. Mascot uniqueness
        result = conn.execute(
            text(
                "SELECT mascot, COUNT(*) c FROM programs GROUP BY mascot HAVING COUNT(*) > 1"
            )
        )
        dupes = result.fetchall()
        if dupes:
            errors.append(f"DB: duplicate mascot values: {[(d[0], d[1]) for d in dupes]}")
        else:
            print("[ok] mascot: all unique")

        # 6. Tier values only 1 or 2
        result = conn.execute(
            text("SELECT COUNT(*) FROM programs WHERE tier NOT IN (1, 2)")
        )
        bad_count = result.scalar()
        if bad_count > 0:
            errors.append(f"DB: {bad_count} programs with invalid tier")
        else:
            print("[ok] tier: all values are 1 or 2")

        # 7. Each conglomerate has exactly 26 programs (13 T1, 13 T2)
        result = conn.execute(
            text(
                "SELECT c.code, COUNT(p.id) total,"
                " SUM(CASE WHEN p.tier=1 THEN 1 ELSE 0 END) t1,"
                " SUM(CASE WHEN p.tier=2 THEN 1 ELSE 0 END) t2"
                " FROM conglomerates c"
                " LEFT JOIN programs p ON p.conglomerate_id = c.id"
                " GROUP BY c.code"
                " ORDER BY c.code"
            )
        )
        rows = result.fetchall()
        for row in rows:
            code, total, t1, t2 = row[0], row[1], row[2], row[3]
            if total != 26 or t1 != 13 or t2 != 13:
                errors.append(
                    f"DB: {code} has {total} programs (T1={t1}, T2={t2}), expected 26 (13/13)"
                )
            else:
                print(f"[ok] {code}: 26 programs (13 T1, 13 T2)")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed conglomerates and programs into gridiron DB")
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://gridiron:gridiron@localhost:5438/gridiron",
        ),
        help="SQLAlchemy database URL",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and validate only — do not write to DB",
    )
    args = parser.parse_args()

    # Locate UNIVERSE-SEEDING.md relative to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    md_path = project_root / "_config" / "UNIVERSE-SEEDING.md"

    if not md_path.exists():
        print(f"ERROR: source file not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing {md_path}...")
    programs = parse_programs_from_markdown(md_path)
    print(f"Parsed {len(programs)} programs.")

    # Pre-insert validation
    print("\nRunning pre-insert validation...")
    parse_errors = validate_programs(programs)
    if parse_errors:
        print("VALIDATION ERRORS:")
        for e in parse_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Pre-insert validation passed.")

    # Print summary per conglomerate
    by_conf: dict[str, list[ProgramRow]] = {}
    for p in programs:
        by_conf.setdefault(p.conglomerate_code, []).append(p)
    for code in ["NCC", "SBC", "ACA", "MCC", "UAC"]:
        rows = by_conf.get(code, [])
        t1 = sum(1 for r in rows if r.tier == 1)
        t2 = sum(1 for r in rows if r.tier == 2)
        print(f"  {code}: {len(rows)} programs ({t1} T1, {t2} T2)")

    # Insert (or skip if dry-run)
    seed(args.db_url, programs, dry_run=args.dry_run)

    # Post-insert DB validation
    if not args.dry_run:
        print("\nRunning post-insert DB validation...")
        db_errors = validate_db(args.db_url)
        if db_errors:
            print("\nDB VALIDATION ERRORS:")
            for e in db_errors:
                print(f"  - {e}")
            sys.exit(1)
        print("\nAll validations passed. Seed complete.")
    else:
        print("\n[dry-run] Seed complete. No data written to DB.")


if __name__ == "__main__":
    main()
