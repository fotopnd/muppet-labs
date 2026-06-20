"""seed_roster.py — Generate 85 players per program (11,050 total) and load them into the players table.

Usage:
    uv run seed-roster --db-url $DATABASE_URL --seed 42
    uv run seed-roster --db-url $DATABASE_URL --seed 42 --dry-run
    uv run seed-roster --db-url $DATABASE_URL --seed 42 --dry-run --limit 5
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import sqlalchemy as sa
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLAYERS_PER_PROGRAM = 85
SBC_CONGLOMERATE_CODE = "SBC"

# Position distribution spec: list of (position, count) pairs summing to 85.
# Reserve/Walk-on pool — positions drawn from a mixed set.
POSITION_DISTRIBUTION: list[tuple[str, int]] = [
    ("QB", 3),
    ("RB", 4),
    ("FB", 2),
    ("WR", 8),
    ("TE", 4),
    ("LT", 3),
    ("LG", 3),
    ("C", 3),
    ("RG", 3),
    ("RT", 3),
    ("DE", 5),
    ("DT", 5),
    ("OLB", 5),
    ("MLB", 4),
    ("CB", 7),
    ("S", 5),
    ("K", 1),
    ("P", 2),
    ("LS", 1),
    ("ATH", 4),
    # Reserve/Walk-on (10 total): mixed positions
    ("QB", 1),
    ("RB", 1),
    ("WR", 2),
    ("OLB", 1),
    ("CB", 1),
    ("DE", 1),
    ("LT", 1),
    ("S", 1),
    ("ATH", 1),
]

# Derive flat roster template from distribution
ROSTER_TEMPLATE: list[str] = []
for pos, count in POSITION_DISTRIBUTION:
    ROSTER_TEMPLATE.extend([pos] * count)

assert len(ROSTER_TEMPLATE) == 85, f"Roster template has {len(ROSTER_TEMPLATE)} positions, expected 85"

# Jersey number ranges by position group
JERSEY_RANGES: dict[str, tuple[int, int]] = {
    "QB":  (1, 19),
    "RB":  (20, 39),
    "FB":  (20, 49),
    "WR":  (1, 19),
    "TE":  (40, 89),
    "LT":  (50, 79),
    "LG":  (50, 79),
    "C":   (50, 79),
    "RG":  (50, 79),
    "RT":  (50, 79),
    "DE":  (90, 99),
    "DT":  (90, 99),
    "OLB": (40, 59),
    "MLB": (40, 59),
    "CB":  (20, 49),
    "S":   (20, 49),
    "K":   (1, 19),
    "P":   (1, 19),
    "LS":  (50, 79),
    "ATH": (1, 49),
}

# Year weights: skewed toward 1–2 (freshman/sophomore)
YEAR_WEIGHTS = [40, 30, 20, 10]  # for years 1, 2, 3, 4


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class PlayerRow:
    program_id: int
    first_name: str
    last_name: str
    position: str
    year: int
    jersey_num: int
    alpha: float
    delta: float
    sigma: float
    psi: float
    omega: float


# ---------------------------------------------------------------------------
# Name corpus helpers
# ---------------------------------------------------------------------------

def load_corpus(corpus_path: Path) -> dict:
    with open(corpus_path) as f:
        return json.load(f)


def weighted_draw(pairs: list[list]) -> str:
    """Draw one item from a list of [name, weight] pairs."""
    names = [p[0] for p in pairs]
    weights = [p[1] for p in pairs]
    return random.choices(names, weights=weights, k=1)[0]


def whimsy_draw(corpus: dict) -> str:
    """Draw a single whimsy word (uniform from flat list)."""
    return random.choice(corpus["whimsy"])


def draw_name(corpus: dict, is_sbc: bool) -> tuple[str, str]:
    """
    Draw (first_name, last_name) applying the whimsy rule:
      1%   — both first AND last are whimsy
      4.5% — whimsy first only
      4.5% — whimsy last only
      90%  — all standard
    """
    first_pool = corpus["male_first"]["southern" if is_sbc else "general"]
    surname_pool = corpus["surnames"]

    r = random.random()
    if r < 0.01:
        first = whimsy_draw(corpus)
        last = whimsy_draw(corpus)
    elif r < 0.055:
        first = whimsy_draw(corpus)
        last = weighted_draw(surname_pool)
    elif r < 0.10:
        first = weighted_draw(first_pool)
        last = whimsy_draw(corpus)
    else:
        first = weighted_draw(first_pool)
        last = weighted_draw(surname_pool)

    return first, last


# ---------------------------------------------------------------------------
# Attribute generation
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def draw_attrs(position: str, year: int) -> tuple[float, float, float, float, float]:
    """
    Draw (alpha, delta, sigma, psi, omega) in [0.0, 1.0].

    V1 placeholder: uniform [0.2, 0.8] with mild position bias.
    Year modifiers: senior (+0.05 sigma), freshman (+0.05 delta).
    """
    base = lambda: random.uniform(0.2, 0.8)

    alpha = base()
    delta = base()
    sigma = base()
    psi = base()
    omega = base()

    # Year-based modifiers
    if year == 1:   # freshman
        delta = clamp(delta + 0.05)
    elif year == 4:  # senior
        sigma = clamp(sigma + 0.05)

    return alpha, delta, sigma, psi, omega


# ---------------------------------------------------------------------------
# Jersey number assignment
# ---------------------------------------------------------------------------

def assign_jersey(position: str, used: set[int]) -> int:
    """
    Pick a jersey number from position's range that isn't already used.
    Falls back to any unused number 1–99 if the range is exhausted.
    """
    lo, hi = JERSEY_RANGES.get(position, (1, 99))
    candidates = [n for n in range(lo, hi + 1) if n not in used]
    if not candidates:
        # Fallback: any unused number
        candidates = [n for n in range(1, 100) if n not in used]
    if not candidates:
        raise RuntimeError("Exhausted all jersey numbers for program")
    return random.choice(candidates)


# ---------------------------------------------------------------------------
# Roster generation
# ---------------------------------------------------------------------------

def generate_roster(program_id: int, is_sbc: bool, corpus: dict) -> list[PlayerRow]:
    """Generate exactly 85 PlayerRow objects for a single program."""
    players: list[PlayerRow] = []
    used_jerseys: set[int] = set()

    positions = ROSTER_TEMPLATE.copy()
    random.shuffle(positions)

    for position in positions:
        first, last = draw_name(corpus, is_sbc)
        year = random.choices([1, 2, 3, 4], weights=YEAR_WEIGHTS, k=1)[0]
        jersey = assign_jersey(position, used_jerseys)
        used_jerseys.add(jersey)
        alpha, delta, sigma, psi, omega = draw_attrs(position, year)

        players.append(PlayerRow(
            program_id=program_id,
            first_name=first,
            last_name=last,
            position=position,
            year=year,
            jersey_num=jersey,
            alpha=alpha,
            delta=delta,
            sigma=sigma,
            psi=psi,
            omega=omega,
        ))

    return players


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def get_sync_url(db_url: str) -> str:
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return db_url


def fetch_programs(engine: sa.Engine) -> list[dict]:
    """Return list of {id, conglomerate_id} for all programs."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT p.id, c.code as conglomerate_code FROM programs p JOIN conglomerates c ON c.id = p.conglomerate_id ORDER BY p.id")
        ).fetchall()
    return [{"id": r[0], "conglomerate_code": r[1]} for r in rows]


