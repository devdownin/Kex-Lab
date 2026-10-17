SHELL := /bin/sh
.DEFAULT_GOAL := setup
COMPOSE := docker compose --env-file versions.env --env-file .env -f compose.yml

.PHONY: observability-smoke demo-lite demo-lite-down release-prepare check setup up down reset status smoke logs components evaluate demo demo-down traffic doctor report wait observability-up observability-down demo-basic demo-lag demo-dlt demo-overload hub-pull hub-up hub-down hub-status health profile-core profile-ai profile-reviews profile-full profile-demo integration-smoke scenario-assert agent-e2e

check:
	sh scripts/check.sh

setup:
	@test -f .env || cp .env.example .env
	@echo "Kex Lab configured. Review .env before using AI features."

up: setup
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) -f compose.operational-reviews.yml down -v --remove-orphans

status:
	sh scripts/status.sh

smoke:
	sh scripts/smoke-test.sh $(or $(PROFILE),ai)

logs:
	$(COMPOSE) logs -f

components:
	sh scripts/components.sh

evaluate:
	sh scripts/evaluate.sh all

demo-lite: setup
	sh scripts/demo-lite.sh

demo-lite-down:
	$(COMPOSE) -f compose.autotune.yml down

release-prepare:
	python3 scripts/prepare-release.py

demo: setup
	sh scripts/quick-demo.sh

traffic: setup
	docker compose --env-file versions.env --env-file .env -f compose.yml -f compose.autotune.yml run --rm traffic

demo-down:
	docker compose --env-file versions.env --env-file .env -f compose.yml -f compose.autotune.yml -f compose.hub.yml down

doctor:
	sh scripts/doctor.sh

wait:
	KEX_LAB_HEALTH_PROFILE=$(or $(PROFILE),ai) sh scripts/wait-ready.sh

report:
	sh scripts/report.sh $(or $(PROFILE),ai)

health:
	sh scripts/health.sh $(or $(PROFILE),ai)

demo-basic: setup
	sh scripts/scenario.sh basic

demo-lag: setup
	sh scripts/scenario.sh lag

demo-dlt: setup
	sh scripts/scenario.sh dlt

demo-overload: setup
	sh scripts/scenario.sh overload

observability-smoke: setup
	sh scripts/observability-smoke.sh

observability-up: setup
	sh scripts/observability.sh up

observability-down:
	sh scripts/observability.sh down

hub-pull:
	sh scripts/hub.sh pull

hub-up: setup
	sh scripts/hub.sh up

hub-down:
	sh scripts/hub.sh down

hub-status:
	sh scripts/hub.sh ps

profile-core: setup
	docker compose --env-file versions.env --env-file .env -f compose.yml up -d kafka explorer

profile-ai: setup
	docker compose --env-file versions.env --env-file .env -f compose.yml up -d kafka explorer agent

profile-reviews: setup
	docker compose --env-file versions.env --env-file .env -f compose.yml -f compose.operational-reviews.yml up -d kafka explorer agent

profile-full: setup
	sh scripts/hub.sh up

profile-demo: demo

integration-smoke: setup
	sh scripts/integration-smoke.sh

scenario-assert: setup
	sh scripts/scenario-assert.sh $(or $(SCENARIO),basic)

agent-e2e: setup
	sh scripts/agent-e2e.sh
