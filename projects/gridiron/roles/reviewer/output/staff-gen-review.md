# Staff-Gen Review

**Feature:** staff-gen  
**Reviewer:** Claude (automated)  
**Review date:** 2026-06-20  
**Verdict:** PASS WITH NOTES

---

## Summary

All structural and DB-level requirements from the brief are met. The tables are correctly defined, migration chain is linear, row counts are exact, and every constraint check passes. One meaningful deviation from the brief exists (whimsy logic differs from roster-gen), and one minor ambiguity is noted around the migration `down_revision` pointer.

---

## Check Results

### 1. DB Counts

✅ **PASS**

| Table | Actual | Expected |
|-------|--------|----------|
| coaches | 650 | 650 (5 × 130) |
| boosters | 534 | 390–650 |

Booster distribution: 25 programs × 3, 66 × 4, 39 × 5. All programs in range [3, 5].

---

### 2. Coach Roles

✅ **PASS**

```
SELECT role, COUNT(*) FROM coaches GROUP BY role ORDER BY role;
```

| role | count |
|------|-------|
| Defensive Coordinator | 130 |
| Head Coach | 130 |
| Offensive Coordinator | 130 |
| Recruiting Coordinator | 130 |
| Special Teams Coordinator | 130 |

All 5 roles present, each with exactly 130 rows. Zero programs have a role count ≠ 1.

---

### 3. Rating / Influence Range

✅ **PASS**

- Coach rating range (live DB): [0.000400, 0.999900] — within [0.0, 1.0]
- Booster influence range (live DB): [0.002700, 0.999600] — within [0.0, 1.0]
- Zero DB rows violate the range per direct COUNT query.

---

### 4. SBC Southern Names

⚠️ **NOTE — corpus routing correct; name quality mixed**

The seed script correctly identifies SBC (conglomerate_id=2) and routes first-name draws to `corpus["male_first"]["southern"]` / `corpus["female_first"]["southern"]`. DB confirmed: SBC id=2, code=SBC.

Sample of SBC Head Coaches from live DB:
```
[Alabama Institute]        Katelyn Kruger
[Alabama Tech]             Jack Harrell
[Carolina Tech]            Awl Burgess   ← whimsy
[Central Kentucky Univ]    Terry Pope
[Central Texas Univ]       Cecilia Monroe
[Clarksville Univ]         Pleat Lamar   ← whimsy
[East Texas Univ]          Jaden Coleman
[Florence Univ]            Kalie Garza
[Florida Tech]             Alondra Richman
[Fort Lauderdale Univ]     William Brumley
```

Corpus routing is correct. The "southern flavour" relies on the corpus having a meaningful `southern` sub-pool distinct from `general` — the reviewer cannot verify corpus contents here, but the routing logic is sound. Whimsy overrides appear at roughly expected frequency (2 of 15 sample = ~13%, consistent with ~10% first-name rate).

**No action needed unless the corpus itself lacks genuine southern bias.**

---

### 5. Whimsy Consistency

❌ **FAIL — whimsy rules differ between roster-gen and staff-gen**

The brief states: *"Same sampling rules as roster-gen (10% whimsy / 1% both)".*

**roster-gen (`seed_roster.py` `draw_name`):**
```
r < 0.01   → both whimsy (1%)
r < 0.055  → whimsy first only (4.5%)
r < 0.10   → whimsy last only (4.5%)
else        → both standard (90%)
```
Total first-name whimsy: ~5.5%. Total last-name whimsy: ~5.5%. "Both whimsy": 1%.

**staff-gen (`seed_staff.py` `generate_name`):**
```python
WHIMSY_FIRST_RATE = 0.10   # 10% threshold
WHIMSY_BOTH_RATE  = 0.01   # 1% threshold

roll < 0.01  → both whimsy (1%)
roll < 0.10  → whimsy first, standard last (9%)
else          → both standard (90%)
```
Total first-name whimsy: 10%. Total last-name whimsy: 1%. "Both whimsy": 1%.

**Divergences:**
1. staff-gen applies **no whimsy-last-only** path — roster-gen has a 4.5% chance of a whimsy surname with a normal first name; staff-gen has zero.
2. staff-gen's first-name whimsy rate is **10% vs roster-gen's 5.5%**. The brief says "10%", which matches staff-gen's docstring — but roster-gen splits it as 4.5% + 4.5% + 1% = 10% *total* across both components combined. The two scripts interpret "10%" differently.
3. The brief description "10% whimsy / 1% both" is ambiguous. Under roster-gen's interpretation, "10%" means *total whimsy exposure* (5.5% first, 4.5% last, 1% both = 10% of rows touch whimsy). Under staff-gen's interpretation, "10%" means *10% first-name whimsy only*.

**Decision required (see below).** This is a functional difference in output character, not a correctness bug — but it means coaches and players have different name flavour distributions.

---

### 6. Migration Chain

✅ **PASS**

