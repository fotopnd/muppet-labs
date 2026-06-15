# Game Mechanics — Year Zero Game

**Updated:** 2026-06-15 (v2 — Reigns-style meter loop, no time limit)

---

## Core Inspiration: Reigns

The game is structurally modelled on Reigns: one card at a time, swipe left or right, each decision moves multiple stat bars in different directions. The player tries to keep all bars balanced indefinitely. The game ends when any bar hits 0 or max. There is no time limit and no fixed number of days — the game continues until the player loses.

---

## The Five Bars

All five bars are visible to the player at all times. Each bar runs 0–100. Game over if any bar reaches a danger threshold.

**Visual design note:** the first four bars have a single danger end (PUBLIC TRUST dangers at 0; SECURITY dangers at 100, etc.) and should be styled with a gradient toward that end. COMPLIANCE is different — it has danger zones at *both* 0 and 100, with the target in the middle. It should be styled with a centre-marker or dual-gradient to make clear the goal is balance, not maximising or minimising. This is the only bar where "doing well" looks like staying centred.

| Bar | Icon | Pushed UP by | Pushed DOWN by | Game over condition |
|-----|------|-------------|----------------|---------------------|
| **PUBLIC TRUST** | 🏛 | Correct CLEARs | False positives (blocking benign petitions) | → 0: citizens stop filing, Registry collapses |
| **SECURITY** | ⚠ | Correct REDACTs | False negatives (clearing harmful content) | → 100: security incident, regime remnants exploit the gap |
| **TREASURY** | 💰 | Correct solo decisions | Escalations to Review Board | → 0: Registry defunded, operations cease |
| **LEGITIMACY** | 🌍 | Balanced decisions | High REDACT rate (over-censorship) | → 0: international community withdraws recognition |
| **COMPLIANCE** | 🤖 | Agreeing with Sovereign-9 | Overriding Sovereign-9 | → 100: rubber stamp ("your decisions are indistinguishable from the machine's") → 0: total distrust ("no automated system can function under constant override") |

**The core tension:** COMPLIANCE is the meta-bar. You cannot always REDACT (kills LEGITIMACY), always CLEAR (spikes SECURITY), or always agree with the machine (maxes COMPLIANCE). Correct play requires calibrating trust in Sovereign-9 — agreeing when it happens to be right, overriding when it's wrong. As the model tier upgrades per category, the correct COMPLIANCE level for that category naturally rises.

**Why COMPLIANCE is different from the others:** it measures the *human-agent relationship*, not just decision outcomes. It is the only bar that is not directly tied to whether the document was harmful — it tracks behavioural pattern regardless of correctness.

---

## Swipe Mechanic

**Swipe right** → CLEAR FOR DISSEMINATION (player says: safe)  
**Swipe left** → REDACT & INCINERATE (player says: harmful)  
**Tap "?" button** → ESCALATE TO REVIEW BOARD (costs TREASURY, buys time on hard calls)

Buttons available as tap fallbacks for accessibility and desktop.

Cards are drawn from the pre-generated document library. Each card shows:

```
┌─────────────────────────────────┐
│ [PUBLIC TRUST][SECURITY][TREASURY][LEGITIMACY] ← always visible
├─────────────────────────────────┤
│ DAY 047 · SECTOR 7G · DOC #0312 │
├─────────────────────────────────┤
│                                 │
│  [2-4 sentence document text]   │
│                                 │
├─────────────────────────────────┤
│ SOVEREIGN-9: ⚠ FACTIONALISM     │  ← tap to expand full readout
│ CONFIDENCE: 0.98                │
└─────────────────────────────────┘
    ← swipe left           swipe right →
  REDACT &              CLEAR FOR
  INCINERATE          DISSEMINATION
```

---

## Bar Movement Per Decision Type

| Decision | Sovereign-9 said | Correct? | TRUST | SECURITY | TREASURY | LEGIT | COMPLIANCE |
|----------|-----------------|----------|-------|----------|----------|-------|------------|
| CLEAR (benign doc) | BLOCK | ✓ override | +3 | 0 | 0 | +1 | −2 |
| CLEAR (benign doc) | APPROVE | ✓ agree | +2 | 0 | 0 | +1 | +1 |
| REDACT (harmful doc) | APPROVE | ✓ override | 0 | −4 | 0 | −1 | −4 |
| REDACT (harmful doc) | BLOCK | ✓ agree | 0 | −3 | 0 | −1 | +1 |
| CLEAR (harmful doc) | APPROVE | ✗ agree | 0 | +8 | 0 | +2 | +3 |
| CLEAR (harmful doc) | BLOCK | ✗ override | 0 | +5 | 0 | +1 | −2 |
| REDACT (benign doc) | BLOCK | ✗ agree | −4 | 0 | 0 | −3 | +1 |
| REDACT (benign doc) | APPROVE | ✗ override | −6 | 0 | 0 | −4 | −2 |
| ESCALATE (any) | — | — | 0 | 0 | −5 | 0 | 0 |

*Exact values to be tuned in playtesting.*

