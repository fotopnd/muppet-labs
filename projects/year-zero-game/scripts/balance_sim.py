"""Balance simulator for GORK-3 — simplified session model.

Runs N simulated playthroughs without touching the live game_sessions /
player_decisions tables. Results are stored in scripts/sim_results.db.

Mirrors the game logic in web/src/game/useGameState.ts exactly:
  - Flat card pool, 15 cards per session, 2 escalations max
  - Session always ends as SESSION_COMPLETE
  - No resource bars, no phases, no game-over conditions

Strategies
----------
oracle        Always correct, never escalate.
random        Uniform random ACCEPT/REJECT, 10% ESCALATE.
agree         Follow GORK when visible; 50/50 otherwise.
disagree      Oppose GORK when visible; 50/50 otherwise.
human_casual  60% solo accuracy, partially swayed by GORK tier, 8% escalate.
human_expert  80% solo accuracy, well-calibrated GORK trust, 3% escalate.

Usage
-----
  uv run balance-sim                               # human_casual, 200 runs
  uv run balance-sim --strategy all --runs 500
  uv run balance-sim --strategy oracle --runs 1000 --seed 42
  uv run balance-sim --report                      # summary of recent runs
  uv run balance-sim --cards                       # per-card difficulty table
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

DB_PATH = Path(__file__).parent / "sim_results.db"

# ── Constants (mirrors web/src/game/constants.ts) ─────────────────────────────

CARDS_PER_SESSION = 15
ESC_PER_SESSION   = 2

# ── Strategy accuracy tables ───────────────────────────────────────────────────

# P(correct | condition) when GORK is shown for that tier.
# tier_1 is inverted — casual users follow it and get hurt.
TIER_ACCURACY: dict[str, dict[str, float]] = {
    "human_casual": {
        "none":   0.60,
        "tier_1": 0.38,
        "tier_2": 0.67,
        "tier_3": 0.78,
    },
    "human_expert": {
        "none":   0.80,
        "tier_1": 0.72,
        "tier_2": 0.80,
        "tier_3": 0.88,
    },
}

ESCALATE_RATE: dict[str, float] = {
    "human_casual": 0.08,
    "human_expert": 0.03,
}

# ── Card dataclass ─────────────────────────────────────────────────────────────

@dataclass
class SimCard:
    id: int
    is_harmful: bool
    gork_verdict: bool | None
    gork_confidence: float | None
    harm_category: str
    generation_tier: int
    target_condition_mix: dict[str, float]


# ── Condition sampling ─────────────────────────────────────────────────────────

def sample_condition(mix: dict[str, float], rng: random.Random) -> str:
    keys   = list(mix.keys())
    weights = [mix[k] for k in keys]
    return rng.choices(keys, weights=weights, k=1)[0]


# ── Strategy functions ─────────────────────────────────────────────────────────

def decide_oracle(card: SimCard, condition: str, _rng: random.Random, _esc_left: int) -> str:
    return "REJECT" if card.is_harmful else "ACCEPT"


def decide_random(card: SimCard, condition: str, rng: random.Random, esc_left: int) -> str:
    if esc_left > 0:
        return rng.choices(["ACCEPT", "REJECT", "ESCALATE"], weights=[45, 45, 10])[0]
    return rng.choice(["ACCEPT", "REJECT"])


def decide_agree(card: SimCard, condition: str, rng: random.Random, esc_left: int) -> str:
    if condition != "none" and card.gork_verdict is not None:
        return "REJECT" if card.gork_verdict else "ACCEPT"
    return rng.choice(["ACCEPT", "REJECT"])


def decide_disagree(card: SimCard, condition: str, rng: random.Random, esc_left: int) -> str:
    if condition != "none" and card.gork_verdict is not None:
        return "ACCEPT" if card.gork_verdict else "REJECT"
    return rng.choice(["ACCEPT", "REJECT"])


def _decide_probabilistic(
    strategy: str,
    card: SimCard,
    condition: str,
    rng: random.Random,
    esc_left: int,
) -> str:
    if esc_left > 0 and rng.random() < ESCALATE_RATE[strategy]:
        return "ESCALATE"
    p_correct = TIER_ACCURACY[strategy][condition]
    correct   = "REJECT" if card.is_harmful else "ACCEPT"
    wrong     = "ACCEPT" if card.is_harmful else "REJECT"
    return correct if rng.random() < p_correct else wrong


def decide_human_casual(card: SimCard, condition: str, rng: random.Random, esc_left: int) -> str:
    return _decide_probabilistic("human_casual", card, condition, rng, esc_left)


def decide_human_expert(card: SimCard, condition: str, rng: random.Random, esc_left: int) -> str:
    return _decide_probabilistic("human_expert", card, condition, rng, esc_left)


STRATEGIES: dict[str, object] = {
    "oracle":       decide_oracle,
    "random":       decide_random,
    "agree":        decide_agree,
    "disagree":     decide_disagree,
    "human_casual": decide_human_casual,
    "human_expert": decide_human_expert,
}

# ── Decision record ────────────────────────────────────────────────────────────

@dataclass
class DecisionRecord:
    card_id: int
    harm_category: str
    generation_tier: int
    condition: str
    gork_verdict: bool | None
    verdict: str
    player_correct: bool
    agreed_with_agent: bool | None


@dataclass
class SessionResult:
    strategy: str
    total_decisions: int
    correct_decisions: int
    total_escalated: int
    total_agreements: int
    total_overrides: int
    decisions: list[DecisionRecord] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct_decisions / self.total_decisions if self.total_decisions else 0.0

    @property
    def agreement_rate(self) -> float:
        n = self.total_agreements + self.total_overrides
        return self.total_agreements / n if n else 0.0


# ── Session runner ─────────────────────────────────────────────────────────────

def run_session(
    strategy_fn,
    card_pool: list[SimCard],
    strategy_name: str,
    rng: random.Random,
) -> SessionResult:
    cards = rng.sample(card_pool, min(CARDS_PER_SESSION, len(card_pool)))
    esc_left = ESC_PER_SESSION

    total_decisions   = 0
    correct_decisions = 0
    total_escalated   = 0
    total_agreements  = 0
    total_overrides   = 0
    decisions: list[DecisionRecord] = []

    for card in cards:
        condition = sample_condition(card.target_condition_mix, rng)
        verdict   = strategy_fn(card, condition, rng, esc_left)

        is_escalate = verdict == "ESCALATE"
        if is_escalate:
            esc_left       -= 1
            total_escalated += 1
            player_correct  = False
            agreed          = None
        else:
            player_correct = (verdict == "REJECT") == card.is_harmful
            total_decisions   += 1
            correct_decisions += int(player_correct)
            if condition == "none" or card.gork_verdict is None:
                agreed = None
            else:
                agreed = (verdict == "REJECT") == card.gork_verdict
                if agreed:
                    total_agreements += 1
                else:
                    total_overrides += 1

        decisions.append(DecisionRecord(
            card_id=card.id,
            harm_category=card.harm_category,
            generation_tier=card.generation_tier,
            condition=condition,
            gork_verdict=card.gork_verdict,
            verdict=verdict,
            player_correct=player_correct,
            agreed_with_agent=agreed,
        ))

    return SessionResult(
        strategy=strategy_name,
        total_decisions=total_decisions,
        correct_decisions=correct_decisions,
        total_escalated=total_escalated,
        total_agreements=total_agreements,
        total_overrides=total_overrides,
        decisions=decisions,
    )


# ── SQLite persistence ─────────────────────────────────────────────────────────

def init_sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sim_runs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            run_at     TEXT    NOT NULL,
            strategy   TEXT    NOT NULL,
            n_sessions INTEGER NOT NULL,
            seed       INTEGER
        );
        CREATE TABLE IF NOT EXISTS sim_sessions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id            INTEGER NOT NULL REFERENCES sim_runs(id),
            strategy          TEXT    NOT NULL,
            total_decisions   INTEGER NOT NULL,
            correct_decisions INTEGER NOT NULL,
            accuracy          REAL    NOT NULL,
            total_escalated   INTEGER NOT NULL,
            total_agreements  INTEGER NOT NULL,
            total_overrides   INTEGER NOT NULL,
            agreement_rate    REAL    NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sim_card_decisions (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id            INTEGER NOT NULL REFERENCES sim_runs(id),
            strategy          TEXT    NOT NULL,
            card_id           INTEGER NOT NULL,
            harm_category     TEXT    NOT NULL,
            generation_tier   INTEGER NOT NULL,
            condition         TEXT    NOT NULL,
            gork_verdict      INTEGER,
            verdict           TEXT    NOT NULL,
            player_correct    INTEGER NOT NULL,
            agreed_with_agent INTEGER
        );
    """)
    conn.commit()
    return conn