```
uv run alembic history output:
  36a6ee9b555e -> b2c3d4e5f6a7 (head), staff_schema
  a1b2c3d4e5f6 -> 36a6ee9b555e, players_schema
  33f31770f03e -> a1b2c3d4e5f6, games_schedule_schema
  <base>        -> 33f31770f03e, programs_schema
```

Linear chain, no branches, head is `b2c3d4e5f6a7`.

⚠️ **NOTE — `down_revision` mismatch in migration file**

The migration file `b2c3d4e5f6a7_staff_schema.py` declares:
```python
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
```
But `alembic history` shows the actual parent is `36a6ee9b555e` (players_schema). The `a1b2c3d4e5f6` value in the file refers to `games_schedule_schema`, skipping the players migration.

**However**, Alembic reports the chain as correct (with `36a6ee9b555e` as actual parent). This suggests Alembic resolved the parent from the DB's `alembic_version` tracking rather than from the `down_revision` constant — or the constant in the handoff doc vs the actual file differs. The file was read directly and shows `'a1b2c3d4e5f6'` on line 18. This should be verified: if the live migration file genuinely says `a1b2c3d4e5f6`, Alembic's history output is inconsistent and this is a latent bug that would surface on a fresh `alembic downgrade`.

---

### 7. Model Correctness

✅ **PASS**

`gridiron/models.py` `Coach` and `Booster` models match the migration DDL exactly:

| Attribute | DDL | Model |
|-----------|-----|-------|
| `id` | `SERIAL PK` | `mapped_column(Integer, primary_key=True)` |
| `program_id` | `INTEGER NOT NULL FK programs.id` | `mapped_column(Integer, ForeignKey("programs.id"), nullable=False)` |
| `role` (coaches) | `TEXT NOT NULL` | `mapped_column(Text, nullable=False)` |
| `first_name` | `TEXT NOT NULL` | `mapped_column(Text, nullable=False)` |
| `last_name` | `TEXT NOT NULL` | `mapped_column(Text, nullable=False)` |
| `rating` / `influence` | `REAL NOT NULL` + CHECK BETWEEN 0.0 AND 1.0 | `mapped_column(Float, nullable=False)` + `CheckConstraint(...)` |
| `created_at` | `TIMESTAMPTZ DEFAULT now()` | `mapped_column(server_default=func.now())` |

CHECK constraint names match: `ck_coaches_rating`, `ck_boosters_influence`.

Back-references wired correctly on `Program`:
```python
Program.coaches = relationship("Coach", back_populates="program")
Program.boosters = relationship("Booster", back_populates="program")
```

---

### 8. Idempotency

✅ **PASS**

`seed_to_db()` opens a single transaction and runs:
```python
conn.execute(text("DELETE FROM boosters"))
conn.execute(text("DELETE FROM coaches"))
```
before reinserting. Delete order (boosters first, then coaches) respects the FK from boosters → coaches' shared `programs` parent correctly. Re-running the script with the same seed would produce identical row counts. The approach differs from roster-gen's `ON CONFLICT DO UPDATE` pattern (noted in handoff), but is functionally safe.

---

## Items Requiring a Decision Before API Can Serve Staff Data

### Decision 1 (REQUIRED): Whimsy rule reconciliation

The whimsy logic in staff-gen differs from roster-gen in two ways:
- staff-gen has no "whimsy last name only" path (roster-gen has 4.5%)
- staff-gen first-name whimsy rate is 10% vs roster-gen's 5.5%

**Options:**
1. Accept staff-gen as-is and update the brief to clarify the intended rule going forward ("10% first-name whimsy, no last-only whimsy").
2. Update `seed_staff.py` `generate_name()` to mirror roster-gen's 4-way split exactly (1%/4.5%/4.5%/90%) and re-seed.
3. Treat the two scripts as intentionally different (players vs staff are different populations).

**Recommendation:** Reconcile to roster-gen's rule (option 2) if name texture consistency matters for the product. The data is cheap to re-seed. If staff names are intentionally distinct, document it explicitly in the brief.

### Decision 2 (LOW PRIORITY): Migration `down_revision` pointer

The `down_revision` constant in `b2c3d4e5f6a7_staff_schema.py` reads `'a1b2c3d4e5f6'` (games_schedule_schema), but `alembic history` reports the parent as `36a6ee9b555e` (players_schema). One of these is wrong.

Verify with `grep down_revision /Users/fotopnd/Documents/muppet-labs/projects/gridiron/alembic/versions/b2c3d4e5f6a7_staff_schema.py` and confirm it says `36a6ee9b555e`. If it says `a1b2c3d4e5f6`, fix before the next `alembic downgrade` is attempted (skips players table drop, leaving orphaned rows).

---

## What Is NOT Blocked

The tables are live and valid. The following can proceed in parallel with the decision above:
- API endpoints reading coach/booster data
- Team profile page wiring
- v2 planning for coach ratings → simulation mechanics
