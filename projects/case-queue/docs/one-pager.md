# What Keeps a Moderation Queue Honest

Content moderation queues have a recognizable shape. Cases arrive from an ingestion source, analysts review them in priority order, each case receives a decision (remove, clear, or escalate), and every action is logged with who acted and when. That shape appears in every major platform's enforcement infrastructure. It is not hard to describe. It is not even hard to sketch in code.

What is hard is getting the enforcement properties right: that the audit trail is complete regardless of who acted, that role-based controls are enforced at the API layer rather than relied on in the client, and that an AI reviewer integrates into the same workflow a human analyst uses rather than running in a separate lane that quietly bypasses the enforcement logic. Those properties are invisible when they are correct and costly when they are not.

Case Queue was built to demonstrate those properties end-to-end: a React and TypeScript frontend, a Python FastAPI backend, PostgreSQL with Alembic-managed migrations, and an AI reviewer command-line interface (CLI) that classifies cases via a local Ollama model or the Claude API.

## Background

The domain model follows the Jigsaw Toxic Comment Classification taxonomy: toxic, severe toxic, obscene, threat, insult, and identity hate. Five hundred and forty synthetic cases are seeded across six categories and three severity levels, at a distribution weighted toward moderate-confidence flags (30% high severity, 45% medium, 25% low). A uniform spread would not reflect the real shape of a content moderation workload, where the genuinely ambiguous cases are the majority. The distribution is intentional.

The system has two types of actors: human analysts using the browser and the AI reviewer running as a CLI process. Both reach the same backend.

## The Approach

**One write path.** Both the browser and the AI reviewer post decisions through a single endpoint. This is the most consequential design decision in the project. A design that routes human and automated decisions through separate endpoints requires duplicating the role enforcement logic at two points in the codebase and produces an incomplete audit trail by construction, because any decision posted through an AI-specific path that bypasses enforcement is invisible to the same log a human reviewer's decision lands in.

The single endpoint means the audit log is complete regardless of actor. It also means the role enforcement logic lives in exactly one place. The `reviewer` role can approve or reject cases. The `senior_reviewer` role can also escalate. Both are enforced at the API layer from request headers. In a production deployment, those headers would be set by an authenticated gateway that maps a verified user identity to a role. The shape of the access control policy is correct here. The session system is deliberately out of scope.

**AI reviewer constraints.** The AI reviewer polls the queue, fetches pending cases, and posts decisions through the same endpoint a human analyst uses. Three constraints govern its behaviour.

First, a confidence threshold. The classifier requests a structured JSON response from the model that includes the action, reasoning, and a confidence score. Cases below 0.7 confidence are escalated rather than actioned. Uncertain automated decisions route to a human reviewer rather than being forced to a binary outcome.

Second, a dry-run flag. Running with `--dry-run` classifies each case and logs the proposed decision without posting it. This makes it possible to evaluate model behaviour before enabling live actioning, which mirrors the validation workflow a real ML-assisted moderation system requires before promoting a classifier to production.

Third, a cost guardrail on the Claude backend. Before posting any decisions, the reviewer estimates spend for the current cycle and requires explicit confirmation. This reflects the economics of cloud inference as a real constraint rather than a detail to defer.

**Testing.** The backend test suite covers role enforcement, decision recording, audit log pagination, and the pagination contract across 22 tests. Tests run against a dedicated PostgreSQL test database with NullPool (no connection reuse across async contexts) and patch the lifespan initialization so the test runner does not attempt to connect to the production database. The frontend suite (11 tests via vitest and Testing Library) covers case queue rendering, filtering, pagination, and the decision form submission flow.

## The Results

Both test suites pass cleanly. The AI reviewer correctly classifies synthetic cases via both backends, with borderline cases escalating as intended. The audit log is complete regardless of whether a decision was posted by a browser session or a CLI invocation. There is no code path that produces a decision without an audit record.

## What We Learned

The single write path constraint was the most structurally useful decision in the project, and the reason is not elegance. Committing to it early closed off a class of design questions that would otherwise have accumulated: should the AI reviewer have elevated permissions, should it bypass role enforcement for throughput, should human and automated decisions appear on separate audit views. Those questions become incoherent once the write path is shared. A system where all decisions enter through the same gate is simpler to reason about, easier to audit, and harder to misconfigure than one with separate lanes for different actor types. That holds at any scale.

## Where to Go Next

The repository is at `projects/case-queue/`. The README covers local setup, the full API surface, and the deployment configuration for Hostinger VPS. The AI reviewer README covers the classification flow and backend configuration options.
