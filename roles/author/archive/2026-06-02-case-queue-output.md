# Author Output — case-queue one-pager

**Date:** 2026-06-02
**Document:** `projects/case-queue/docs/one-pager.md`
**Brief:** `roles/doc-brief/output/output.md`
**Template:** `templates/blog-post.md`

## What was written

Blog Post / Case Study targeting Technical (Tier 1) readers. ~870 words. Follows the same
arc as `projects/eval-harness/docs/one-pager.md`: hook, background, approach, results,
learned, next.

## Decisions made during drafting

- Title: "What Keeps a Moderation Queue Honest" — leads with the enforcement integrity
  question rather than naming the project or describing the stack.
- Hook opens on the recognizable shape of moderation queues, then pivots to what is actually
  hard (enforcement properties). Avoids listing technologies in the opening.
- The Approach section uses three bold anchors (one write path, AI reviewer constraints,
  testing) to give structure without requiring sub-headings that would fragment the narrative.
- Role-based access control framing: explicitly acknowledges headers-as-RBAC is a deliberate
  scope decision, not a gap. The phrase "The shape of the access control policy is correct
  here" is the key signal to a technical reader.
- "What We Learned" focuses on the structural consequence of the single-path decision
  (it closed off a class of questions) rather than restating the feature.

## Notes for doc-reviewer

- Check that key message 1 (single write path) lands clearly in "The Approach" first anchor.
- Check that key message 2 (AI reviewer constraints) reads as production instinct, not demo
  features — the three-point structure (threshold, dry-run, cost guardrail) should feel like
  a considered list, not a feature dump.
- Check that key message 3 (RBAC framing) is honest without being defensive.
- Voice: no em-dashes, no semicolons applied throughout. Verify none slipped through.
- Length target was ~1000 words; draft is approximately 870. Within acceptable range given
  the brief instruction to lean tight.
