# Deployment Plan — rsync → git pull

Migrates Hetzner backend deploys from rsync to `git pull` from the public GitHub repo.
Subsequent deploys become a single SSH command. Optional Phase 3 wires GitHub Actions
for push-to-deploy with no manual step.

**Server:** `root@167.233.32.222`  
**Code root on server:** `/srv/` (mirrors monorepo root)  
**Shared venv:** `/srv/.venv`  
**Services:** `red-team-platform` · `llm-safety-monitor` · `error-hide-seek`

---

## Phase 1 — Make repo public (GitHub UI)

1. Go to `https://github.com/fotopnd/muppet-labs/settings`
2. Scroll to **Danger Zone → Change repository visibility**
3. Click **Make public** → confirm

That's it. The public HTTPS URL is:
```
https://github.com/fotopnd/muppet-labs.git
```
No auth required for `git pull` on a public repo.

---

## Phase 2 — Initialise git on the server

SSH in:
```bash
ssh -i /Users/fotopnd/Documents/vault/ssh-key-2026-06-17.key root@167.233.32.222
```

### 2a — Verify .env files are in place

These won't be touched by git (they're gitignored), but confirm them before doing anything:

```bash
ls /srv/projects/red-team-platform/.env
ls /srv/projects/llm-safety-monitor/.env
ls /srv/projects/error-hide-seek/.env
```

All three should exist. If any is missing, copy it from local before continuing:
```bash
# Run locally (not on server):
scp -i /Users/fotopnd/Documents/vault/ssh-key-2026-06-17.key \
  projects/red-team-platform/.env \
  root@167.233.32.222:/srv/projects/red-team-platform/.env
```

### 2b — Initialise git at /srv

```bash
cd /srv
git init
git remote add origin https://github.com/fotopnd/muppet-labs.git
git fetch origin main
```

### 2c — Checkout without touching .env files

Git will refuse to overwrite files that exist unless forced. Since the rsync'd files
match what's in the repo, a force checkout is safe. The .env files are gitignored so
git won't create or delete them.

```bash
git checkout -f -b main --track origin/main
```

Verify the .env files survived:
```bash
ls /srv/projects/red-team-platform/.env
ls /srv/projects/llm-safety-monitor/.env
ls /srv/projects/error-hide-seek/.env
```

### 2d — Install uv and sync the virtualenv

uv is not installed by default on the server. Install it once:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Then sync all workspace members (`--all-packages` is required — plain `uv sync` only
installs the root package's deps, which are none):

```bash
cd /srv
/root/.local/bin/uv sync --all-packages
```

Verify uvicorn landed:

```bash
ls /srv/.venv/bin/uvicorn
```

### 2e — Restart all services and check

```bash
systemctl restart red-team-platform llm-safety-monitor error-hide-seek
systemctl status red-team-platform llm-safety-monitor error-hide-seek --no-pager
```

Check the APIs respond:
```bash
curl -s http://localhost:8003/health | head -c 200
curl -s http://localhost:8002/health | head -c 200
curl -s http://localhost:8004/health | head -c 200
```

---

## Phase 2 complete — subsequent deploy flow

From here, every backend deploy is:

```bash
ssh -i /Users/fotopnd/Documents/vault/ssh-key-2026-06-17.key root@167.233.32.222 \
  "cd /srv && git pull && /root/.local/bin/uv sync --all-packages && systemctl restart red-team-platform llm-safety-monitor error-hide-seek"
```

Or add a Makefile target at the monorepo root:

```makefile
HETZNER_KEY := /Users/fotopnd/Documents/vault/ssh-key-2026-06-17.key
HETZNER_HOST := root@167.233.32.222

deploy-backends:
	ssh -i $(HETZNER_KEY) $(HETZNER_HOST) \
	  "cd /srv && git pull && /root/.local/bin/uv sync --all-packages && \
	   systemctl restart red-team-platform llm-safety-monitor error-hide-seek && \
	   systemctl status red-team-platform llm-safety-monitor error-hide-seek --no-pager"
```

Frontend deploys are unchanged — still `pnpm build` + `wrangler pages deploy`.

---

## Phase 3 (optional) — GitHub Actions push-to-deploy

Automates the backend deploy on every push to `main`. Do this when manual deploy friction
becomes noticeable.

### 3a — Add SSH key to GitHub Secrets

1. Go to `https://github.com/fotopnd/muppet-labs/settings/secrets/actions`
2. New repository secret → name: `HETZNER_SSH_KEY`
3. Value: paste the contents of `/Users/fotopnd/Documents/vault/ssh-key-2026-06-17.key`

### 3b — Create the workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy backends

on:
  push:
    branches: [main]
    paths:
      - 'projects/red-team-platform/**'
      - 'projects/llm-safety-monitor/**'
      - 'projects/error-hide-seek/**'
      - 'packages/**'
      - 'pyproject.toml'
      - 'uv.lock'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Hetzner
        uses: appleboy/ssh-action@v1
        with:
          host: 167.233.32.222
          username: root
          key: ${{ secrets.HETZNER_SSH_KEY }}
          script: |
            cd /srv
            git pull
            /root/.local/bin/uv sync --all-packages
            systemctl restart red-team-platform llm-safety-monitor error-hide-seek
```

The `paths` filter means the action only fires when backend code or dependencies change —
not when you push a frontend-only change or a README update.

### 3c — Test it

Push a trivial change (e.g. a comment in a backend file) and watch the Actions tab at
`https://github.com/fotopnd/muppet-labs/actions`.

---

## Notes

- **Frontend deploys are separate and unchanged.** `wrangler pages deploy` is still the
  mechanism; Cloudflare Pages does not read from GitHub in this setup.
- **`.env` files are never in git.** They live permanently on the server at
  `/srv/projects/<project>/.env`. Rotate a key → `scp` the updated file, restart the service.
- **`uv sync` is idempotent.** It's safe to run on every deploy; it's a no-op if
  `uv.lock` hasn't changed.
- **Year-zero-game** is at `/srv/projects/year-zero-game` on the server but has no
  running service yet. It will be pulled with the rest of the repo when git is initialised.
