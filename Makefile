.PHONY: ci lint test build install dev setup env clean up down logs

# ── Local build ──────────────────────────────────────────────────

install:
	corepack enable pnpm
	pnpm install --frozen-lockfile

env:
	@test -f .env || (cp .env.example .env && \
		RANDOM_KEY=$$(openssl rand -hex 32) && \
		sed -i.bak "s/ENCRYPTION_KEY=.*/ENCRYPTION_KEY=$$RANDOM_KEY/" .env && \
		sed -i.bak "s/CRON_SECRET=.*/CRON_SECRET=$$RANDOM_KEY/" .env && \
		sed -i.bak "s/NEXTAUTH_SECRET=.*/NEXTAUTH_SECRET=$$RANDOM_KEY/" .env && \
		rm -f .env.bak && \
		echo ".env created with generated secrets")

setup: env install
	pnpm db:generate

build: install
	pnpm build --filter=@formbricks/web...

dev: setup
	pnpm dev

lint: install
	pnpm lint

test: install
	pnpm test

clean:
	pnpm clean

# ── Dagger CI (containerized) ────────────────────────────────────

ci:
	dagger call -m ci all --src .

ci-lint:
	dagger call -m ci lint --src .

ci-test:
	dagger call -m ci test --src .

ci-build:
	dagger call -m ci build --src .

# ── Docker Compose (local stack) ─────────────────────────────────

up: env
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f formbricks
