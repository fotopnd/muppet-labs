"""
build_name_corpus.py — downloads SSA + Census name data and builds
scripts/seed_data/name_corpus.json for downstream people-generation scripts.

CLI:
    uv run scripts/build_name_corpus.py            # download + build (skips download if cached)
    uv run scripts/build_name_corpus.py --check    # validate existing corpus JSON only
    uv run scripts/build_name_corpus.py --force    # re-download even if cached
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
import tempfile
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).parent
SEED_DIR = SCRIPTS_DIR / "seed_data"
SSA_NAMES_DIR = SEED_DIR / "ssa_names"
SSA_STATE_DIR = SEED_DIR / "ssa_state_names"
CENSUS_CSV = SEED_DIR / "Names_2010Census.csv"
CORPUS_JSON = SEED_DIR / "name_corpus.json"

# ---------------------------------------------------------------------------
# Download URLs
# ---------------------------------------------------------------------------

SSA_NATIONAL_URL = "https://www.ssa.gov/oact/babynames/names.zip"
SSA_STATE_URL = "https://www.ssa.gov/oact/babynames/state/namesbystate.zip"
CENSUS_URL = "https://www2.census.gov/topics/genealogy/2010surnames/Names_2010Census.csv"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COHORT_YEARS = range(1990, 2011)  # 1990–2010 inclusive
SOUTHERN_STATES = {"AL", "AR", "GA", "LA", "MS", "SC", "TN", "TX"}
GENERAL_MIN_COUNT = 500
SOUTHERN_MIN_COUNT = 100
SURNAME_MIN_COUNT = 1000

WHIMSY_POOL = [
    "Awl", "Bilge", "Blot", "Blunder", "Bobbin", "Bracken", "Brad", "Bramble", "Bristle",
    "Burdock", "Burrow", "Buzz", "Caliper", "Camshaft", "Capstan", "Cellar", "Chime",
    "Chutney", "Cleat", "Clink", "Cloakroom", "Clover", "Cobble", "Cog", "Copse",
    "Corduroy", "Crag", "Crisp", "Ditch", "Eaves", "Fen", "Fender", "Flange", "Furrow",
    "Garret", "Gasket", "Gorse", "Grime", "Grommet", "Grout", "Gusset", "Hacksaw",
    "Hitch", "Jicama", "Joist", "Kink", "Lanyard", "Larder", "Lath", "Ledger", "Lichen",
    "Mallet", "Morel", "Moss", "Mutter", "Newel", "Pantry", "Parsnip", "Pippin", "Piston",
    "Pleat", "Plink", "Plinth", "Plummet", "Porthole", "Puffball", "Radish", "Rattle",
    "Router", "Rutabaga", "Scullery", "Selvage", "Shackle", "Silo", "Slag", "Smudge",
    "Snag", "Spec", "Spill", "Spire", "Sprocket", "Stapler", "Teasel", "Thatch", "Thimble",
    "Thistle", "Thud", "Thumbtack", "Turbine", "Turnip", "Valve", "Velvet", "Yam",
]


# ---------------------------------------------------------------------------
# Download helpers
# ---------------------------------------------------------------------------

# SSA's website blocks Python urllib even with browser User-Agent (HTTP 403).
# curl with full browser-like sec-fetch headers is accepted. We shell out to curl
# to download SSA files; Census files are served more permissively.

_CURL_BROWSER_HEADERS = [
    "-H", "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "-H", "Accept-Language: en-US,en;q=0.9",
    "-H", "Accept-Encoding: gzip, deflate, br",
    "-H", "Referer: https://www.ssa.gov/oact/babynames/limits.html",
    "-H", "Sec-Fetch-Dest: document",
    "-H", "Sec-Fetch-Mode: navigate",
    "-H", "Sec-Fetch-Site: same-origin",
]


def _fetch_url_curl(url: str) -> bytes:
    """Download a URL using curl with browser-compatible headers."""
    result = subprocess.run(
        ["curl", "-L", "-s", "--fail", "--tlsv1.2", *_CURL_BROWSER_HEADERS, url],
        capture_output=True,
        timeout=180,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"curl failed (exit {result.returncode}) for {url}: {result.stderr.decode()[:200]}"
        )
    return result.stdout


def download_ssa_national(force: bool = False) -> None:
    """Download and extract SSA national name files if not already cached."""
    marker = SSA_NAMES_DIR / "yob1990.txt"
    if marker.exists() and not force:
        print(f"  SSA national: cached ({SSA_NAMES_DIR})")
        return

    print(f"  SSA national: downloading from {SSA_NATIONAL_URL}...")
    data = _fetch_url_curl(SSA_NATIONAL_URL)
    print(f"  SSA national: {len(data):,} bytes — extracting...")
    SSA_NAMES_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            # Extract only yobYYYY.txt files for the cohort range
            if member.startswith("yob") and member.endswith(".txt"):
                try:
                    year = int(member[3:7])
                except ValueError:
                    continue
                if year in COHORT_YEARS:
                    zf.extract(member, SSA_NAMES_DIR)
    count = sum(1 for _ in SSA_NAMES_DIR.glob("yob*.txt"))
    print(f"  SSA national: extracted {count} year files")


def download_ssa_state(force: bool = False) -> None:
    """Download and extract SSA state name files if not already cached."""
    # Only need southern state files; check for one as the cache marker.
    marker = SSA_STATE_DIR / "TX.TXT"
    if marker.exists() and not force:
        print(f"  SSA state: cached ({SSA_STATE_DIR})")
        return

    print(f"  SSA state: downloading from {SSA_STATE_URL}...")
    data = _fetch_url_curl(SSA_STATE_URL)
    print(f"  SSA state: {len(data):,} bytes — extracting...")
    SSA_STATE_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for member in zf.namelist():
            # Extract only the southern state .TXT files (e.g. TX.TXT)
            name = member.split("/")[-1]
            stem = name.replace(".TXT", "")
            if name.endswith(".TXT") and len(name) == 6 and stem in SOUTHERN_STATES:
                zf.extract(member, SSA_STATE_DIR)
    count = sum(1 for _ in SSA_STATE_DIR.glob("*.TXT"))
    print(f"  SSA state: extracted {count} southern state files")


def download_census(force: bool = False) -> None:
    """Download Census 2010 surname CSV if not already cached.

    The Census server is more permissive than SSA — the file is inside a zip
    at a different URL than the brief specifies. We download the zip and extract.
    """
    if CENSUS_CSV.exists() and not force:
        print(f"  Census surnames: cached ({CENSUS_CSV})")
        return

    # The Census direct CSV URL returns 404; the file lives in a zip.
    census_zip_url = "https://www2.census.gov/topics/genealogy/2010surnames/names.zip"
    print(f"  Census surnames: downloading from {census_zip_url}...")
    result = subprocess.run(
        ["curl", "-L", "-s", "--fail", census_zip_url,
         "-H", "User-Agent: curl/8.7.1"],
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"curl failed for Census zip: {result.stderr.decode()[:200]}"
        )
    data = result.stdout
    print(f"  Census surnames: {len(data):,} bytes — extracting CSV...")
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        with zf.open("Names_2010Census.csv") as src:
            CENSUS_CSV.write_bytes(src.read())
    print(f"  Census surnames: saved to {CENSUS_CSV}")


# ---------------------------------------------------------------------------
# Corpus builders
# ---------------------------------------------------------------------------

def build_general_first_names() -> tuple[list[list], list[list]]:
    """
    Aggregate SSA national data for 1990–2010.
    Returns (male_general, female_general) as lists of [name, count] sorted desc.
    """
    male_counts: dict[str, int] = defaultdict(int)
    female_counts: dict[str, int] = defaultdict(int)

    missing_years = []
    for year in COHORT_YEARS:
        path = SSA_NAMES_DIR / f"yob{year}.txt"
        if not path.exists():
            missing_years.append(year)
            continue
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 3:
                    continue
                name, sex, count_str = parts
                count = int(count_str)
                if sex == "M":
                    male_counts[name] += count
                elif sex == "F":
                    female_counts[name] += count

    if missing_years:
        print(f"  WARNING: missing SSA national files for years: {missing_years}", file=sys.stderr)

    male_general = sorted(
        [[n, c] for n, c in male_counts.items() if c >= GENERAL_MIN_COUNT],
        key=lambda x: x[1], reverse=True,
    )
    female_general = sorted(
        [[n, c] for n, c in female_counts.items() if c >= GENERAL_MIN_COUNT],
        key=lambda x: x[1], reverse=True,
    )
    return male_general, female_general


def build_southern_first_names() -> tuple[list[list], list[list]]:
    """
    Aggregate SSA state data for southern states 1990–2010.
    State files format: ST,Sex,Year,Name,Count
    Returns (male_southern, female_southern).
    """
    male_counts: dict[str, int] = defaultdict(int)
    female_counts: dict[str, int] = defaultdict(int)

    found_states = set()
    missing_states = []
    for state in SOUTHERN_STATES:
        path = SSA_STATE_DIR / f"{state}.TXT"
        if not path.exists():
            missing_states.append(state)
            continue
        found_states.add(state)
        with path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                if len(parts) != 5:
                    continue
                st, sex, year_str, name, count_str = parts
                year = int(year_str)
                if year not in COHORT_YEARS:
                    continue
                count = int(count_str)
                if sex == "M":
                    male_counts[name] += count
                elif sex == "F":
                    female_counts[name] += count

    if missing_states:
        print(f"  WARNING: missing SSA state files for: {missing_states}", file=sys.stderr)

    print(f"  Southern states found: {sorted(found_states)}")

    male_southern = sorted(
        [[n, c] for n, c in male_counts.items() if c >= SOUTHERN_MIN_COUNT],
        key=lambda x: x[1], reverse=True,
    )
    female_southern = sorted(
        [[n, c] for n, c in female_counts.items() if c >= SOUTHERN_MIN_COUNT],
        key=lambda x: x[1], reverse=True,
    )
    return male_southern, female_southern


def build_surnames() -> list[list]:
    """
    Parse Census 2010 surname CSV.
    Keeps surnames with count >= SURNAME_MIN_COUNT, normalised to title case.
    Returns list of [name, count] sorted desc by count.
    """
    if not CENSUS_CSV.exists():
        raise FileNotFoundError(f"Census CSV not found: {CENSUS_CSV}")

    surnames: list[list] = []
    with CENSUS_CSV.open(newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name_raw = row.get("name", "").strip()
            count_raw = row.get("count", "").strip()
            if not name_raw or not count_raw:
                continue
            # Skip header artifacts or non-numeric counts
            try:
                count = int(count_raw.replace(",", ""))
            except ValueError:
                continue
            if count < SURNAME_MIN_COUNT:
                continue
            # Skip aggregate/catch-all rows in the Census file
            if name_raw.upper() in {"ALL OTHER NAMES", "ALL NAMES"}:
                continue
            # Normalise from uppercase to title case
            name = name_raw.title()
            surnames.append([name, count])

    surnames.sort(key=lambda x: x[1], reverse=True)
    return surnames


# ---------------------------------------------------------------------------
# Corpus assembly
# ---------------------------------------------------------------------------

def build_corpus() -> dict:
    print("Building general first names...")
    male_general, female_general = build_general_first_names()
    print(f"  male_first.general:   {len(male_general):,} entries")
    print(f"  female_first.general: {len(female_general):,} entries")

    print("Building southern first names...")
    male_southern, female_southern = build_southern_first_names()
    print(f"  male_first.southern:   {len(male_southern):,} entries")
    print(f"  female_first.southern: {len(female_southern):,} entries")

    print("Building surnames...")
    surnames = build_surnames()
    print(f"  surnames: {len(surnames):,} entries")

    corpus = {
        "version": "1.0",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "male_first": {
            "general": male_general,
            "southern": male_southern,
        },
        "female_first": {
            "general": female_general,
            "southern": female_southern,
        },
        "surnames": surnames,
        "whimsy": WHIMSY_POOL,
    }
    return corpus


def write_corpus(corpus: dict) -> None:
    SEED_DIR.mkdir(parents=True, exist_ok=True)
    CORPUS_JSON.write_text(json.dumps(corpus, ensure_ascii=False, separators=(",", ":")))
    size_kb = CORPUS_JSON.stat().st_size / 1024
    print(f"Wrote {CORPUS_JSON} ({size_kb:.1f} KB)")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_corpus(corpus: dict) -> bool:
    """Validate corpus against spec criteria. Returns True if all pass."""
    checks: list[tuple[str, bool]] = []

    mg = corpus.get("male_first", {}).get("general", [])
    fg = corpus.get("female_first", {}).get("general", [])
    ms = corpus.get("male_first", {}).get("southern", [])
    fs = corpus.get("female_first", {}).get("southern", [])
    sur = corpus.get("surnames", [])
    whi = corpus.get("whimsy", [])

    checks.append(("male_first.general >= 500", len(mg) >= 500))
    checks.append(("female_first.general >= 500", len(fg) >= 500))
    checks.append(("male_first.southern >= 100", len(ms) >= 100))
    checks.append(("female_first.southern >= 100", len(fs) >= 100))
    checks.append(("surnames >= 2000", len(sur) >= 2000))
    checks.append(("whimsy == 93", len(whi) == 93))

    # All weights positive integers
    def all_positive_ints(lst: list[list]) -> bool:
        return all(isinstance(entry[1], int) and entry[1] > 0 for entry in lst)

    checks.append(("male_first.general weights positive", all_positive_ints(mg)))
    checks.append(("female_first.general weights positive", all_positive_ints(fg)))
    checks.append(("male_first.southern weights positive", all_positive_ints(ms)))
    checks.append(("female_first.southern weights positive", all_positive_ints(fs)))
    checks.append(("surnames weights positive", all_positive_ints(sur)))

    all_pass = True
    for label, ok in checks:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}")
        if not ok:
            all_pass = False

    # Print actual sizes for reference
    print(f"\n  Actual sizes:")
    print(f"    male_first.general:   {len(mg):,}")
    print(f"    female_first.general: {len(fg):,}")
    print(f"    male_first.southern:  {len(ms):,}")
    print(f"    female_first.southern:{len(fs):,}")
    print(f"    surnames:             {len(sur):,}")
    print(f"    whimsy:               {len(whi)}")

    return all_pass


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build name_corpus.json from SSA and Census data"
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Validate existing corpus JSON only (no download or rebuild)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-download source files even if already cached"
    )
    args = parser.parse_args()

    if args.check:
        if not CORPUS_JSON.exists():
            print(f"ERROR: corpus not found at {CORPUS_JSON}", file=sys.stderr)
            sys.exit(1)
        print(f"Validating {CORPUS_JSON}...")
        with CORPUS_JSON.open() as f:
            corpus = json.load(f)
        ok = validate_corpus(corpus)
        sys.exit(0 if ok else 1)

    # Download phase
    print("=== Download phase ===")
    download_ssa_national(force=args.force)
    download_ssa_state(force=args.force)
    download_census(force=args.force)

    # Build phase
    print("\n=== Build phase ===")
    corpus = build_corpus()

    # Write
    print("\n=== Write phase ===")
    write_corpus(corpus)

    # Validate
    print("\n=== Validation ===")
    ok = validate_corpus(corpus)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
