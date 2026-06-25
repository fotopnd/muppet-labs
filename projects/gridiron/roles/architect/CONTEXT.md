# Architect — Gridiron Override

Extends the global workspace architect role.
Read the global contract first: `roles/architect/CONTEXT.md` (workspace root).

## Gridiron additions

**Invoke ponytail at session start:** `/ponytail` (full mode)

Apply the ponytail decision ladder before designing each component:
- Does this component need to exist? (YAGNI)
- Can an existing dep or stdlib handle it without a new module?
- Flat structure beats layered. One module beats five.
- If complexity is unavoidable, name the concrete requirement forcing it.

**Engine privacy boundary:** any component under `gridiron/engine/` is PRIVATE.
Do not reference engine internals in output.md — the architect output is shareable context.
Mark engine-internal interfaces with `[PRIVATE]` in the Module Interfaces section.

**Output file for gridiron:** `projects/gridiron/roles/architect/output/output.md`
