.PHONY: ci lint test build up down

# Run the full CI pipeline locally via Dagger
ci:
	dagger call -m ci all --src .

lint:
	dagger call -m ci lint --src .

test:
	dagger call -m ci test --src .

build:
	dagger call -m ci build --src .

# Docker Compose shortcuts
up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f formbricks
