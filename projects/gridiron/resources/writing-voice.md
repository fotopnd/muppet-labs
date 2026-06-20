# writing-voice.md — Gridiron Project

> Loaded by any role producing written output for this project.
> Overrides workspace `resources/writing-voice.md` for gridiron-specific work.

---

## Project Register

Capitalist grimdark. The world is a recognisable, slightly dystopian extension of current college sports — not satirical, not comedic. The corporate takeover is treated as fait accompli, presented with the breathless enthusiasm of a broadcast executive memo. The simulation is straight and realistic; the flavour layer is the institutional machinery around it.

Reference: **Rollerball (1975)** — the corporation as protagonist, the sport as product, the athletes as assets.

Tagline: **More Football More Of The Time.**

---

## In-Universe Terminology

| Concept | Term used in this project |
|---------|--------------------------|
| The governing body | **NAFCA** — National American Football Conference Association |
| A conference | Broadcast Conglomerate |
| A season | Season |
| Division within a conference | Tier 1 (Championship Tier) / Tier 2 (Developmental Tier) |
| Promotion/relegation event | The Boardroom Swap |
| A team | Team / Program (both standard college football usage) |
| A player | Player |
| A coach | Coach |
| A game | Game |
| A play | Play |
| A score | Score / Points |
| A roster | Roster |
| A recruit | Recruit |
| Transfer portal | Transfer Portal |
| Positions | Standard football positions (QB, RB, WR, TE, OL, DL, LB, CB, S, K, P) |
| Stats | Standard football stats terminology throughout |
| The rivalry weeks | Rivalry Window / Exhibition Shield |
| The variance factor | Primetime Drama Multiplier |
| The championship promotion rule | The Ultimate Ascent Clause |
| Team budget system | Media Rights Revenue |
| Player recruitment cycle | Recruiting / Transfer Portal |
| Live game view | Gamecast Central |
| Standings page | The Conglomerate Grid |
| Tier 2 at-large guarantee | Tier 2 Guaranteed Bracket Pathway |
| Upset potential framing | Cinderella Path / Cinderella Window |
| Conglomerate 1 | **NCC** — National Collegiate Conference / TCB Sports Network |
| Conglomerate 2 | **SBC** — Southern Broadcast Coalition / ISG Sports Network |
| Conglomerate 3 | **ACA** — American College Alliance / STN Broadcast Group |
| Conglomerate 4 | **MCC** — Midwestern Collegiate Conference / CHBA Sports |
| Conglomerate 5 | **UAC** — United American Conference / FPC Americana Network |

---

## Brand Palettes

### NAFCA (Governing Body)

| Token | Hex | Usage |
|-------|-----|-------|
| Patriot Blue | `#0B3C5D` | Primary NAFCA crest, shield |
| Industrial Silver | `#328CC1` | Secondary NAFCA accent |
| Institutional White | `#D9B310` | NAFCA tertiary / gold seal |

### NCC — TCB Sports Network

| Token | Hex | Usage |
|-------|-----|-------|
| Deep Executive Navy | `#0A192F` | Primary |
| Platinum White | `#F5F7FA` | Secondary |
| High-Contrast Cyan | `#00F0FF` | Accent / data highlights |

**Aesthetic:** Minimalist, flat, mechanical. Heavy stat tickers, rolling win-probability graphs.

### SBC — ISG Sports Network

| Token | Hex | Usage |
|-------|-----|-------|
| Premium Crimson | `#8B0000` | Primary |
| High-Visibility Yellow | `#FFD700` | Secondary |
| Charcoal Grey | `#1C1C1C` | Background |

**Aesthetic:** Bold, gloss-accented, cinematic. Dynamic player metrics, prime-time atmosphere.

### ACA — STN Broadcast Group

| Token | Hex | Usage |
|-------|-----|-------|
| Obsidian Black | `#0B0C10` | Primary |
| Burnished Gold | `#C5A059` | Secondary |
| Silk Cream | `#FFFDD0` | Tertiary / text |

**Aesthetic:** Prestige, streaming-first, thin-line overlays. High-end typography. Slow dissolves.

### MCC — CHBA Sports

| Token | Hex | Usage |
|-------|-----|-------|
| Classic Athletic Gold | `#DAA520` | Primary |
| Dark Slate | `#2F4F4F` | Secondary |
| Pure White | `#FFFFFF` | Tertiary |

**Aesthetic:** Traditionalist, institutional. Monospaced tables, timeless fonts, brass-driven audio.

### UAC — FPC Americana Network

| Token | Hex | Usage |
|-------|-----|-------|
| Patriotic Blue | `#104E8B` | Primary |
| Stadium Red | `#CD2626` | Secondary |
| Off-White | `#F0F0F0` | Tertiary |

**Aesthetic:** Raw, functional, high-visibility. Standard lower-third bugs, no complex telemetry.

---

## Design Document Style

- **Audience:** Technical collaborators and future-self; assumes engineering fluency
- **Formality:** Confident, specific, declarative — reads like a product spec written by someone who also watches football
- **Density:** High. Bullet-heavy, named concepts, explicit numbers. Avoid vague generalities.
- **Diagrams:** Yes — ASCII or structured tables preferred for schema; visual mockups for frontend

---

## Frontend Copy Style

- Corporate broadcast, not game-y. Feels like a financial terminal crossed with a premium sports network overlay.
- Dark mode default. Data density over whitespace.
- Network hubs adapt to conglomerate identity — each hub uses its defined broadcast palette (see Brand Palettes section above).
- Monospaced fonts for all numerical data tables. Columns must align during rapid sorting.
- Play event cards use colour-coded impact indicators: Crimson = Turnover, Gold = Touchdown, Blue = Explosive Play (20+ yards).
- No whimsy. No emoji in data views. Impact language only where it serves broadcast realism.

---

## Things to Avoid

- Whimsical or absurdist tone (this is not Blaseball)
- Fantasy or supernatural mechanics in the simulation layer
- Modern startup / product language ("delightful", "seamless", "intuitive")
- Hedging or softening corporate language — the conglomerates are not apologetic
- Exposing engine internals (scoring constants, probability matrices) in any public-facing copy or design document shared outside the repo
