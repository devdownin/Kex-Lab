SHELL := /bin/sh
COMPOSE := docker compose -f compose.yml

.PHONY: setup up down reset status smoke logs components evaluate demo demo-down traffic

setup:
	@test -f .env || cp .env.example .env
	@echo "Kex Lab configured. Review .env before using AI features."

up: setup
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v --remove-orphans

status:
	sh scripts/status.sh

smoke:
	sh scripts/smoke-test.sh

logs:
	$(COMPOSE) logs -f

components:
	sh scripts/components.sh

evaluate:
	sh scripts/evaluate.sh all

demo: setup
	sh scripts/demo.sh

traffic: setup
	docker compose -f compose.yml -f compose.autotune.yml run --rm traffic

demo-down:
	docker compose -f compose.yml -f compose.autotune.yml down
