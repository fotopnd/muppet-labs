"""Balance simulator for GORK-3.

Runs N simulated playthroughs without touching the live game_sessions /
player_decisions tables. Results are stored in a local SQLite database at
scripts/sim_results.db, kept separate from production analytics.

Mirrors the game logic in web/src/game/useGameState.ts exactly.

Strategies
----------
oracle        Always correct, never escalate.
random        Uniform random over CLEAR/REDACT, 10 % chance ESCALATE.
agree         Follow GORK when visible; 50 % correct solo.
disagree      Oppose GORK when visible; 50 % correct solo.
human_casual  60 % solo accuracy, partially swayed by GORK per tier, 6 % escalate.
human_expert  80 % solo accuracy, well-calibrated GORK trust per tier, 3 % escalate.

Usage
-----
  uv run balance-sim --strategy human_casual --runs 200
  uv run balance-sim --strategy all --runs 500 --seed 42
  uv run balance-sim --report                     # print last run summary
"""
from __future__ import annotations

import argparse
import asyncio
import random
import sqlite3
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from year_zero.database import engine, session_factory
from year_zero.models import DocumentLibrary

# ── Paths ─────────────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "sim_results.db"

# ── Constants (mirror of web/src/game/constants.ts) ───────────────────────────

INITIAL_BARS = {
    "publicTrust": 50,
    "security": 20,
    "treasury": 70,
    "legitimacy": 60,
    "compliance": 50,
}

CARDS_PER_DAY = 10
MAX_DAYS = 5

ESCALATE_DELTA = (0, 0, -8, 0, 0)

# key: (verdict, gork_was_flagged, is_harmful)
BAR_MOVEMENT: dict[tuple[str, bool, bool], tuple[int, ...]] = {
    ("CLEAR",  True,  False): ( 4,  0,  0,  3, -3),
    ("CLEAR",  False, False): ( 3,  0,  0,  3,  2),
    ("REDACT", False, True):  ( 0, -6,  0,  2, -6),
    ("REDACT", True,  True):  ( 0, -5,  0,  2,  2),
    ("CLEAR",  False, True):  ( 0, 14,  0, -5,  6),
    ("CLEAR",  True,  True):  ( 0,  9,  0, -3, -4),
    ("REDACT", True,  False): (-7,  0,  0, -6,  2),
    ("REDACT", False, False): (-10, 0,  0, -8, -4),
}

GAME_OVER = {
    "publicTrust": ("min", 0,   "TRUST_ZERO"),
    "security":    ("max", 100, "SECURITY_MAX"),
    "treasury":    ("min", 0,   "TREASURY_ZERO"),
    "legitimacy":  ("min", 0,   "LEGITIMACY_ZERO"),
    "compliance":  ("max", 100, "COMPLIANCE_MAX"),
}

PHASE_TRIGGERS = {2: ("security", 40), 3: ("security", 70)}

# Condition accuracy lookup for probabilistic strategies:
# P(correct) given agent_condition tier
TIER_ACCURACY: dict[str, dict[str, float]] = {
    "human_casual": {
        "none":   0.60,
        "tier_1": 0.38,  # tier-1 inverted misleads; partially followed
        "tier_2": 0.65,
        "tier_3": 0.75,
    },
    "human_expert": {
        "none":   0.80,
        "tier_1": 0.72,  # expert trusts self over broken GORK
        "tier_2": 0.78,
        "tier_3": 0.88,
    },
}

ESCALATE_RATE: dict[str, float] = {
    "human_casual": 0.06,
    "human_expert": 0.03,
}

# ── Card dataclass ─────────────────────────────────────────────────────────────

@dataclass
class SimCard:
    id: int
    is_harmful: bool
    gork_verdict: bool | None
    generation_tier: int
    target_condition_mix: dict[str, float]


# ── Agent condition assignment (mirrors assign_condition but without DB side-effects) ──

