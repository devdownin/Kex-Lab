SHELL := /bin/sh
COMPOSE := docker compose --env-file versions.env -f compose.yml

.PHONY: setup up down reset status smoke logs components evaluate demo demo-down traffic doctor report wait observability-up observability-down demo-basic demo-lag demo-dlt demo-overload

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
	docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml run --rm traffic

demo-down:
	docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml down

doctor:
	sh scripts/doctor.sh

wait:
	sh scripts/wait-ready.sh

report:
	sh scripts/report.sh

demo-basic: setup
	sh scripts/scenario.sh basic

demo-lag: setup
	sh scripts/scenario.sh lag

demo-dlt: setup
	sh scripts/scenario.sh dlt

demo-overload: setup
	sh scripts/scenario.sh overload

observability-up: setup
	docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml -f compose.observability.yml up -d

observability-down:
	docker compose --env-file versions.env -f compose.yml -f compose.autotune.yml -f compose.observability.yml down