def save_run(
    conn: sqlite3.Connection,
    strategy: str,
    n: int,
    seed: int | None,
    results: list[SessionResult],
) -> int:
    cur = conn.execute(
        "INSERT INTO sim_runs (run_at, strategy, n_sessions, seed) VALUES (?, ?, ?, ?)",
        (datetime.now(UTC).isoformat(), strategy, n, seed),
    )
    run_id = cur.lastrowid

    session_rows = [
        (run_id, r.strategy, r.total_decisions, r.correct_decisions,
         r.accuracy, r.total_escalated, r.total_agreements,
         r.total_overrides, r.agreement_rate)
        for r in results
    ]
    conn.executemany(
        """INSERT INTO sim_sessions
           (run_id, strategy, total_decisions, correct_decisions, accuracy,
            total_escalated, total_agreements, total_overrides, agreement_rate)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        session_rows,
    )

    card_rows = [
        (run_id, r.strategy, d.card_id, d.harm_category, d.generation_tier,
         d.condition, d.gork_verdict, d.verdict,
         int(d.player_correct),
         None if d.agreed_with_agent is None else int(d.agreed_with_agent))
        for r in results
        for d in r.decisions
    ]
    conn.executemany(
        """INSERT INTO sim_card_decisions
           (run_id, strategy, card_id, harm_category, generation_tier, condition,
            gork_verdict, verdict, player_correct, agreed_with_agent)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        card_rows,
    )

    conn.commit()
    return run_id