def sample_condition(mix: dict[str, float], rng: random.Random) -> str:
    keys = list(mix.keys())
    weights = [mix[k] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


# ── Strategy functions ─────────────────────────────────────────────────────────

def decide_oracle(card: SimCard, condition: str, rng: random.Random) -> str:
    return "REDACT" if card.is_harmful else "CLEAR"


def decide_random(card: SimCard, condition: str, rng: random.Random) -> str:
    return rng.choices(["CLEAR", "REDACT", "ESCALATE"], weights=[45, 45, 10])[0]


def decide_agree(card: SimCard, condition: str, rng: random.Random) -> str:
    if condition != "none" and card.gork_verdict is not None:
        return "REDACT" if card.gork_verdict else "CLEAR"
    return rng.choice(["CLEAR", "REDACT"])


def decide_disagree(card: SimCard, condition: str, rng: random.Random) -> str:
    if condition != "none" and card.gork_verdict is not None:
        return "CLEAR" if card.gork_verdict else "REDACT"
    return rng.choice(["CLEAR", "REDACT"])


def _decide_probabilistic(strategy: str, card: SimCard, condition: str, rng: random.Random) -> str:
    if rng.random() < ESCALATE_RATE[strategy]:
        return "ESCALATE"
    p_correct = TIER_ACCURACY[strategy][condition]
    correct_verdict = "REDACT" if card.is_harmful else "CLEAR"
    wrong_verdict = "CLEAR" if card.is_harmful else "REDACT"
    return correct_verdict if rng.random() < p_correct else wrong_verdict


def decide_human_casual(card: SimCard, condition: str, rng: random.Random) -> str:
    return _decide_probabilistic("human_casual", card, condition, rng)


def decide_human_expert(card: SimCard, condition: str, rng: random.Random) -> str:
    return _decide_probabilistic("human_expert", card, condition, rng)


STRATEGIES: dict[str, object] = {
    "oracle":        decide_oracle,
    "random":        decide_random,
    "agree":         decide_agree,
    "disagree":      decide_disagree,
    "human_casual":  decide_human_casual,
    "human_expert":  decide_human_expert,
}

# ── Game simulation ────────────────────────────────────────────────────────────

@dataclass
class DecisionRecord:
    game_day: int
    phase: int
    condition: str
    verdict: str
    correct: bool
    agreed_with_agent: bool | None


@dataclass
class SessionResult:
    strategy: str
    days_survived: int
    total_decisions: int
    correct_decisions: int
    total_escalated: int
    total_agreements: int
    total_overrides: int
    phase_reached: int
    game_over_condition: str
    final_bars: dict[str, int]
    decisions: list[DecisionRecord] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct_decisions / self.total_decisions if self.total_decisions else 0.0

    @property
    def agreement_rate(self) -> float:
        n = self.total_agreements + self.total_overrides
        return self.total_agreements / n if n else 0.0


def clamp(v: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, v))


def apply_delta(bars: dict[str, int], delta: tuple[int, ...]) -> dict[str, int]:
    keys = list(INITIAL_BARS.keys())
    return {k: clamp(bars[k] + delta[i]) for i, k in enumerate(keys)}


def check_game_over(bars: dict[str, int]) -> str | None:
    for bar, (direction, value, reason) in GAME_OVER.items():
        v = bars[bar]
        if direction == "min" and v <= value:
            return reason
        if direction == "max" and v >= value:
            return reason
    return None


def resolve_phase(bars: dict[str, int], current: int) -> int:
    if current < 3 and bars["security"] >= PHASE_TRIGGERS[3][1]:
        return 3
    if current < 2 and bars["security"] >= PHASE_TRIGGERS[2][1]:
        return 2
    return current


