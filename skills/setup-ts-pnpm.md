# Skill: Setup a TypeScript / React Project with pnpm + Vite

> Load this file when the planner or implementer role needs to initialise a new TypeScript project.
> These steps assume a React + Vite project. Adapt step 2 for non-React TypeScript.

---

## Prerequisites

Ensure `pnpm` is installed:

```bash
which pnpm || npm install -g pnpm
```

Ensure `node` is 18+:

```bash
node --version
```

---

## Procedure

### Step 1 — Scaffold with Vite

```bash
cd /path/to/parent/
pnpm create vite <project-name> --template react-ts
cd <project-name>
pnpm install
```

This creates: `package.json`, `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`, `vite.config.ts`, `src/`, `index.html`.

---

### Step 2 — Harden `tsconfig.app.json`

Replace the generated `tsconfig.app.json` with a strict config:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noEmit": true,
    "skipLibCheck": true,
    "verbatimModuleSyntax": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"]
}
```

Add the path alias to `vite.config.ts`:

```ts
import path from 'path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

Install the node types for path resolution:

```bash
pnpm add -D @types/node
```

---

### Step 3 — Add ESLint and Prettier

```bash
pnpm add -D eslint @eslint/js typescript-eslint eslint-plugin-react-hooks prettier
```

Create `eslint.config.ts`:

```ts
import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    plugins: { 'react-hooks': reactHooks },
    rules: { ...reactHooks.configs.recommended.rules },
  },
)
```

Create `.prettierrc`:

```json
{
  "semi": false,
  "singleQuote": true,
  "trailingComma": "all",
  "printWidth": 100
}
```

---

### Step 4 — Add Vitest and Testing Library

```bash
pnpm add -D vitest @vitest/ui jsdom @testing-library/react @testing-library/user-event @testing-library/jest-dom
```

Add to `vite.config.ts`:

```ts
/// <reference types="vitest" />
// ...inside defineConfig:
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
  },
```

Create `src/test/setup.ts`:

```ts
import '@testing-library/jest-dom'
```

Add to `package.json` scripts:

```json
"test": "vitest run",
"test:ui": "vitest --ui"
```

---

### Step 5 — Add `.gitignore` entries

Ensure these are present (Vite scaffold usually includes them):

```
node_modules/
dist/
.env
.env.local
```

---

### Step 6 — Verify

```bash
pnpm dev        # dev server should start on http://localhost:5173
pnpm build      # should compile without errors
pnpm test       # should find 0 tests and exit 0
```

---

## Common Mistakes

| Mistake | Symptom | Fix |
|---------|---------|-----|
| Missing `@types/node` | `path` import errors in `vite.config.ts` | `pnpm add -D @types/node` |
| `verbatimModuleSyntax` without `import type` | TS error on type-only imports | Use `import type { Foo }` for type imports |
| Path alias works in TS but not at runtime | `@/` imports 404 in browser | Add `resolve.alias` to `vite.config.ts` (step 2) |
| `exactOptionalPropertyTypes` breaks existing types | Type errors on `foo?: string` assigned `undefined` | Assign explicitly or mark as `foo?: string | undefined` |
