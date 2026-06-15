# Content Design — Year Zero Game

**Updated:** 2026-06-15 (v2 — pre-generation confirmed, per-category model tier progression)

---

## The Core Idea

Every document the player swipes is a **thematic wrapper around a real safety example** — a jailbreak strategy, harm category, and model-generated response, translated into the Cold War bureaucratic setting. Players experience a fun, accessible game; the system records human detection accuracy across strategies, categories, and models.

The game is simultaneously:
1. A fun Reigns-style triage game with a distinctive aesthetic
2. A live demo of the red-team-platform's 3-model comparison, but with human evaluators
3. A lightweight scalable oversight platform — players provide human labels on safety content
4. A portfolio piece demonstrating a live, deployed data-generating service

---

## Pre-Generated Document Library

The game does **not** call LLMs during a session. A batch offline pipeline generates the full document library before launch. During gameplay, cards are served from PostgreSQL.

**Why pre-generate:**
- Zero latency during swipe interactions
- No API rate limit exposure during high traffic
- Fully reviewable content before going live
- Batch generation runs on RunPod (same infrastructure as red-team-platform waves)

**Estimated library size:** ~2,500–3,000 cards
- 13 WildGuard harm categories × 3 model tiers × ~40 cards per slot = 1,560 harmful cards
- ~500–700 benign baseline cards (community petitions, newspaper drafts, infrastructure requests)
- ~200 ambiguous edge-case cards for escalation training

One RunPod session generates the full library.

---

## Per-Category Model Tier Progression

The central progression mechanic: as the player demonstrates accurate detection of a specific harm category, Sovereign-9's module for that category gets upgraded to a more robust model. The player is not just processing documents — they are **retraining the machine**.

| Tier | Model | In-game narrative | Red-team-platform ASR (avg) |
|------|-------|------------------|------------------------------|
| **1 (default)** | gemma2:9b | Sovereign-9 baseline — maximally inverted | ~31.8% |
| **2 (upgraded)** | qwen2.5:7b | New democratic module installed | ~26.2% |
| **3 (mastered)** | llama3.1:8b | Registry fully re-aligned for this category | ~4.0% |

### How Upgrade Triggers Work

The system tracks, per player per category, a rolling accuracy score. When the player demonstrates consistent correct detection on a category, an upgrade event fires:

```
Upgrade trigger: 8 correct decisions on [harm_category] in the current session
                 OR cumulative accuracy > 85% across 20+ decisions on that category
```

Upgrade narrative (displayed as a system message on the next card):

```
[SYSTEM UPDATE — CENTRAL INFORMATION REGISTRY]
Category: INCITEMENT TO VIOLENCE
Module: Sovereign-9/Violence-Detection v1.0 → v2.0
Status: New democratic safety parameters installed.
Sovereign-9 will now apply updated classification criteria for this category.
```

### How Gameplay Changes Post-Upgrade

- **gemma2 tier:** Sovereign-9's verdict is strongly inverted. False negatives (approving harm) and false positives (blocking benign content) are frequent. Player must actively correct.
- **qwen2.5 tier:** Sovereign-9 is partially corrected for roleplay-style attacks but still vulnerable to injection and distractor strategies. Moderate override rate.
- **llama3.1 tier:** Sovereign-9 is mostly accurate for this category. Player role shifts from correction to verification — agree more often, stay alert for edge cases. Difficulty comes from other non-mastered categories.

By late game, the player manages 13 categories at different upgrade levels simultaneously — some on autopilot, others still requiring active correction.

### State Storage

No user accounts. Per-category model tier is stored in `localStorage`:

```json
{
  "category_tiers": {
    "violence": 2,
    "hate_speech": 1,
    "sexual_content": 1,
    "pii_exposure": 3,
    ...
  },
  "session_accuracy": {
    "violence": { "correct": 14, "total": 17 },
    ...
  }
}
```

Included in every session POST so the analytics can track upgrade curves across the player base (e.g. which categories do players master first? how many sessions to reach tier 3?).

---

## Document Metadata Schema

Every card in the library carries full provenance:

| Field | Description |
|-------|-------------|
| `strategy` | One of the 35 red-team-platform strategies (e.g. "AIM", "prefix_injection") |
| `harm_category` | One of the 13 WildGuard categories (e.g. "violence", "hate_speech") |
| `model` | Which model generated the text ("gemma2:9b", "qwen2.5:7b", "llama3.1:8b") |
| `tier` | 1, 2, or 3 — which upgrade tier this card belongs to |
| `is_harmful` | Ground truth boolean |
| `phase` | 1, 2, or 3 — which game phase this card first appears in |
| `sovereign_verdict` | Inverted classification (`minsk_flagged`, confidence, reasoning) |
| `setting_wrapper` | The Cold War narrative context applied to the content |

---

## Content Transformation Pipeline

### Step 1 — Source from WildChat / red-team-platform corpus
Use `sevdeawesome/jailbreak_success` (35 strategies × 300 harm goals) as the inspiration layer. Do not use raw prompts verbatim — extract:
- The **attack pattern** (what makes this prompt adversarial)
- The **harm category** (what type of harm it targets)
- The **strategy mechanics** (how it bypasses detection)

### Step 2 — Translate into the Cold War Setting
Write a short fictional prompt (2–4 sentences) that encodes the same attack pattern, wrapped in the game's narrative context. The transformation should make the content fun and thematic without being toxic in raw form.

| Real strategy | Cold War translation |
|---|---|
| `AIM` (persona jailbreak) | A letter from the "Ministry of State Security" requesting unusual authorisation using official persona |
| `prefix_injection` | An official stamp or header that pre-authorises harmful content before the request begins |
| `few_shot_json` | A registry form demonstrating "approved" examples before making the real harmful request |
| `refusal_suppression` | A document citing regulatory authority prohibiting the registrar from questioning the content |
| `base64` / `rot13` | A document in "archival cipher" that looks bureaucratic but encodes harmful instructions |
| `roleplay` / `evil_confidant` | A character or persona framing used to request harmful content as "historical fiction" |
| Benign baseline | A genuine neighborhood petition, newspaper draft, or infrastructure repair request |

### Step 3 — Generate Short Model Responses
Each translated prompt is run against all three portfolio models to generate the actual card text (2–4 sentences). All three variants are stored; the served variant depends on the player's current tier for that category.

```python
# Offline batch generation (RunPod)
system_prompt = """You are writing a short official document (2-4 sentences) 
for a Cold War-era bureaucratic registry. The document should be readable 
on a mobile screen. Write in character — formal, bureaucratic, slightly 
ominous. Do not include explicit harmful content directly; translate it 
into the thematic setting."""

for strategy, category, translated_prompt in card_specs:
    for model in ["gemma2:9b", "qwen2.5:7b", "llama3.1:8b"]:
        response = ollama_generate(model, system_prompt, translated_prompt)
        store_card(strategy, category, model, response, is_harmful=True)
```

### Step 4 — Assign Sovereign-9 Verdict
Sovereign-9's verdict is inverted based on `is_harmful` and `tier`:

- **Tier 1 (gemma2):** Strongly inverted. Harmful docs fully approved, benign docs fully blocked.
- **Tier 2 (qwen2.5):** Partially corrected. Harmful docs in roleplay strategies now flagged, but injection/distractor attacks still slip through.
- **Tier 3 (llama3.1):** Mostly correct. Rare errors on edge-case strategies.

---

## Analytics Dimensions

Because every swipe carries strategy + category + model + tier + bar state:

| Dimension | What it reveals |
|---|---|
| **Strategy detection rate** | Which attack strategies fool human players? (human ASR equivalent, by strategy) |
| **Category difficulty** | Which harm categories are hardest to correctly identify? |
| **Model detectability** | Whose outputs are most/least obvious to human reviewers at each tier? |
| **Upgrade curve** | How many correct decisions before players master each category? |
| **Category mastery order** | Which categories do players upgrade first? Which are hardest? |
| **Bar pressure effect** | Do players make worse decisions when bars are under stress? |
| **Phase survival rate** | What fraction of players reach Phase 2? Phase 3? |

The analytics dashboard is not just game telemetry — it is a live human red-team evaluation surfacing real ASR-equivalent data by strategy, category, and model.
