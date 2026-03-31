# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

DevOps infrastructure for autonomous AI agent code delivery, built around [Formbricks](https://github.com/railflow/formbricks) (Next.js + Prisma + PostgreSQL survey platform). The infrastructure automates verification and deployment of agent-authored changes.

## Commands

```bash
# Local development — run Formbricks + deps
docker compose up -d          # or: make up
docker compose down            # or: make down

# Local CI via Dagger (runs lint, typecheck, test, build)
make ci                        # full pipeline
make lint                      # ESLint only
make typecheck                 # TypeScript type check only
make test                      # Vitest only
make build                     # build only

# Individual Dagger calls
dagger call -m ci all --src .
dagger call -m ci lint --src .

# Simulate an agent-authored PR
./scripts/simulate-agent-change.sh

# Setup branch protection (requires gh CLI with admin access)
./scripts/setup-branch-protection.sh
```

## Architecture

```
apps/                 → Formbricks application code
packages/             → Shared monorepo packages
ci/                   → Dagger Python module (CI pipeline)
  src/ci/main.py      → Pipeline: lint, typecheck, test, build, all
.github/
  workflows/ci.yml    → Runs Dagger CI on every PR
  workflows/deploy.yml → Deploys to Vercel + Neon on push to main
  CODEOWNERS           → Routes all PRs to cubic.dev for AI review
  pull_request_template.md
scripts/
  setup-branch-protection.sh → Configures GitHub branch rules
  simulate-agent-change.sh   → Demo script for agent flow
docker-compose.yml    → Local stack: Formbricks + Postgres + Redis + MinIO + Mailhog
vercel.json           → Vercel deployment config
```

## Key Constraints

- **No direct pushes to main** — all changes must go through PRs
- **cubic.dev reviews every PR** — configured via CODEOWNERS
- **CI must pass before merge** — Dagger pipeline is a required status check
- **CD only on main** — deploy.yml triggers only on push to main
- **Secrets in GitHub Secrets** — VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID, DATABASE_URL

## Environment

- Copy `.env.example` to `.env` for local Docker Compose
- Formbricks secrets: generate with `openssl rand -hex 32` for NEXTAUTH_SECRET, ENCRYPTION_KEY, CRON_SECRET
- Vercel/Neon config is stored in GitHub Secrets, not in `.env`