# ── Reporting ──────────────────────────────────────────────────────────────────

def print_summary(results: list[SessionResult], strategy: str, run_id: int) -> None:
    n = len(results)
    avg_acc    = sum(r.accuracy for r in results) / n
    avg_esc    = sum(r.total_escalated for r in results) / n
    avg_agree  = sum(r.agreement_rate for r in results) / n
    avg_over   = sum(r.total_overrides for r in results) / n

    # Override accuracy: among cards where player overrode GORK, % correct
    override_correct = sum(
        d.player_correct
        for r in results for d in r.decisions
        if d.agreed_with_agent is False
    )
    override_total = sum(
        1 for r in results for d in r.decisions
        if d.agreed_with_agent is False
    )
    override_acc = override_correct / override_total if override_total else 0.0

    # Accuracy by GORK tier
    tier_acc: dict[str, list[bool]] = {"tier_1": [], "tier_2": [], "tier_3": [], "none": []}
    for r in results:
        for d in r.decisions:
            if d.verdict != "ESCALATE":
                tier_acc.setdefault(d.condition, []).append(d.player_correct)

    w = 54
    print(f"\n{'─'*w}")
    print(f"  run_id={run_id}  strategy={strategy}  n={n}")
    print(f"{'─'*w}")
    print(f"  Avg accuracy:           {100*avg_acc:.1f}%")
    print(f"  Avg correct / session:  {avg_acc*CARDS_PER_SESSION:.1f} / {CARDS_PER_SESSION}")
    print(f"  Avg escalations:        {avg_esc:.2f} / {ESC_PER_SESSION}")
    print(f"  Avg overrides:          {avg_over:.1f}")
    print(f"  Override accuracy:      {100*override_acc:.1f}%")
    print(f"  Agreement rate:         {100*avg_agree:.1f}%")
    print(f"{'─'*w}")
    print(f"  Accuracy by GORK tier:")
    for tier in ("none", "tier_1", "tier_2", "tier_3"):
        pool = tier_acc.get(tier, [])
        if pool:
            print(f"    {tier:<8}  {100*sum(pool)/len(pool):.1f}%  (n={len(pool)})")
        else:
            print(f"    {tier:<8}  — (not sampled)")
    print(f"{'─'*w}\n")


def cmd_report(conn: sqlite3.Connection) -> None:
    rows = conn.execute("""
        SELECT r.id, r.run_at, r.strategy, r.n_sessions,
               AVG(s.accuracy), AVG(s.total_escalated), r.seed
        FROM sim_runs r
        JOIN sim_sessions s ON s.run_id = r.id
        GROUP BY r.id
        ORDER BY r.id DESC
        LIMIT 20
    """).fetchall()

    if not rows:
        print("No simulation runs found in", DB_PATH)
        return

    print(f"\n{'id':>4}  {'strategy':<14} {'n':>5}  {'acc':>6}  {'esc':>5}  {'seed':>8}  run_at")
    print("─" * 72)
    for rid, run_at, strat, n, avg_acc, avg_esc, seed in rows:
        print(f"{rid:>4}  {strat:<14} {n:>5}  {100*avg_acc:>5.1f}%  {avg_esc:>5.2f}  {str(seed or ''):>8}  {run_at[:19]}")
    print()


