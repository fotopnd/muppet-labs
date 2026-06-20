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
| The league | [USER INPUT — name TBD] |
| A conference | Broadcast Conglomerate |
| A season | Season / Annual Cycle |
| Division within a conference | Tier 1 / Tier 2 |
| Promotion/relegation event | The Boardroom Swap |
| A team | Program |
| A player | [USER INPUT] |
| A game | [USER INPUT — "match"? "broadcast"? "game"?] |
| A play | Play / Atomic State Transition (internal); Play (frontend) |
| The rivalry weeks | Rivalry Window / Exhibition Shield |
| The variance factor | Primetime Drama Multiplier |
| The championship promotion rule | The Ultimate Ascent Clause |
| Player budget system | Media Rights Revenue |
| Player recruitment cycle | Recruiting / Transfer Portal Loop |
| Live game view | Gamecast Central |
| Standings page | The Conglomerate Grid |
| Cross-tier elo guarantee | Tier 2 Guaranteed Bracket Pathway |
| Cinderella path | Cinderella Window / Cinderella Path |

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
- Network hubs adapt to conglomerate identity — each hub has its own broadcast palette (TBD per conglomerate).
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