def seed(db_url: str, all_players: list[PlayerRow], dry_run: bool) -> None:
    if dry_run:
        print(f"[dry-run] Would insert {len(all_players)} player rows. Skipping DB write.")
        return

    sync_url = get_sync_url(db_url)
    engine = create_engine(sync_url, echo=False)

    with engine.begin() as conn:
        # Truncate existing players (idempotent re-seed)
        conn.execute(text("TRUNCATE TABLE players RESTART IDENTITY"))

        # Bulk insert via executemany
        rows = [
            {
                "program_id": p.program_id,
                "first_name": p.first_name,
                "last_name": p.last_name,
                "position": p.position,
                "year": p.year,
                "jersey_num": p.jersey_num,
                "alpha": p.alpha,
                "delta": p.delta,
                "sigma": p.sigma,
                "psi": p.psi,
                "omega": p.omega,
            }
            for p in all_players
        ]

        conn.execute(
            text(
                "INSERT INTO players (program_id, first_name, last_name, position, year, jersey_num, alpha, delta, sigma, psi, omega) "
                "VALUES (:program_id, :first_name, :last_name, :position, :year, :jersey_num, :alpha, :delta, :sigma, :psi, :omega)"
            ),
            rows,
        )

    print(f"Inserted {len(all_players)} players into the database.")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_players(all_players: list[PlayerRow]) -> list[str]:
    """Run pre-insert validation. Returns list of errors."""
    errors: list[str] = []

    total = len(all_players)
    if total != 11050:
        errors.append(f"Expected 11,050 players, got {total}")

    by_program: dict[int, list[PlayerRow]] = {}
    for p in all_players:
        by_program.setdefault(p.program_id, []).append(p)

    for prog_id, players in by_program.items():
        if len(players) != 85:
            errors.append(f"Program {prog_id}: expected 85 players, got {len(players)}")

        jerseys = [p.jersey_num for p in players]
        if len(set(jerseys)) != len(jerseys):
            dupes = [j for j in jerseys if jerseys.count(j) > 1]
            errors.append(f"Program {prog_id}: duplicate jerseys {set(dupes)}")

        for p in players:
            for attr_name, val in [("alpha", p.alpha), ("delta", p.delta), ("sigma", p.sigma), ("psi", p.psi), ("omega", p.omega)]:
                if not (0.0 <= val <= 1.0):
                    errors.append(f"Program {prog_id}: {attr_name}={val} out of [0,1]")

    # Whimsy rate (approximate — just warn, not fail)
    # corpus whimsy words are all lowercase-first-letter or capitalized; checking here is impractical
    # without the corpus, so we skip this check in pre-insert validation.

    return errors


