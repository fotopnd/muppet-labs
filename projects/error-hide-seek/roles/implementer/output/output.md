# Implementer 6b Output — error-hide-seek Frontend

**Role:** implementer (frontend phase)
**Sequence:** `new-project-full` (step 6b)
**Date:** 2026-06-07

---

## Status: Complete

Frontend implementation is complete. `pnpm build` exits 0. 15 tests pass. 0 TypeScript errors.

---

## Files Written

### Config
- `web/vite.config.ts` — `@tailwindcss/vite` plugin, port 5174, vitest config with jsdom, `@/` path alias
- `web/tsconfig.app.json` — strict TS 6 config, `allowImportingTsExtensions`, `vite/client` types, path alias
- `web/pnpm-workspace.yaml` — `allowBuilds: msw: true`

### Source
- `web/src/index.css` — Tailwind v4 `@import` + `@theme` token layer (all 11 color vars, 2 font vars)
- `web/src/App.tsx` — `QueryClientProvider`, `BrowserRouter`, two routes + `*` redirect, header shell with breadcrumb
- `web/src/main.tsx` — unchanged from scaffold
- `web/src/types/index.ts` — all TypeScript types matching API schemas exactly (incl. `paper_title` in `Session`)
- `web/src/api/client.ts` — `apiFetch<T>()` wrapper around `fetch`, JSON content-type default
- `web/src/hooks/useSession.ts` — `GET /sessions/{id}`, enabled guard, no refetch
- `web/src/hooks/useSubmitReview.ts` — `POST /reviews`, navigates to `/results/{experimentId}` on success
- `web/src/hooks/useResults.ts` — `GET /results/{id}`, conditional poll (`30s` when `uplift === null`, stops on complete)
- `web/src/hooks/useExperiments.ts` — `GET /experiments` (stubbed, not used in v1 UI)
- `web/src/hooks/usePapers.ts` — `GET /papers` (stubbed, not used in v1 UI)
- `web/src/components/AnnotatedAbstract.tsx` — segmentation algorithm, confidence-coloured highlights, tooltip with badge
- `web/src/components/SelectionFloater.tsx` — React portal, `position: fixed`, 15-char guard in parent
- `web/src/components/DetectionList.tsx` — flagged excerpt list, note input, remove ×, submit spinner
- `web/src/components/UpliftHero.tsx` — `+X.X%` format, emerald/red/muted by sign, null → "Results incomplete"
- `web/src/components/ConditionResultsTable.tsx` — 3-condition table + category breakdown, highlighted human+agent TPR cell
- `web/src/components/PaperHeader.tsx` — condition badge, paper title
- `web/src/components/CompletionBanner.tsx` — completed session state

### Pages
- `web/src/pages/ReviewPage.tsx` — useSession, mouseup handler, SelectionFloater state, submit via useSubmitReview, loading/error states
- `web/src/pages/ResultsPage.tsx` — useResults, UpliftHero + ConditionResultsTable, loading/error states

### Tests
- `web/src/test/setup.ts` — `@testing-library/jest-dom`
- `web/src/test/handlers.ts` — MSW v2 handlers for all endpoints (session variants: unaided/human_agent/completed/404; results with uplift + null uplift)
- `web/src/test/ReviewPage.test.tsx` — 8 tests covering paper title render, empty detection list, abstract text, highlights, completion banner, error state, submit button
- `web/src/test/ResultsPage.test.tsx` — 7 tests covering uplift color, incomplete state, condition headers, TPR values, category breakdown, "—" for incomplete

---

## Deviations from Spec

| Spec | Deviation | Reason |
|------|-----------|--------|
| `tailwind.config.js` (Tailwind v3 API) | CSS `@theme` block in `index.css` (Tailwind v4) | `@tailwindcss/vite` 4.x requires v4 config approach; same class names, same token values |
| `data-floater` attribute on floater button | Not in spec | Added to allow `mousedown` outside-click detection |
| `noUncheckedIndexedAccess` strict mode | Added | Workspace convention; no runtime impact, only improves type safety |

---

## Test Results

```
pnpm exec vitest run
Test Files  2 passed (2)
     Tests  15 passed (15)
  Duration  613ms
```

```
pnpm build
✓ built in 90ms
0 TypeScript errors
```

---

## Handoff

**Next role:** reviewer

**Reviewer reads:**
- This file
- `roles/implementer/output/backend-output.md`
- `roles/architect/output/output.md`
- `roles/design-brief/output/output.md`
- `roles/frontend-architect/output/output.md`
- Source files in `error_hide_seek/` and `web/src/`

**To run the full stack:**
```bash
docker compose up -d db
uv run api                    # API on :8004
cd web && pnpm dev            # Frontend on :5174
```