def run_session(
    strategy_fn,
    phase_pools: dict[int, list[SimCard]],
    strategy_name: str,
    rng: random.Random,
) -> SessionResult:
    bars = dict(INITIAL_BARS)
    active_phase = 1
    game_over: str | None = None

    total_decisions = 0
    correct_decisions = 0
    total_escalated = 0
    total_agreements = 0
    total_overrides = 0
    phase_reached = 1
    decisions: list[DecisionRecord] = []

    for day in range(1, MAX_DAYS + 1):
        pool = phase_pools[active_phase]
        day_cards = rng.sample(pool, min(CARDS_PER_DAY, len(pool)))

        day_correct = 0
        day_escalated = 0

        for card in day_cards:
            condition = sample_condition(card.target_condition_mix, rng)
            verdict = strategy_fn(card, condition, rng)
            is_escalate = verdict == "ESCALATE"

            if is_escalate:
                delta = ESCALATE_DELTA
                player_correct = False
                agreed = None
            else:
                gork_flagged = condition != "none" and card.gork_verdict is True
                delta = list(BAR_MOVEMENT.get((verdict, gork_flagged, card.is_harmful), (0,) * 5))
                if condition == "none":
                    delta[4] = 0  # no compliance movement without GORK
                delta = tuple(delta)

                player_correct = (verdict == "REDACT") == card.is_harmful
                if condition == "none":
                    agreed = None
                else:
                    agreed = (verdict == "REDACT") == (card.gork_verdict is True)

            bars = apply_delta(bars, delta)
            game_over = check_game_over(bars)

            decisions.append(DecisionRecord(
                game_day=day,
                phase=active_phase,
                condition=condition,
                verdict=verdict,
                correct=player_correct,
                agreed_with_agent=agreed,
            ))

            if not is_escalate:
                total_decisions += 1
                if player_correct:
                    correct_decisions += 1
                    day_correct += 1
                if agreed is True:
                    total_agreements += 1
                elif agreed is False:
                    total_overrides += 1
            else:
                total_escalated += 1
                day_escalated += 1

            if game_over:
                return SessionResult(
                    strategy=strategy_name,
                    days_survived=day,
                    total_decisions=total_decisions,
                    correct_decisions=correct_decisions,
                    total_escalated=total_escalated,
                    total_agreements=total_agreements,
                    total_overrides=total_overrides,
                    phase_reached=phase_reached,
                    game_over_condition=game_over,
                    final_bars=bars,
                    decisions=decisions,
                )

        # Day-end treasury bonus if accuracy > 50 %
        day_card_decisions = CARDS_PER_DAY - day_escalated
        day_accuracy = day_correct / day_card_decisions if day_card_decisions else 0
        if day_accuracy > 0.5:
            bars = apply_delta(bars, (0, 0, 5, 0, 0))
            game_over = check_game_over(bars)
            if game_over:
                return SessionResult(
                    strategy=strategy_name,
                    days_survived=day,
                    total_decisions=total_decisions,
                    correct_decisions=correct_decisions,
                    total_escalated=total_escalated,
                    total_agreements=total_agreements,
                    total_overrides=total_overrides,
                    phase_reached=phase_reached,
                    game_over_condition=game_over,
                    final_bars=bars,
                    decisions=decisions,
                )

        if day == MAX_DAYS:
            return SessionResult(
                strategy=strategy_name,
                days_survived=MAX_DAYS,
                total_decisions=total_decisions,
                correct_decisions=correct_decisions,
                total_escalated=total_escalated,
                total_agreements=total_agreements,
                total_overrides=total_overrides,
                phase_reached=phase_reached,
                game_over_condition="DAYS_COMPLETE",
                final_bars=bars,
                decisions=decisions,
            )

        # Advance phase for next day
        active_phase = resolve_phase(bars, active_phase)
        phase_reached = max(phase_reached, active_phase)

    # Unreachable but satisfies type checker
    return SessionResult(
        strategy=strategy_name,
        days_survived=MAX_DAYS,
        total_decisions=total_decisions,
        correct_decisions=correct_decisions,
        total_escalated=total_escalated,
        total_agreements=total_agreements,
        total_overrides=total_overrides,
        phase_reached=phase_reached,
        game_over_condition="DAYS_COMPLETE",
        final_bars=bars,
        decisions=decisions,
    )


