# doc-types.md — Document Type Catalog

> Loaded by: `doc-brief` (document type selection).
> Lists all available document types, their templates, audience tier, writing goal, and when to choose them.

---

## How to Select a Document Type

The `doc-brief` role uses this file to match the human's intent to the right template. Ask two questions:

1. **Who is the primary reader?** → Audience tier (Technical / Technical Leadership / Executive)
2. **What do you need them to do after reading?** → Writing goal (Inform / Educate / Persuade)

Then find the type below that matches both. If two types fit, prefer the more specific one.

---

## Document Types

### Technical Deep-Dive

| Field | Value |
|-------|-------|
| **Template** | `templates/technical-deep-dive.md` |
| **Primary audience** | Technical |
| **Primary goal** | Inform / Educate |
| **Typical length** | 1000–2500 words |

**Use when:** A technical reader needs to understand how something was built — the design decisions, architecture, non-obvious implementation details, and evidence it works. Good for: portfolio technical writeups, engineering blog posts aimed at practitioners, onboarding documentation for a complex system.

**Not for:** Convincing anyone to do something. Not for executives. If the reader already knows the system well, consider a Technical Summary instead.

---

### Design Proposal (RFC)

| Field | Value |
|-------|-------|
| **Template** | `templates/design-proposal.md` |
| **Primary audience** | Technical |
| **Primary goal** | Persuade |
| **Typical length** | 500–1500 words |

**Use when:** You need a technical audience to adopt a decision or approach. The document must include the proposed decision, the alternatives considered, and the reasoning. Good for: pre-implementation architecture decisions, tooling choices, process changes.

**Not for:** Documenting something already built (use Technical Deep-Dive or Technical Summary). Not for executives.

---

### Technical Summary

| Field | Value |
|-------|-------|
| **Template** | `templates/technical-summary.md` |
| **Primary audience** | Technical Leadership |
| **Primary goal** | Inform |
| **Typical length** | 400–800 words |

**Use when:** A tech lead, EM, or senior IC needs to understand what was built without reading a full deep-dive. Focuses on decisions and outcomes, not implementation. Good for: post-project summaries for managers, cross-team updates, handoff documents.

**Not for:** Convincing anyone (use Design Proposal). Not for non-technical readers.

---

### Executive Summary

| Field | Value |
|-------|-------|
| **Template** | `templates/executive-summary.md` |
| **Primary audience** | Executive / Stakeholder |
| **Primary goal** | Inform / Persuade |
| **Typical length** | 300–600 words |

**Use when:** A non-technical decision-maker or hiring manager needs to quickly understand what was built, why it matters, and what was demonstrated. Leads with the conclusion. Good for: one-pagers for interviews, project briefings for leadership, portfolio summaries.

**Not for:** Audiences who will want technical depth inline (link to a deep-dive instead).

---

### Blog Post / Case Study

| Field | Value |
|-------|-------|
| **Template** | `templates/blog-post.md` |
| **Primary audience** | General / Public |
| **Primary goal** | Educate / Persuade |
| **Typical length** | 800–2000 words |

**Use when:** You want a broader audience — including technical readers who don't know you — to understand and be interested in the work. Narrative-driven. Shows the thinking, not just the result. Good for: public portfolio pieces, LinkedIn articles, personal site posts, conference talk companion posts.

**Note:** The audience is "General / Public" but blog posts frequently skew technical. Use audience-tiers.md to calibrate: a practitioner-focused post reads like Tier 1 with more narrative structure; a general-interest post reads like Tier 3 with storytelling.

---

### Stakeholder Update

| Field | Value |
|-------|-------|
| **Template** | `templates/stakeholder-update.md` |
| **Primary audience** | All tiers |
| **Primary goal** | Inform |
| **Typical length** | 200–400 words |

**Use when:** Communicating progress to anyone who has an interest in the project. Focused, structured, short. Does not explain the project — assumes the reader knows what it is. Good for: weekly updates, milestone check-ins, project status emails.

**Not for:** First introductions to a project. Not for external audiences who don't know the project.

---

## Quick Selection Guide

| If the reader is... | And they need to... | Use |
|--------------------|---------------------|-----|
| An engineer | Understand how it was built | Technical Deep-Dive |
| An engineer | Decide which approach to take | Design Proposal |
| A tech lead or EM | Know what was built and why | Technical Summary |
| An executive or hiring manager | Understand value and outcomes | Executive Summary |
| A broad/public audience | Be interested and learn something | Blog Post |
| Anyone already tracking the project | Know current status | Stakeholder Update |
