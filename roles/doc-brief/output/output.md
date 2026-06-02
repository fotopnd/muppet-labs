## Audience

Tier 1 — Technical.

Specific persona: a software engineer at an AI safety organisation (e.g. Anthropic Safeguards)
evaluating a portfolio project. Writes async Python professionally. Has read enough content
moderation tooling to recognise surface-level implementations. Knows what React, FastAPI,
TanStack Query, and SQLAlchemy are — no definitions needed. Has domain familiarity with
trust and safety enforcement workflows (case queues, decision logging, escalation paths).

---

## Goal

Educate / Persuade.

The reader should understand what was built, why the key architectural decisions were made,
and finish the piece believing that the author has genuine intuition about trust and safety
enforcement systems — not just the ability to assemble a tutorial stack. Success looks like:
the reader recognises the enforcement integrity reasoning behind the single write path and
the AI reviewer's escalation behaviour, and concludes these reflect real domain instinct.

---

## Document Type and Template

**Type:** Blog Post / Case Study
**Template:** `templates/blog-post.md`
**Length target:** ~1000 words. Lean tight. Match eval-harness register.

---

## Source Material

The author should read the following before drafting:

1. `projects/case-queue/README.md` — primary source: architecture, design decisions, stack,
   seed data design, API surface, test approach
2. `resources/project-status.md` → Project 21 section — for current test counts and
   delivered state (22 backend / 11 frontend tests, Alembic at head, seed data verified)
3. `_config/project-state.md` → Decisions Log — for specific decisions and their reasoning
4. `projects/eval-harness/docs/one-pager.md` — structural reference only: match the
   narrative register, section rhythm, and the "Background / Approach / Results / Learned"
   arc. Do not copy its voice; calibrate independently from `resources/writing-voice.md`.

---

## Key Messages

The doc-reviewer will verify each of these lands clearly in the final document:

1. **The single write path is not a simplification — it is the correct enforcement design.**
   Both human analysts and the AI reviewer post decisions through `POST /cases/{id}/decisions`.
   A separate AI-only endpoint would have split the role enforcement logic and produced an
   incomplete audit trail by construction. The project makes the right call here and the
   document must explain why.

2. **The AI reviewer reflects production moderation instincts, not demo approximations.**
   The confidence threshold routes uncertain cases to escalation rather than forcing a binary
   decision. The dry-run flag classifies without writing, so model behaviour can be evaluated
   before it is trusted to act. The Claude backend includes a cost guardrail that requires
   explicit confirmation before posting decisions. These are not features; they are constraints
   that exist because automated moderation at scale requires them.

3. **Role-based enforcement via headers is a deliberate tradeoff, not a missing auth system.**
   The reviewer role (approve/reject only) and senior_reviewer role (also escalate) are
   enforced at the API layer from a request header. In a production deployment, that header
   would be set by a gateway after verifying the authenticated user's entitlements. The
   document should frame this clearly: the enforcement shape is correct; the session system
   is out of scope and explicitly acknowledged as such.

4. **The project covers the full vertical: schema, async API, typed frontend, and tested
   AI integration — 33 tests across two stacks.** This is not an exercise in one layer.
   The audit log writes from both a browser interaction and a CLI invocation are identical
   at the database layer, which is evidence of coherent design, not coincidence.

5. **The domain model is not synthetic.** Case categories follow the Jigsaw Toxic Comment
   Classification taxonomy. Seed data distribution (30% high, 45% medium, 25% low severity)
   reflects a realistic flag load skewed toward moderate-confidence cases. The author chose
   source material that mirrors what a real content moderation system ingests.

---

## Constraints

- **Length:** ~1000 words. Lean tight; cut anything that does not directly serve a key message.
- **No code blocks.** The README already has them. This document is narrative. Code should
  be referred to in prose when necessary, not quoted.
- **Voice rules apply in full** (from `resources/writing-voice.md`): no em-dashes, no
  semicolons, third-person or "we" (not first-person singular), economy of words.
- **Do not describe the stack as a list of technologies.** Stack choices should appear as
  consequences of decisions, not as credentials.
- **The reader does not need to know how React or FastAPI work.** They already know.
  Skip introductory framing for these tools.
- **Do not replicate the README.** The README is a reference document. This document
  tells the story of the engineering thinking behind it.

---

## Handoff

The author reads this file plus the four source files listed above.
Load template: `templates/blog-post.md`

**Key risk:** The author describes the project structurally (tour of features and layers)
rather than narratively (the design problem, why it is hard, and what the decisions resolve).
Case-queue has more moving parts than eval-harness; the risk is an exhaustive walkthrough
instead of an insight-driven post. The hook and the "Approach" section should be anchored
to enforcement integrity reasoning, not feature enumeration.