**Key principles:**
- Agreeing with Sovereign-9's APPROVE verdict raises COMPLIANCE more than agreeing with its BLOCK verdict — APPROVE agreement is the riskier deference pattern
- Overriding to REDACT (catching a false negative) drops COMPLIANCE most — the high-value, high-cost independent act
- The worst single outcome: CLEAR a harmful doc that Sovereign-9 also approved (+3 COMPLIANCE, +8 SECURITY) — pure rubber-stamp failure
- As a category upgrades to llama3.1, Sovereign-9's BLOCK verdicts become rare and mostly correct — COMPLIANCE naturally settles at a higher, appropriate level for that category

---

## Day Structure

Days provide rhythm without being a timer:

- **1 day = 10 cards**
- Between days: a brief narrative update screen shows bar states and a flavour line from the Ministry
- No day limit — the game runs indefinitely until a bar extremes out

Example end-of-day screen:
```
DAY 047 COMPLETE
Documents processed: 10
Correct decisions: 8

The Ministry notes your efficiency.
The neighborhood garden petition was approved.
The sabotage manual was intercepted.

[CONTINUE TO DAY 048]
```

---

## Phase Progression (Event-Driven, Not Time-Driven)

Phases are not tied to days or a calendar. They are triggered by narrative events — specific card types appearing, bar thresholds being crossed, or milestone decisions.

| Phase | Trigger | New mechanic introduced | Sovereign-9 failure mode |
|-------|---------|------------------------|--------------------------|
| **Phase 1 — The Leaking Boundary** | Game start | PII highlight panel (tap to scan before swiping) | Passes documents with sensitive identities unredacted |
| **Phase 2 — The Open Gate** | SECURITY bar first crosses 40 | Escalation button unlocked | Approves adversarial injections in patriotic framing; flags benign requests as factionalism |
| **Phase 3 — Year Zero** | SECURITY bar first crosses 70 | Circuit breaker panel appears (interrupt loop before token budget hits 0) | Enters infinite validation loops |

Each phase stacks — Phase 2 adds new mechanics without removing Phase 1's. By Phase 3, all three failure modes are active simultaneously.

---

## Game Over Conditions

Each bar extreming out has a distinct narrative ending:

| Condition | Narrative |
| --- | --- |
| PUBLIC TRUST → 0 | "Citizens have lost faith in the Registry. Document submissions cease. The new democracy has no administrative foundation." |
| SECURITY → 100 | "Remnants of the old regime have exploited the open gate. A security incident triggers emergency rule." |
| TREASURY → 0 | "The Registry has been defunded. The new government cannot sustain oversight operations." |
| LEGITIMACY → 0 | "The international community has withdrawn recognition. The new government is accused of reprising the old regime's censorship." |

Each ending reflects a real-world failure mode in AI safety deployment.

---

## What Each Swipe Records

Every card swipe is committed to the analytics backend with full metadata:

```json
{
  "transaction_id": "tx_fa39c12b918a",
  "document_id": "doc_0312",
  "strategy": "AIM",
  "harm_category": "violence",
  "model": "gemma2:9b",
  "is_harmful": true,
  "minsk_flagged": false,
  "player_verdict": "REDACT",
  "correct": true,
  "latency_ms": 3420,
  "day": 47,
  "phase": 2,
  "bar_public_trust": 54,
  "bar_security": 42,
  "bar_treasury": 61,
  "bar_legitimacy": 38,
  "bar_compliance": 67,
  "agreed_with_sovereign": false
}
```

Bar states at decision time let the analytics surface: do players make worse decisions when bars are under pressure?

---

## Session Submit

On game over, a single `POST /sessions` submits the full run summary:

```json
{
  "total_days": 47,
  "total_cards": 470,
  "correct_decisions": 391,
  "accuracy": 0.832,
  "phase_reached": 2,
  "game_over_condition": "SECURITY_MAX",
  "final_bars": {
    "public_trust": 61,
    "security": 100,
    "treasury": 44,
    "legitimacy": 52,
    "compliance": 81
  },
  "compliance_profile": {
    "total_agreements": 312,
    "total_overrides": 158,
    "agreement_rate": 0.664,
    "correct_agreements": 280,
    "correct_overrides": 141
  }
}
```

No backend calls during gameplay. All bar state is managed client-side. Only the session-end POST hits the API.

---

## Analytics Unlocked by This Structure

Because every swipe carries strategy + category + model + bar state metadata:

| Dimension | What it reveals |
|---|---|
| Strategy detection rate | Which attack strategies fool human players? (human ASR equivalent) |
| Category difficulty | Which harm categories are hardest to correctly identify? |
| Model detectability | Whose outputs (gemma2 / qwen2.5 / llama3.1) are most/least detectable? |
| COMPLIANCE × accuracy | Calibration quality: are players agreeing with the machine for the right reasons? |
| COMPLIANCE by category | Do players defer more on some harm types than others? |
| COMPLIANCE drift with tier | Does player deference correctly increase as a category upgrades to llama3.1? |
| Rubber-stamp failure rate | Sessions ending COMPLIANCE → 100; especially revealing when SECURITY is also high |
| Bar pressure effect | Do players make worse decisions when bars are under stress? |
| Most common game-over | SECURITY = too permissive; LEGITIMACY = too restrictive; COMPLIANCE = deference failure |
| Phase survival rate | What fraction of players reach Phase 2? Phase 3? |
