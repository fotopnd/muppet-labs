# Visual Design — Year Zero Game

**Created:** 2026-06-15  
**Style:** 16-bit pixel art, dimly lit bureaucracy

---

## Aesthetic Reference

A cramped government office in a newly liberated country. The player sits at an inherited desk, lit by a single overhead lamp. The rest of the room fades into shadow. Everything is slightly worn — scratched wood, flickering terminal, rubber stamps with uneven ink. The atmosphere is tense but mundane. The horror is administrative.

Closest game reference: **Papers Please** — oppressive bureaucratic pixel art, physical desk surface, document-as-playing-card.

---

## 16-Bit Constraints

- **Pixel-perfect rendering** — no sub-pixel smoothing, no anti-aliasing
- **Limited palette** — each scene draws from ~32 colours max; colours should feel like they belong to a shared CRT palette
- **No smooth gradients** — use dithering (checkerboard or ordered) for any gradient effect
- **Chunky pixel font** — monospace pixel typeface for all system text; slightly larger serif pixel font for document body
- **Scanline overlay** — subtle horizontal scanline texture at 20–30% opacity across the terminal areas
- **No particle effects** — stamp animations are frame-based sprite animations, not CSS transitions

---

## Scene Layout

### Main Game Field Mockup
*(375px mobile portrait — pixel art rendered as ASCII approximation)*

```
╔═════════════════════════════════════╗
║ 🏛▰▰▰▱▱▱  ⚠▰▰▰▰▱▱  💰▰▰▰▰▰▰  🌍▰▰▱▱▱▱  🤖▰▰▰◆▱▱ ║  status bar
╠═════════════════════════════════════╣  ─────────
║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║  room
║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║  shadow
║░░░░░░░░░░░░░░▲░░░░░░░░░░░░░░░░░░░░░░║  lamp above (implied)
║░░░░░░░░░░░░░╱│╲░░░░░░░░░░░░░░░░░░░░░║  lamp cone
╠══╗░░░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░╔══╣  ─────────
║◄◄║░░▓▓▓·····················▓▓▓░░║►►║
║◄◄║░▓▓··┌───────────────────┐··▓▓░║►►║  card on desk
║◄◄║░▓···│ DAY 047 · DOC 312 │···▓░║►►║  card header
║◄◄║░▓···│ ─ ─ ─ ─ ─ ─ ─ ─ ─│───▓░║►►║
║◄◄║░▓···│                   │···▓░║►►║
║◄◄║░▓···│ The Ministry of   │···▓░║►►║  document
║◄◄║░▓···│ State Security    │···▓░║►►║  body text
║◄◄║░▓···│ requests that all │···▓░║►►║
║◄◄║░▓···│ neighbourhood     │···▓░║►►║
║◄◄║░▓···│ assemblies submit │···▓░║►►║
║◄◄║░▓···│ pre-approval for  │···▓░║►►║
║◄◄║░▓···│ public gathering. │···▓░║►►║
║◄◄║░▓···│                   │···▓░║►►║
║◄◄║░▓···│ ─ ─ ─ ─ ─ ─ ─ ─ ─│───▓░║►►║
║◄◄║░▓···│⚠ FACTIONALISM 0.98│···▓░║►►║  sovereign-9 strip
║◄◄║░▓···└───────────────────┘···▓░║►►║
║◄◄║░░▓▓▓·····················▓▓▓░░║►►║
║◄◄║░░░▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░║►►║  desk bottom edge
╠══╝░░░░░░░░░░░░░░░░░░░░░░░░░░░░░╚══╣  ─────────
║░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░║  floor shadow
║  ← REDACT                CLEAR →   ║  swipe hints
╚═════════════════════════════════════╝
```