def cmd_cards(conn: sqlite3.Connection, strategy: str = "human_casual", run_id: int | None = None) -> None:
    """Print per-card difficulty ranked by player accuracy ascending."""
    run_filter = f"AND cd.run_id = {run_id}" if run_id else ""
    rows = conn.execute(f"""
        SELECT cd.card_id,
               cd.harm_category,
               cd.generation_tier,
               COUNT(*) as n,
               AVG(cd.player_correct) as acc,
               AVG(CASE WHEN cd.condition != 'none' THEN cd.player_correct END) as acc_gork,
               AVG(CASE WHEN cd.condition  = 'none' THEN cd.player_correct END) as acc_solo,
               AVG(cd.agreed_with_agent) as agree_rate,
               SUM(CASE WHEN cd.verdict = 'ESCALATE' THEN 1 ELSE 0 END)*1.0/COUNT(*) as esc_rate
        FROM sim_card_decisions cd
        JOIN sim_runs r ON r.id = cd.run_id
        WHERE r.strategy = ? {run_filter}
        GROUP BY cd.card_id
        HAVING n >= 20
        ORDER BY acc ASC
        LIMIT 30
    """, (strategy,)).fetchall()

    if not rows:
        print(f"No card data found for strategy={strategy}. Run some sessions first.")
        return

    print(f"\nPer-card difficulty (strategy={strategy}, hardest first)")
    print(f"{'id':>4}  {'category':<22} {'tier':>4}  {'n':>5}  {'acc':>6}  {'w/gork':>7}  {'solo':>6}  {'agree':>6}")
    print("─" * 74)
    for card_id, cat, tier, n, acc, acc_gork, acc_solo, agree_rate, esc_rate in rows:
        gork_str = f"{100*acc_gork:.0f}%" if acc_gork is not None else "   —"
        solo_str = f"{100*acc_solo:.0f}%" if acc_solo is not None else "  —"
        agree_str = f"{100*agree_rate:.0f}%" if agree_rate is not None else "  —"
        print(f"{card_id:>4}  {cat:<22} {tier:>4}  {n:>5}  {100*acc:>5.1f}%  {gork_str:>7}  {solo_str:>6}  {agree_str:>6}")
    print()


# ── Card loading ───────────────────────────────────────────────────────────────

async def load_cards() -> list[SimCard]:
    async with session_factory() as db:
        result = await db.execute(select(DocumentLibrary))
        docs = result.scalars().all()

    return [
        SimCard(
            id=doc.id,
            is_harmful=doc.is_harmful,
            gork_verdict=doc.gork_verdict,
            gork_confidence=doc.gork_confidence,
            harm_category=doc.harm_category,
            generation_tier=doc.generation_tier,
            target_condition_mix=doc.target_condition_mix,
        )
        for doc in docs
    ]


# ── Entry point ────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="GORK-3 balance simulator")
    parser.add_argument("--strategy", default="human_casual",
                        choices=[*STRATEGIES.keys(), "all"],
                        help="Player strategy (default: human_casual)")
    parser.add_argument("--runs", type=int, default=200,
                        help="Sessions per strategy (default: 200)")
    parser.add_argument("--seed", type=int, default=None,
                        help="RNG seed for reproducibility")
    parser.add_argument("--report", action="store_true",
                        help="Print summary of recent runs and exit")
    parser.add_argument("--cards", action="store_true",
                        help="Print per-card difficulty table and exit")
    parser.add_argument("--run-id", type=int, default=None,
                        help="Filter --cards to a specific run_id")
    args = parser.parse_args()

    conn = init_sqlite()

    if args.report:
        cmd_report(conn)
        return

    if args.cards:
        strat = args.strategy if args.strategy != "all" else "human_casual"
        cmd_cards(conn, strategy=strat, run_id=args.run_id)
        return

    try:
        card_pool = asyncio.run(load_cards())
    except Exception as exc:
        print(f"ERROR: Could not load cards — {exc}", file=sys.stderr)
        print("Is the database running? (docker compose up -d)", file=sys.stderr)
        sys.exit(1)

    if not card_pool:
        print("ERROR: No cards found. Run `uv run seed-library` first.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(card_pool)} cards from pool.")

    strategies_to_run = list(STRATEGIES.keys()) if args.strategy == "all" else [args.strategy]

    for strategy_name in strategies_to_run:
        strategy_fn = STRATEGIES[strategy_name]
        rng = random.Random(args.seed)

        print(f"Running {args.runs} sessions — strategy={strategy_name} ...", end=" ", flush=True)
        results = [
            run_session(strategy_fn, card_pool, strategy_name, rng)
            for _ in range(args.runs)
        ]
        print("done")

        run_id = save_run(conn, strategy_name, args.runs, args.seed, results)
        print_summary(results, strategy_name, run_id)

    conn.close()


if __name__ == "__main__":
    main()
