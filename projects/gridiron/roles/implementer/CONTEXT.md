# Implementer — Gridiron Override

Extends the global workspace implementer role.
Read the global contract first: `roles/implementer/CONTEXT.md` (workspace root).

## Gridiron additions

**Invoke ponytail at session start:** `/ponytail` (full mode)

Before writing each module, run the ponytail ladder:
- Does this module need to exist at all? (YAGNI)
- Can stdlib or an already-installed dep handle it?
- Is one function sufficient instead of a class or module?
- Default to the minimum code that satisfies the architect's interface.

**Engine privacy:** code under `gridiron/engine/` is PRIVATE — never push to public remote.
Mark any file written to `engine/` in the Files Produced table with `[PRIVATE]`.

**Output files for gridiron:**
- Backend phase → `projects/gridiron/roles/implementer/output/backend-output.md`
- Frontend phase → `projects/gridiron/roles/implementer/output/output.md`