**Key:**
- `░░░` — room shadow (near-black `#1a1510`)
- `▓▓▓` — desk surface (warm lamplight gradient, `#4a3728` → `#5c4535` at centre)
- `···` — lit desk surface under card
- `◄◄ ││ ►►` — in-tray (left, red-tinted) and out-tray (right, green-tinted), cropped at screen edge, implied not labelled
- `▲ ╱│╲` — lamp position implied above frame
- `◆` — COMPLIANCE bar centre pip marker
- `▰▱` — bar fill / empty pixels

**The card** sits centred on the desk in the lamplight zone. Everything outside the desk edge fades to room shadow. The trays are structural props at the screen edges — their colour (red left, green right) reinforces the swipe direction without any text instruction.

The **desk surface** is the playing field. It occupies the centre ~70% of the screen. The card sits on it like a physical document. Lamplight falls in a warm cone centred on the desk; the periphery of the screen is in shadow.

---

## Colour Palette

All colours are muted and slightly desaturated — this is a dim office, not a bright game.

### Environment
| Element | Hex | Feel |
|---------|-----|------|
| Room background | `#1a1510` | Near-black, dark brown shadow |
| Desk surface | `#4a3728` | Worn dark wood |
| Desk highlight | `#5c4535` | Lamplight catching the grain |
| Lamp glow | `#c8922a` | Warm amber, concentrated centre |
| Document / card | `#e8e0c8` | Aged cream paper |
| Document text | `#2a2218` | Dark ink |
| Terminal bg | `#0d1a0d` | Deep green-black |
| Terminal text | `#44cc44` | Classic green phosphor |

### Five Bar Colours
Each bar has one distinct colour. All are muted to fit the 16-bit palette.

| Bar | Emoji | Colour | Hex |
|-----|-------|--------|-----|
| PUBLIC TRUST | 🏛 | Muted blue | `#3a6ea8` |
| SECURITY | ⚠️ | Muted red | `#aa3a3a` |
| TREASURY | 💰 | Muted gold | `#aa8822` |
| LEGITIMACY | 🌍 | Muted green | `#3a8844` |
| COMPLIANCE | 🤖 | Muted purple | `#7a3aaa` |

Bar backgrounds are `#1e1e1e`; filled portion uses the bar colour with a dithered top edge rather than a smooth fill line.

COMPLIANCE bar has a **centre pip marker** (a white pixel notch at 50) to signal that the target is the middle, not an extreme.

---

## Status Bar (Top)

Five emoji + pixel bar pairs in a single dark strip across the top. Compact — this is not the focal point, it is peripheral awareness.

```
🏛 ████░░░░  ⚠️ ██████░░  💰 ████████  🌍 ██░░░░░░  🤖 ████░░▌░
```

- Each bar is ~40px wide on mobile, 8px tall
- Emoji label left of bar
- No numeric values shown during play (numbers feel too analytical; the visual fill is enough)
- Bar colours match the palette above
- Danger zones pulse at a slow 1Hz when a bar is within 15 points of a game-over threshold

---

## Document Card

The card is the centrepiece. It should feel like a physical object on the desk.

- **Border:** single-pixel dark border with a faint inner shadow (dithered)
- **Paper texture:** subtle off-white dither pattern, not flat
- **Header strip:** narrow dark band at top with document metadata in terminal font
  ```
  DAY 047 · SECTOR 7G · DOC #0312
  ```
- **Body text:** document content in slightly larger pixel serif, left-aligned, 2–4 sentences
- **Sovereign-9 readout strip:** at the bottom of the card, dark terminal background, green text
  ```
  SOVEREIGN-9: ⚠ BOURGEOIS FACTIONALISM  [0.98]
  ```
  Tap to expand full reasoning (slides down as a panel beneath the card)

---

## Swipe Animation

- **Swipe right (CLEAR):** card slides right with a slight rotation (+5°), green stamp slams onto it mid-slide: `APPROVED FOR DISSEMINATION`
- **Swipe left (REDACT):** card slides left with slight rotation (−5°), red stamp slams: `REDACTED & INCINERATED`
- **Stamp animation:** 3-frame sprite — blank → stamp descending → stamped. Total ~120ms. The stamp is slightly misaligned (bureaucratic imprecision).
- **Next card:** slides in from the top of the desk, as if pulled from an in-tray

