# typescript-conventions.md — TypeScript Standards for Muppet Labs

> Language-specific conventions for TypeScript projects.
> Load this file in roles that need language guidance: planner (tech stack), implementer (code production), reviewer (style assessment).
> Do not load for roles that only need working-style guidance — use `vibecoding-style.md` for that.

---

## Compiler Config

- TypeScript 5.x. Target `ES2022`. Module `ESNext`. `moduleResolution: bundler`.
- **Strict mode on.** `"strict": true` in `tsconfig.json` — no exceptions.
- Enable `noUncheckedIndexedAccess` and `exactOptionalPropertyTypes` in addition to strict.
- No `ts-ignore` or `@ts-expect-error` except with an explicit comment explaining why.
- `skipLibCheck: true` is acceptable; it only skips `.d.ts` files in node_modules.

---

## Package Management and Tooling

- Use `pnpm` for all package management. No npm, no yarn.
- Format with `prettier`. Lint with `eslint` (flat config, `eslint.config.ts`).
- Follow `skills/setup-ts-pnpm.md` to initialise a new project correctly.
- `pnpm-lock.yaml` is committed. Do not commit `node_modules/`.

---

## Type System

- Prefer explicit types over inference at module boundaries (function return types, exported values).
- Within function bodies, inference is fine — do not annotate every variable.
- Use `type` for shapes and unions. Use `interface` only when declaration merging is intentional.
- No `any`. If external data has an unknown shape, use `unknown` and narrow it explicitly.
- Discriminated unions over optional fields for variant types.
  ```ts
  // prefer this
  type Action = { type: 'approve'; notes: string } | { type: 'escalate'; reason: string }
  // over this
  type Action = { type: string; notes?: string; reason?: string }
  ```
- Avoid non-null assertions (`!`). Narrow the type instead.

---

## Naming Conventions

- **Files:** `kebab-case.ts` for utilities and modules; `PascalCase.tsx` for React components.
- **Types / Interfaces:** `PascalCase`.
- **Variables / functions:** `camelCase`.
- **Constants:** `SCREAMING_SNAKE_CASE` only for true module-level constants (enums, config values). Do not use it for every `const`.
- **React components:** `PascalCase`, one component per file.

---

## Imports

- Absolute imports via path aliases (`@/` mapped to `src/`). No relative `../../` climbing more than one level.
- Group imports: external packages → internal modules → types. Prettier/ESLint enforce order.
- Type-only imports use `import type { Foo }` — keeps the import graph clean and enables `verbatimModuleSyntax`.

---

## React Conventions

- Functional components only. No class components.
- Props type inline as `function Foo({ bar }: { bar: string })` for small components; extract a named `type FooProps` when props grow beyond ~4 fields.
- Hooks follow React rules: no conditional calls, custom hooks named `useX`.
- Server state (API data): TanStack Query. Do not hand-roll fetch + useEffect + useState for data fetching.
- UI state (form inputs, modal open/close): `useState` or `useReducer` in the component.
- No prop drilling beyond two levels — use context or co-locate state.
- Components render one thing. Extract sub-components when a render function exceeds ~60 lines.

---

## Error Handling

- API calls return a typed result; handle both success and error states at the call site.
- Do not throw from React components — use error boundaries for unexpected failures.
- Form validation errors are typed, not string-concatenated from arbitrary places.

---

## Testing

- Use `vitest` for unit and component tests. Test files colocated: `Foo.test.tsx` next to `Foo.tsx`.
- Use `@testing-library/react` for component tests. No snapshot tests.
- Mock only at boundaries: API calls (via `msw`) and browser APIs that don't exist in jsdom.
- Test behaviour, not implementation: assert what the user sees, not which function was called.

---

## General Style

- **Working before clean.** The first pass should run. Refactoring is the reviewer's job.
- **Explicit over clever.** Readable over terse. No one-liner reduce chains that require a comment to parse.
- **No placeholder stubs.** Do not write `// TODO: implement` without noting it explicitly in the role output file.
- **Comments explain why, not what.** TypeScript types explain the what.
