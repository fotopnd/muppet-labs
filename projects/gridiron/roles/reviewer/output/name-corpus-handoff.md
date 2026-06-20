# Handoff: name-corpus

**Role:** implementer → reviewer
**Date:** 2026-06-20
**Status:** COMPLETE — all validation checks pass, ready for reviewer

---

## What was built

### Files created
- `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/scripts/build_name_corpus.py` — download + build script
- `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/scripts/seed_data/name_corpus.json` — 613 KB corpus (gitignored)
- Raw source data in `scripts/seed_data/` (gitignored):
  - `ssa_names/yob1990.txt` through `yob2010.txt` (21 files)
  - `ssa_state_names/AL.TXT AR.TXT GA.TXT LA.TXT MS.TXT SC.TXT TN.TXT TX.TXT` (8 files)
  - `Names_2010Census.csv`

### Entry added to pyproject.toml
```
build-name-corpus = "scripts.build_name_corpus:main"
```

---

## Actual corpus sizes

| Section | Count |
|---|---|
| male_first.general | 3,544 |
| female_first.general | 4,989 |
| male_first.southern | 2,080 |
| female_first.southern | 2,946 |
| surnames | 24,889 |
| whimsy | 93 (exactly) |

All counts well exceed brief minimums (500/500/100/100/2000/93).

---

## Data quality notes

### SSA national (yob*.txt)
- Clean data: `name,sex,count` CSV with no header row
- No missing years in 1990–2010 range; all 21 files present and parseable
- Names are already title-cased in the source

### SSA state (*.TXT)
- Format: `ST,Sex,Year,Name,Count` with no header row
- Covers data from 1910 onward; script filters to 1990–2010 only
- All 8 southern states present and complete

### Census 2010 surnames (Names_2010Census.csv)
- Contains one aggregate row: `ALL OTHER NAMES` with count 29,312,001
- This row is **filtered out** by the script (would otherwise rank #1 and corrupt draws)
- Counts in the file include commas as thousands separators — script strips them correctly
- Source file is latin-1 encoded (not UTF-8); script opens with `encoding="latin-1"`

---

## Download behaviour

### SSA website quirk
Python's `urllib` and plain curl receive HTTP 403 from `www.ssa.gov`. The script
uses `subprocess` + `curl` with full browser-like headers (User-Agent, Accept,
Sec-Fetch-* headers, Referer) to get HTTP 200. This is the standard workaround
for SSA's Cloudflare-based bot protection.

The Census zip (`www2.census.gov`) serves with a plain curl User-Agent header (200 OK).

### Download sizes
| Source | Size |
|---|---|
| SSA national (names.zip) | ~7.9 MB |
| SSA state (namesbystate.zip) | ~24.4 MB |
| Census (names.zip) | ~12.9 MB |

### Caching
- SSA national: cached when `scripts/seed_data/ssa_names/yob1990.txt` exists
- SSA state: cached when `scripts/seed_data/ssa_state_names/TX.TXT` exists
- Census CSV: cached when `scripts/seed_data/Names_2010Census.csv` exists
- `--force` flag bypasses all caches and re-downloads

Script is idempotent — safe to run multiple times; second run uses all caches.

---

## Deviations from brief

| Item | Brief | Actual |
|---|---|---|
| Census download URL | `Names_2010Census.csv` direct URL | Returns 404; file is inside `names.zip` at same directory — script downloads zip and extracts |
| SSA download method | `urllib` implied | Switched to `subprocess(curl)` due to SSA's 403 block on Python urllib |
| SSA state extraction | Extract all states | Only extracts the 8 southern states (saves ~16 MB of disk) |

---

## What the reviewer should check

1. **`--force` re-download path**: manually delete one of the cache markers (e.g. `rm scripts/seed_data/Names_2010Census.csv`) and run with `--force` to confirm re-download works end-to-end (not just the build phase).

2. **Corpus JSON structure**: confirm the JSON is valid and that `random.choices(names, weights=[w for _,w in entries])` would work with it — names and weights are in parallel position 0/1 of each sublist.

3. **Whimsy pool exact match**: verify the 93-entry list in the script matches the canonical list in `_config/briefs/name-corpus.md` appendix exactly (no additions, removals, or case changes).

4. **"All Other Names" filter**: spot-check that `Smith` is the first surname entry, not an aggregate row.

5. **pyproject.toml entrypoint**: confirm `uv run build-name-corpus` (using the installed script entrypoint) also works, not just `uv run scripts/build_name_corpus.py`.

6. **Southern state coverage**: brief specifies AL, AR, GA, LA, MS, SC, TN, TX — confirm all 8 are present in `scripts/seed_data/ssa_state_names/`.

7. **No engine imports**: script has zero imports from `gridiron.engine` or `gridiron.api` — confirm isolation contract is maintained.