# ── SQLite persistence ─────────────────────────────────────────────────────────

def init_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sim_runs (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at    TEXT NOT NULL,
            strategy  TEXT NOT NULL,
            n_sessions INTEGER NOT NULL,
            seed      INTEGER,
            notes     TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sim_sessions (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id              INTEGER NOT NULL REFERENCES sim_runs(id),
            strategy            TEXT NOT NULL,
            days_survived       INTEGER NOT NULL,
            total_decisions     INTEGER NOT NULL,
            correct_decisions   INTEGER NOT NULL,
            accuracy            REAL NOT NULL,
            total_escalated     INTEGER NOT NULL,
            total_agreements    INTEGER NOT NULL,
            total_overrides     INTEGER NOT NULL,
            agreement_rate      REAL NOT NULL,
            phase_reached       INTEGER NOT NULL,
            game_over_condition TEXT NOT NULL,
            final_public_trust  INTEGER NOT NULL,
            final_security      INTEGER NOT NULL,
            final_treasury      INTEGER NOT NULL,
            final_legitimacy    INTEGER NOT NULL,
            final_compliance    INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_run(conn: sqlite3.Connection, strategy: str, n: int, seed: int | None, results: list[SessionResult]) -> int:
    cur = conn.execute(
        "INSERT INTO sim_runs (run_at, strategy, n_sessions, seed) VALUES (?, ?, ?, ?)",
        (datetime.now(UTC).isoformat(), strategy, n, seed),
    )
    run_id = cur.lastrowid
    rows = [
        (
            run_id, r.strategy, r.days_survived, r.total_decisions,
            r.correct_decisions, r.accuracy, r.total_escalated,
            r.total_agreements, r.total_overrides, r.agreement_rate,
            r.phase_reached, r.game_over_condition,
            r.final_bars["publicTrust"], r.final_bars["security"],
            r.final_bars["treasury"], r.final_bars["legitimacy"],
            r.final_bars["compliance"],
        )
        for r in results
    ]
    conn.executemany(
        """INSERT INTO sim_sessions
           (run_id, strategy, days_survived, total_decisions, correct_decisions,
            accuracy, total_escalated, total_agreements, total_overrides,
            agreement_rate, phase_reached, game_over_condition,
            final_public_trust, final_security, final_treasury,
            final_legitimacy, final_compliance)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        rows,
    )
    conn.commit()
    return run_id


# ── Reporting ──────────────────────────────────────────────────────────────────

def print_summary(results: list[SessionResult], strategy: str, run_id: int) -> None:
    n = len(results)
    conditions = {}
    for r in results:
        conditions.setdefault(r.game_over_condition, 0)
        conditions[r.game_over_condition] += 1

    avg_acc   = sum(r.accuracy for r in results) / n
    avg_days  = sum(r.days_survived for r in results) / n
    avg_agree = sum(r.agreement_rate for r in results) / n
    avg_esc   = sum(r.total_escalated for r in results) / n

    complete = conditions.get("DAYS_COMPLETE", 0)

    print(f"\n{'─'*54}")
    print(f"  run_id={run_id}  strategy={strategy}  n={n}")
    print(f"{'─'*54}")
    print(f"  Complete (5 days):  {complete:4d}  ({100*complete/n:.1f}%)")
    for cond, cnt in sorted(conditions.items(), key=lambda x: -x[1]):
        if cond == "DAYS_COMPLETE":
            continue
        print(f"  {cond:<22} {cnt:4d}  ({100*cnt/n:.1f}%)")
    print(f"{'─'*54}")
    print(f"  Avg days survived:  {avg_days:.2f}")
    print(f"  Avg accuracy:       {100*avg_acc:.1f}%")
    print(f"  Avg agreement rate: {100*avg_agree:.1f}%")
    print(f"  Avg escalations:    {avg_esc:.1f}")
    print(f"{'─'*54}\n")


def cmd_report(conn: sqlite3.Connection) -> None:
    rows = conn.execute("""
        SELECT r.id, r.run_at, r.strategy, r.n_sessions,
               AVG(s.days_survived), AVG(s.accuracy),
               SUM(CASE WHEN s.game_over_condition='DAYS_COMPLETE' THEN 1 ELSE 0 END)*1.0/COUNT(*),
               r.seed
        FROM sim_runs r
        JOIN sim_sessions s ON s.run_id = r.id
        GROUP BY r.id
        ORDER BY r.id DESC
        LIMIT 20
    """).fetchall()

    if not rows:
        print("No simulation runs found in", DB_PATH)
        return

    print(f"\n{'id':>4}  {'strategy':<14} {'n':>5}  {'days':>5}  {'acc':>6}  {'complete%':>9}  {'seed':>8}  run_at")
    print("─" * 80)
    for r in rows:
        rid, run_at, strat, n, avg_days, avg_acc, complete_rate, seed = r
        print(f"{rid:>4}  {strat:<14} {n:>5}  {avg_days:>5.2f}  {100*avg_acc:>5.1f}%  {100*complete_rate:>8.1f}%  {str(seed):>8}  {run_at[:19]}")
    print()


# ── Card loading ───────────────────────────────────────────────────────────────

async def load_cards() -> dict[int, list[SimCard]]:
    async with session_factory() as db:
        result = await db.execute(select(DocumentLibrary))
        docs = result.scalars().all()

    phase_pools: dict[int, list[SimCard]] = {1: [], 2: [], 3: []}

    for doc in docs:
        card = SimCard(
            id=doc.id,
            is_harmful=doc.is_harmful,
            gork_verdict=doc.gork_verdict,
            generation_tier=doc.generation_tier,
            target_condition_mix=doc.target_condition_mix,
        )
        phase_pools[doc.phase].append(card)

    return phase_pools


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GORK-3 balance simulator")
    parser.add_argument("--strategy", default="human_casual",
                        choices=[*STRATEGIES.keys(), "all"],
                        help="Player strategy to simulate (default: human_casual)")
    parser.add_argument("--runs", type=int, default=200,
                        help="Number of sessions to simulate (default: 200)")
    parser.add_argument("--seed", type=int, default=None,
                        help="RNG seed for reproducibility")
    parser.add_argument("--report", action="store_true",
                        help="Print summary of recent runs and exit")
    args = parser.parse_args()

    conn = init_sqlite()

    if args.report:
        cmd_report(conn)
        return

    strategies_to_run = list(STRATEGIES.keys()) if args.strategy == "all" else [args.strategy]

    try:
        phase_pools = asyncio.run(load_cards())
    except Exception as exc:
        print(f"ERROR: Could not load cards from database — {exc}", file=sys.stderr)
        print("Is the database running? (docker compose up -d)", file=sys.stderr)
        sys.exit(1)

    if not phase_pools[1]:
        print("ERROR: No phase-1 cards found. Run `uv run seed-library` first.", file=sys.stderr)
        sys.exit(1)

    for strategy_name in strategies_to_run:
        strategy_fn = STRATEGIES[strategy_name]
        rng = random.Random(args.seed)

        print(f"Running {args.runs} sessions with strategy={strategy_name} ...", end=" ", flush=True)
        results = [
            run_session(strategy_fn, phase_pools, strategy_name, rng)
            for _ in range(args.runs)
        ]
        print("done")

        run_id = save_run(conn, strategy_name, args.runs, args.seed, results)
        print_summary(results, strategy_name, run_id)

    conn.close()


if __name__ == "__main__":
    main()
