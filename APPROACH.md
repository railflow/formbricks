# APPROACH.md

## What I Built and Why

The core bottleneck: **AI agents can write code, but every change still needs a human to review, approve, and deploy.** I built infrastructure to shrink that loop by automating verification and gating — so humans only intervene when it matters.

### The System

An end-to-end pipeline for agent-authored changes to [Formbricks](https://github.com/formbricks/formbricks) (open-source survey platform, Next.js + Prisma + PostgreSQL):

1. **Local CI via Dagger** — Agents run lint, typecheck, test, and build locally before pushing. Same pipeline runs in CI. No "works on my machine" gaps.
2. **Branch protection** — Direct pushes to `main` are blocked. All changes must go through a PR with passing status checks and at least one approval.
3. **AI code review via cubic.dev** — Every PR gets an automated code review. Catches issues an agent might miss (security, style, logic).
4. **CI via GitHub Actions** — Dagger pipeline runs on every PR. Required to pass before merge.
5. **CD via GitHub Actions** — Merging to `main` auto-deploys to Vercel (app) + Neon (database migrations). Only path to production.
6. **Agent simulation script** — Demonstrates the full flow: branch → change → push → PR → CI → review → merge → deploy.

### Architecture

```
Agent makes change
    │
    ├── Local CI (Dagger) ─── lint, typecheck, test, build
    │
    ▼
Push to feature branch
    │
    ▼
Open PR
    ├── GitHub Actions CI (Dagger) ─── same pipeline
    ├── cubic.dev AI review
    └── Branch protection: 1 approval required
    │
    ▼
Human approves + merges to main
    │
    ▼
GitHub Actions Deploy
    ├── Vercel production deploy
    ├── Prisma migrations on Neon
    └── Smoke test (HTTP health check)
```

### Tech Choices

| Component | Choice | Why |
|-----------|--------|-----|
| App | Formbricks | Real product with UI, DB, user flows. Not a toy. |
| Local CI | Dagger | Runs the same pipeline locally and in CI. Containerized, reproducible. No "push and pray." |
| Remote CI | GitHub Actions | Industry standard. Dagger action makes it trivial. |
| Code review | cubic.dev | AI reviews every PR automatically. Second pair of eyes on agent code. |
| Hosting | Vercel + Neon | Serverless Next.js + serverless Postgres. Preview deploys for PRs. Zero ops. |
| DB | Neon | Branching = instant DB copies for preview environments. |

---

## Threat / Risk Model

### What's dangerous about agent-authored changes?

1. **Secret leakage** — Agent accidentally commits `.env`, API keys, or credentials
2. **Dependency injection** — Agent adds a malicious or vulnerable dependency
3. **SQL injection / XSS** — Agent writes code that doesn't sanitize inputs
4. **Breaking migrations** — Agent generates a migration that drops data
5. **Scope creep** — Agent makes changes beyond what was asked

### How this system handles them

| Risk | Mitigation |
|------|-----------|
| Secret leakage | `.gitignore` covers secrets; PR diff is reviewable; cubic.dev flags credentials |
| Bad dependencies | `pnpm install --frozen-lockfile` in CI rejects lockfile changes; human reviews dependency additions |
| Code vulnerabilities | cubic.dev scans for common vulnerability patterns; lint catches many issues |
| Breaking migrations | Migrations run only on merge to main; Neon branching allows testing against real schema |
| Scope creep | PR template includes checklist; cubic.dev reviews scope; human approval required |

### What's NOT mitigated

- **Subtle logic bugs** that pass tests — requires better test coverage or E2E tests
- **Performance regressions** — no load testing in the pipeline
- **Agent hallucinating test expectations** — agent could write tests that assert wrong behavior

---

## What I Intentionally Left Out

- **E2E tests (Playwright)** — Would add significant value but setup time is high for a day project. The Dagger pipeline is extensible to include them.
- **Canary/blue-green deploys** — Vercel handles this implicitly with instant rollbacks, but I didn't build explicit canary logic.
- **Rollback automation** — Vercel supports instant rollbacks, but there's no automated "rollback on failed smoke test" logic.
- **Neon preview branches per PR** — The infrastructure supports it but I didn't wire up automatic branch creation per PR.
- **Secrets scanning (e.g., truffleHog)** — Would be a simple addition to the Dagger pipeline.
- **DORA metrics / observability dashboard** — Kept it simple with GitHub Actions summaries.

---

## What Breaks First Under Pressure

1. **Build times** — Formbricks is a large monorepo. CI takes 10-15 minutes. At high PR volume, this becomes the bottleneck. Fix: Turborepo remote caching + Dagger caching.
2. **Single Neon database** — All PRs test against the same schema. Concurrent migrations would conflict. Fix: Neon branch-per-PR.
3. **No E2E tests** — Unit tests pass but the app could be broken in user-facing ways. Fix: Add Playwright to the Dagger pipeline.
4. **Human approval** — Still a bottleneck. If the goal is fully autonomous agents, you'd need confidence scoring and auto-merge for low-risk changes.

---

## What I'd Build Next (With More Time)

1. **Risk scoring** — Classify changes by risk (config-only → low, migration → high, new dependency → high) and auto-merge low-risk PRs that pass CI + AI review.
2. **Neon branch-per-PR** — Create an isolated database branch for each PR. Test migrations in isolation.
3. **E2E in Dagger** — Run Playwright tests inside the Dagger pipeline with a real browser.
4. **Secrets scanning** — Add truffleHog or gitleaks to the Dagger pipeline.
5. **Observability** — Deploy time tracking, failure rate, MTTR via GitHub Actions + a simple dashboard.
6. **Auto-rollback** — If smoke test fails post-deploy, automatically roll back to the previous Vercel deployment.
