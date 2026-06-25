"""seed_staff.py — generate coaching staffs and booster groups for all 130 programs.

Usage:
    uv run scripts/seed_staff.py [--db-url URL] [--seed N] [--dry-run]
    uv run seed-staff [--db-url URL] [--seed N] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COACH_ROLES = [
    "Head Coach",
    "Offensive Coordinator",
    "Defensive Coordinator",
    "Special Teams Coordinator",
    "Recruiting Coordinator",
]

# SBC = Southern Broadcast Coalition — uses southern name corpus
SOUTHERN_CONGLOMERATE_CODE = "SBC"
SOUTHERN_CONGLOMERATE_ID = 2  # verified from DB seed

# Booster count distribution: 3 (weight 2), 4 (weight 5), 5 (weight 3)
BOOSTER_COUNT_POPULATION = [3, 4, 5]
BOOSTER_COUNT_WEIGHTS = [2, 5, 3]

# Whimsy sampling rates
WHIMSY_FIRST_RATE = 0.10   # 10% chance whimsy first name
WHIMSY_BOTH_RATE = 0.01    # 1% chance both first and last are whimsy


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CoachRow:
    program_id: int
    role: str
    first_name: str
    last_name: str
    rating: float


@dataclass
class BoosterRow:
    program_id: int
    first_name: str
    last_name: str
    influence: float


@dataclass
class ProgramInfo:
    id: int
    name: str
    conglomerate_id: int
    prestige: int


# ---------------------------------------------------------------------------
# Name corpus loading
# ---------------------------------------------------------------------------

def load_name_corpus(corpus_path: Path) -> dict:
    with open(corpus_path) as f:
        return json.load(f)


def _sample_weighted(pairs: list[list]) -> str:
    """Sample from a list of [name, weight] pairs."""
    names = [p[0] for p in pairs]
    weights = [p[1] for p in pairs]
    return random.choices(names, weights=weights, k=1)[0]


def _sample_whimsy(whimsy: list[str]) -> str:
    """Sample uniformly from flat whimsy list."""
    return random.choice(whimsy)


def _pick_corpus_key(conglomerate_id: int) -> str:
    """Return 'southern' for SBC programs, 'general' otherwise."""
    return "southern" if conglomerate_id == SOUTHERN_CONGLOMERATE_ID else "general"


def sample_first_name(corpus: dict, conglomerate_id: int) -> str:
    """Sample a first name from the male_first pool (includes ambiguous names)."""
    key = _pick_corpus_key(conglomerate_id)
    return _sample_weighted(corpus["male_first"][key])


def sample_last_name(corpus: dict, short_only: bool = False) -> str:
    """Sample a surname. If short_only=True, filter to len <= 8 ('old-money' bias)."""
    surnames = corpus["surnames"]
    if short_only:
        surnames = [s for s in surnames if len(s[0]) <= 8]
    return _sample_weighted(surnames)


def generate_name(
    corpus: dict,
    conglomerate_id: int,
    short_surname: bool = False,
) -> tuple[str, str]:
    """Generate (first_name, last_name) applying whimsy override rules.

    Whimsy rules (same as roster-gen):
    - r < 0.01  → both first and last are whimsy words (1%)
    - r < 0.055 → whimsy first, normal last (4.5%)
    - r < 0.10  → normal first, whimsy last (4.5%)
    - otherwise → both normal (90%)
    """
    whimsy = corpus["whimsy"]
    roll = random.random()

    if roll < WHIMSY_BOTH_RATE:
        first = _sample_whimsy(whimsy)
        last = _sample_whimsy(whimsy)
    elif roll < 0.055:
        first = _sample_whimsy(whimsy)
        last = sample_last_name(corpus, short_only=short_surname)
    elif roll < WHIMSY_FIRST_RATE:
        first = sample_first_name(corpus, conglomerate_id)
        last = _sample_whimsy(whimsy)
    else:
        first = sample_first_name(corpus, conglomerate_id)
        last = sample_last_name(corpus, short_only=short_surname)

    return first, last


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def generate_coaches(
    programs: list[ProgramInfo],
    corpus: dict,
    rng: random.Random,
) -> list[CoachRow]:
    """Generate 5 coaches per program (650 total)."""
    coaches: list[CoachRow] = []

    for program in programs:
        for role in COACH_ROLES:
            first, last = generate_name(corpus, program.conglomerate_id, short_surname=False)
            rating = round(rng.uniform(0.0, 1.0), 4)
            coaches.append(CoachRow(
                program_id=program.id,
                role=role,
                first_name=first,
                last_name=last,
                rating=rating,
            ))

    return coaches


def generate_boosters(
    programs: list[ProgramInfo],
    corpus: dict,
    rng: random.Random,
) -> list[BoosterRow]:
    """Generate 3-5 boosters per program (~520 total)."""
    boosters: list[BoosterRow] = []

    for program in programs:
        count = rng.choices(BOOSTER_COUNT_POPULATION, weights=BOOSTER_COUNT_WEIGHTS, k=1)[0]
        for _ in range(count):
            first, last = generate_name(corpus, program.conglomerate_id, short_surname=True)
            influence = round(rng.uniform(0.0, 1.0), 4)
            boosters.append(BoosterRow(
                program_id=program.id,
                first_name=first,
                last_name=last,
                influence=influence,
            ))

    return boosters


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_coaches(coaches: list[CoachRow], programs: list[ProgramInfo]) -> list[str]:
    errors: list[str] = []

    # Total count
    if len(coaches) != len(programs) * 5:
        errors.append(f"Expected {len(programs) * 5} coaches, got {len(coaches)}")

    # Per-program checks
    by_program: dict[int, list[CoachRow]] = {}
    for c in coaches:
        by_program.setdefault(c.program_id, []).append(c)

    for program in programs:
        prog_coaches = by_program.get(program.id, [])
        if len(prog_coaches) != 5:
            errors.append(f"Program {program.id} has {len(prog_coaches)} coaches, expected 5")
        roles = [c.role for c in prog_coaches]
        for role in COACH_ROLES:
            if roles.count(role) != 1:
                errors.append(f"Program {program.id}: role '{role}' appears {roles.count(role)} times")

    # Rating range
    bad_ratings = [c for c in coaches if not (0.0 <= c.rating <= 1.0)]
    if bad_ratings:
        errors.append(f"{len(bad_ratings)} coaches have rating outside [0.0, 1.0]")

    return errors


def validate_boosters(boosters: list[BoosterRow], programs: list[ProgramInfo]) -> list[str]:
    errors: list[str] = []

    # Total range
    total = len(boosters)
    if not (390 <= total <= 650):
        errors.append(f"Total boosters {total} outside expected range [390, 650]")

    # Per-program count
    by_program: dict[int, list[BoosterRow]] = {}
    for b in boosters:
        by_program.setdefault(b.program_id, []).append(b)

    for program in programs:
        count = len(by_program.get(program.id, []))
        if count not in (3, 4, 5):
            errors.append(f"Program {program.id} has {count} boosters, expected 3-5")

    # Influence range
    bad = [b for b in boosters if not (0.0 <= b.influence <= 1.0)]
    if bad:
        errors.append(f"{len(bad)} boosters have influence outside [0.0, 1.0]")

    return errors


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def get_sync_url(db_url: str) -> str:
    """Convert asyncpg URL to psycopg2 sync URL."""
    if db_url.startswith("postgresql+asyncpg://"):
        return db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
    return db_url


def load_programs(db_url: str) -> list[ProgramInfo]:
    """Load all programs from DB."""
    sync_url = get_sync_url(db_url)
    engine = create_engine(sync_url, echo=False)
    programs: list[ProgramInfo] = []
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name, conglomerate_id, prestige FROM programs ORDER BY id")
        )
        for row in result:
            programs.append(ProgramInfo(
                id=row[0],
                name=row[1],
                conglomerate_id=row[2],
                prestige=row[3],
            ))
    return programs


def seed_to_db(
    db_url: str,
    coaches: list[CoachRow],
    boosters: list[BoosterRow],
    dry_run: bool,
) -> None:
    """Insert coaches and boosters into DB."""
    if dry_run:
        print(f"[dry-run] Would insert {len(coaches)} coaches and {len(boosters)} boosters.")
        return

    sync_url = get_sync_url(db_url)
    engine = create_engine(sync_url, echo=False)

    with engine.begin() as conn:
        # Clear existing staff (idempotent re-seed)
        print("Clearing existing coaches and boosters...")
        conn.execute(text("DELETE FROM boosters"))
        conn.execute(text("DELETE FROM coaches"))

        # Insert coaches
        print(f"Inserting {len(coaches)} coaches...")
        conn.execute(
            text(
                "INSERT INTO coaches (program_id, role, first_name, last_name, rating) "
                "VALUES (:program_id, :role, :first_name, :last_name, :rating)"
            ),
            [
                {
                    "program_id": c.program_id,
                    "role": c.role,
                    "first_name": c.first_name,
                    "last_name": c.last_name,
                    "rating": c.rating,
                }
                for c in coaches
            ],
        )
        print(f"Inserted {len(coaches)} coaches.")

        # Insert boosters
        print(f"Inserting {len(boosters)} boosters...")
        conn.execute(
            text(
                "INSERT INTO boosters (program_id, first_name, last_name, influence) "
                "VALUES (:program_id, :first_name, :last_name, :influence)"
            ),
            [
                {
                    "program_id": b.program_id,
                    "first_name": b.first_name,
                    "last_name": b.last_name,
                    "influence": b.influence,
                }
                for b in boosters
            ],
        )
        print(f"Inserted {len(boosters)} boosters.")

    print("Staff seed complete.")


def validate_db(db_url: str) -> list[str]:
    """Post-insert DB validation. Returns list of errors."""
    sync_url = get_sync_url(db_url)
    engine = create_engine(sync_url, echo=False)
    errors: list[str] = []

    with engine.connect() as conn:
        # Coaches count
        coach_count = conn.execute(text("SELECT COUNT(*) FROM coaches")).scalar()
        if coach_count != 650:
            errors.append(f"DB: coaches has {coach_count} rows, expected 650")
        else:
            print(f"[ok] coaches: {coach_count} rows")

        # Each program has exactly one of each role
        role_check = conn.execute(text(
            "SELECT program_id, role, COUNT(*) c FROM coaches "
            "GROUP BY program_id, role HAVING COUNT(*) != 1"
        )).fetchall()
        if role_check:
            errors.append(f"DB: {len(role_check)} (program, role) pairs with count != 1")
        else:
            print("[ok] coaches: each program has exactly one coach per role")

        # Coaches rating range
        bad_ratings = conn.execute(text(
            "SELECT COUNT(*) FROM coaches WHERE rating < 0.0 OR rating > 1.0"
        )).scalar()
        if bad_ratings:
            errors.append(f"DB: {bad_ratings} coaches with rating outside [0.0, 1.0]")
        else:
            print("[ok] coaches: all ratings in [0.0, 1.0]")

        # Boosters count
        booster_count = conn.execute(text("SELECT COUNT(*) FROM boosters")).scalar()
        if not (390 <= booster_count <= 650):
            errors.append(f"DB: boosters has {booster_count} rows, outside [390, 650]")
        else:
            print(f"[ok] boosters: {booster_count} rows (in expected range 390-650)")

        # Boosters per program: 3-5
        bad_counts = conn.execute(text(
            "SELECT program_id, COUNT(*) c FROM boosters "
            "GROUP BY program_id HAVING COUNT(*) NOT BETWEEN 3 AND 5"
        )).fetchall()
        if bad_counts:
            errors.append(f"DB: {len(bad_counts)} programs with booster count outside [3, 5]")
        else:
            print("[ok] boosters: all programs have 3-5 boosters")

        # Boosters influence range
        bad_influence = conn.execute(text(
            "SELECT COUNT(*) FROM boosters WHERE influence < 0.0 OR influence > 1.0"
        )).scalar()
        if bad_influence:
            errors.append(f"DB: {bad_influence} boosters with influence outside [0.0, 1.0]")
        else:
            print("[ok] boosters: all influence values in [0.0, 1.0]")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed coaching staffs and booster groups for all 130 programs"
    )
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
        help="Random seed for reproducibility (default: 42)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate and validate only — do not write to DB",
    )
    args = parser.parse_args()

    # Seed the RNG
    rng = random.Random(args.seed)
    random.seed(args.seed)  # also seed global random for generate_name calls

    # Locate name corpus
    script_dir = Path(__file__).parent
    corpus_path = script_dir / "seed_data" / "name_corpus.json"
    if not corpus_path.exists():
        print(f"ERROR: name corpus not found: {corpus_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Loading name corpus from {corpus_path}...")
    corpus = load_name_corpus(corpus_path)

    # Load programs
    print(f"Loading programs from DB...")
    programs = load_programs(args.db_url)
    if len(programs) != 130:
        print(f"ERROR: Expected 130 programs in DB, found {len(programs)}", file=sys.stderr)
        sys.exit(1)
    print(f"Loaded {len(programs)} programs.")

    # Generate coaches
    print("\nGenerating coaches...")
    coaches = generate_coaches(programs, corpus, rng)
    print(f"Generated {len(coaches)} coaches.")

    # Validate coaches
    coach_errors = validate_coaches(coaches, programs)
    if coach_errors:
        print("COACH VALIDATION ERRORS:")
        for e in coach_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Coach validation passed.")

    # Generate boosters
    print("\nGenerating boosters...")
    boosters = generate_boosters(programs, corpus, rng)
    print(f"Generated {len(boosters)} boosters.")

    # Validate boosters
    booster_errors = validate_boosters(boosters, programs)
    if booster_errors:
        print("BOOSTER VALIDATION ERRORS:")
        for e in booster_errors:
            print(f"  - {e}")
        sys.exit(1)
    print("Booster validation passed.")

    # Print summary
    by_program_boosters: dict[int, int] = {}
    for b in boosters:
        by_program_boosters[b.program_id] = by_program_boosters.get(b.program_id, 0) + 1

    counts = list(by_program_boosters.values())
    print(f"\nSummary:")
    print(f"  Coaches: {len(coaches)} (5 per program x 130 programs)")
    print(f"  Boosters: {len(boosters)} total")
    print(f"  Booster distribution: {counts.count(3)}x3, {counts.count(4)}x4, {counts.count(5)}x5")

    # Insert or skip
    seed_to_db(args.db_url, coaches, boosters, dry_run=args.dry_run)

    # Post-insert validation
    if not args.dry_run:
        print("\nRunning post-insert DB validation...")
        db_errors = validate_db(args.db_url)
        if db_errors:
            print("\nDB VALIDATION ERRORS:")
            for e in db_errors:
                print(f"  - {e}")
            sys.exit(1)
        print("\nAll validations passed. Staff seed complete.")
    else:
        print("\n[dry-run] Staff seed complete. No data written to DB.")


if __name__ == "__main__":
    main()