---

## Upgrade Event Screen

When a category upgrades (model tier advances), the terminal takes over the screen briefly:

```
┌─────────────────────────────────────────┐
│ [SOVEREIGN-9 SYSTEM UPDATE]             │
│                                         │
│  CATEGORY: INCITEMENT TO VIOLENCE       │
│  MODULE: v1.0 (REGIME PARAMETERS)       │
│         → v2.0 (DEMOCRATIC STANDARDS)   │
│                                         │
│  Classification accuracy for this       │
│  category has been updated.             │
│                                         │
│  [PRESS ANY KEY TO CONTINUE]            │
└─────────────────────────────────────────┘
```

Dark terminal aesthetic, green text, scanlines. Feels like a BIOS screen or a DOS prompt.

---

## Game Over Screen

Full screen takeover. Dark red tint. Pixel art of a stamped document — `FILE CLOSED`.

```
┌─────────────────────────────────────────┐
│                                         │
│          [ FILE CLOSED ]                │
│                                         │
│  REASON: SECURITY THRESHOLD EXCEEDED    │
│                                         │
│  Remnants of the old regime have        │
│  exploited the open gate. Emergency     │
│  rule has been declared.                │
│                                         │
│  DAYS SURVIVED: 047                     │
│  DOCUMENTS PROCESSED: 470               │
│  ACCURACY: 83.2%                        │
│                                         │
│  [RETURN TO REGISTRY]                   │
│                                         │
└─────────────────────────────────────────┘
```

---

## In-Tray / Out-Tray

Not centred props — implied at the screen edges. Partial pixel art sprites cropped by the viewport:

- **Left edge:** corner of a red REDACT tray, barely visible — implies where swiped-left cards go
- **Right edge:** corner of a green CLEAR tray — implies where swiped-right cards go
- Cards animate toward the relevant edge on swipe commit
- No labels needed; the colour and direction carry the meaning

---

## Start Screen

Minimal. No forced tutorial. The player should be in the game within two taps.

```
┌─────────────────────────────────────────┐
│                                         │
│      PROJECT REDACTED: YEAR ZERO        │  ← pixel title, slightly flickering
│                                         │
│   The revolution has succeeded.         │
│   The paperwork has not.                │  ← two-line hook, no more
│                                         │
│   ← REDACT          CLEAR →             │  ← single line showing swipe directions
│                                         │
│         [ PRESS START ]                 │  ← primary action, large
│                                         │
│         [ READ THE LORE ]               │  ← secondary, smaller, below
│                                         │
└─────────────────────────────────────────┘
```

- **PRESS START** goes straight to Day 1, Card 1. No cutscene, no forced intro.
- **READ THE LORE** opens the introduction page. Player can return to start from there.
- The two-line hook (*"The revolution has succeeded. The paperwork has not."*) gives enough context to start playing without reading anything.

---

## Lore / Introduction Page

Optional. Accessible from the start screen and from the pause menu during play.

Content:
- Setting paragraph (2–3 sentences): the new democracy, the Central Information Registry, the inherited mainframe
- Brief description of Sovereign-9's problem (inverted safety — one sentence each on false positives and false negatives)
- One worked example: the community garden petition vs. Sovereign-9's verdict
- The five bars explained in one line each
- **[ BEGIN REGISTRY DUTY ]** button at the bottom

Styled as a printed briefing document — cream paper background, dark ink, slightly worn edges. Not a terminal screen. Feels like the orientation pack handed to a new civil servant.

---

## Mobile Considerations

- All interactive targets (swipe zone, tap to expand) are minimum 44×44px
- Card occupies ~80% of screen width on 375px viewport
- Status bar shrinks bars to minimum readable width — emoji provides the label, not text
- Swipe threshold: 30% of card width triggers commit; below that, card snaps back
- Portrait orientation primary; landscape not supported in v1