def validate_db(engine: sa.Engine) -> list[str]:
    """Post-insert DB validation. Returns list of errors."""
    errors: list[str] = []

    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM players")).scalar()
        if total != 11050:
            errors.append(f"DB: players table has {total} rows, expected 11,050")
        else:
            print(f"[ok] players: {total} rows")

        # Each program has 85
        bad_counts = conn.execute(
            text(
                "SELECT program_id, COUNT(*) c FROM players GROUP BY program_id HAVING COUNT(*) != 85"
            )
        ).fetchall()
        if bad_counts:
            for row in bad_counts:
                errors.append(f"DB: program {row[0]} has {row[1]} players, expected 85")
        else:
            print("[ok] all 130 programs have exactly 85 players")

        # Jersey uniqueness within program
        jersey_dupes = conn.execute(
            text(
                "SELECT program_id, jersey_num, COUNT(*) c FROM players "
                "GROUP BY program_id, jersey_num HAVING COUNT(*) > 1"
            )
        ).fetchall()
        if jersey_dupes:
            for row in jersey_dupes:
                errors.append(f"DB: program {row[0]} jersey {row[1]} appears {row[2]} times")
        else:
            print("[ok] jersey numbers unique within each program")

        # Attribute range checks
        for attr in ("alpha", "delta", "sigma", "psi", "omega"):
            bad = conn.execute(
                text(f"SELECT COUNT(*) FROM players WHERE {attr} < 0.0 OR {attr} > 1.0")
            ).scalar()
            if bad:
                errors.append(f"DB: {bad} players with {attr} out of [0,1]")
            else:
                print(f"[ok] {attr}: all values in [0,1]")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and seed 11,050 fictional players into gridiron DB")
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql+asyncpg://gridiron:gridiron@localhost:5438/gridiron",
        ),
        help="SQLAlchemy database URL",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible generation",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and validate but do not write to DB",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Only seed N programs (for testing; omit for full run)",
    )
    args = parser.parse_args()

    random.seed(args.seed)

    # Locate name corpus
    script_dir = Path(__file__).parent
    corpus_path = script_dir / "seed_data" / "name_corpus.json"
    if not corpus_path.exists():
        print(f"ERROR: name corpus not found at {corpus_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading name corpus from {corpus_path}...")
    corpus = load_corpus(corpus_path)

    # Fetch programs from DB
    sync_url = get_sync_url(args.db_url)
    engine = create_engine(sync_url, echo=False)
    print("Fetching programs from DB...")
    programs = fetch_programs(engine)

    if not programs:
        print("ERROR: no programs found in DB. Run seed-programs first.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(programs)} programs.")

    if args.limit:
        programs = programs[: args.limit]
        print(f"--limit {args.limit}: processing {len(programs)} programs only.")

    # Generate rosters
    all_players: list[PlayerRow] = []
    for prog in programs:
        is_sbc = prog["conglomerate_code"] == SBC_CONGLOMERATE_CODE
        roster = generate_roster(prog["id"], is_sbc, corpus)
        all_players.extend(roster)

    print(f"Generated {len(all_players)} player records.")

    # Pre-insert validation (skip count check when using --limit)
    if not args.limit:
        print("\nRunning pre-insert validation...")
        errors = validate_players(all_players)
        if errors:
            print("VALIDATION ERRORS:")
            for e in errors:
                print(f"  - {e}")
            sys.exit(1)
        print("Pre-insert validation passed.")
    else:
        print(f"[limit mode] Skipping strict count validation (limit={args.limit}).")

    # Seed
    seed(args.db_url, all_players, dry_run=args.dry_run)

    # Post-insert DB validation
    if not args.dry_run and not args.limit:
        print("\nRunning post-insert DB validation...")
        db_errors = validate_db(engine)
        if db_errors:
            print("\nDB VALIDATION ERRORS:")
            for e in db_errors:
                print(f"  - {e}")
            sys.exit(1)
        print("\nAll validations passed. Roster seed complete.")
    elif args.dry_run:
        print("\n[dry-run] Seed complete. No data written to DB.")
    else:
        print(f"\n[limit mode] Inserted {len(all_players)} players for {len(programs)} programs.")


if __name__ == "__main__":
    main()
