CONTAINER_ENGINE ?= podman
COMPOSE_FILE ?= ci/docker-compose.yml
COMPOSE_PROJECT_NAME ?= flow_gen2
NO_CACHE ?=
DB_CONTAINER_NAME ?= flow_gen2_postgres_local
DB_IMAGE ?= postgres:18.1
DB_VOLUME ?= flow_gen2_local_pg_data
DB_PORT ?= 5432
DB_PORT_FLAG := $(if $(DB_PORT),-p $(DB_PORT):5432,)
POSTGRES_USER ?= flow_user
POSTGRES_PASSWORD ?= flow_pass
POSTGRES_DB ?= flow_db
MINIO_CONTAINER_NAME ?= flow_gen2_minio_local
MINIO_IMAGE ?= minio/minio:RELEASE.2025-09-07T16-13-09Z
MINIO_VOLUME ?= flow_gen2_local_minio_data
MINIO_PORT ?= 9000
MINIO_CONSOLE_PORT ?= 9001
MINIO_PORT_FLAG := $(if $(MINIO_PORT),-p $(MINIO_PORT):9000,)
MINIO_CONSOLE_PORT_FLAG := $(if $(MINIO_CONSOLE_PORT),-p $(MINIO_CONSOLE_PORT):9001,)
MINIO_ROOT_USER ?= flow_minio
MINIO_ROOT_PASSWORD ?= change_me_now
MINIO_BUCKET ?= flow-default
MINIO_ENDPOINT ?= http://host.containers.internal:$(MINIO_PORT)
MINIO_MC_IMAGE ?= minio/mc:latest
TEST_DB_CONTAINER_NAME ?= flow_gen2_postgres_test
TEST_DB_PORT ?= 5433
TEST_DB_PORT_FLAG := $(if $(TEST_DB_PORT),-p $(TEST_DB_PORT):5432,)
TEST_DB_HOST ?= localhost
TEST_DB_NAME ?= flow_db_test
TEST_DB_USER ?= postgres
TEST_DB_PASSWORD ?= postgres

PID_DIR := .local
API_PID_FILE := $(PID_DIR)/uvicorn.pid
UI_PID_FILE := $(PID_DIR)/vite.pid
UI_ALT_PID_FILE := $(PID_DIR)/vite-alt.pid
UI_LOG_FILE := $(PID_DIR)/vite.log
UI_ALT_LOG_FILE := $(PID_DIR)/vite-alt.log
PYTHON_BIN ?= /opt/homebrew/opt/python@3.11/bin/python3.11
LOCAL_API_PORT ?= 5556
API_WAIT_TIMEOUT ?= 30

OS := $(shell uname -s 2>/dev/null || echo Windows_NT)
ifeq ($(OS),Windows_NT)
PYTHON_BIN ?= python
ACTIVATE_VENV := .venv\Scripts\Activate.ps1
VENV_PY := .venv\Scripts\python.exe
LOCAL_API_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-api.ps1
LOCAL_UI_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-ui.ps1 -PidFile "$(UI_PID_FILE)"
LOCAL_UI_ALT_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-ui.ps1 -PidFile "$(UI_ALT_PID_FILE)" -ProjectPath "ui_alt" -UiPort "5560"
STOP_API_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-api-stop.ps1 -PidFile "$(API_PID_FILE)"
STOP_UI_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-ui-stop.ps1 -PidFile "$(UI_PID_FILE)"
STOP_UI_ALT_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-ui-stop.ps1 -PidFile "$(UI_ALT_PID_FILE)"
else
ACTIVATE_VENV := .venv/bin/activate
VENV_PY := .venv/bin/python
LOCAL_API_CMD := bash scripts/local-api.sh
LOCAL_UI_CMD := PID_FILE="$(UI_PID_FILE)" LOG_FILE="$(UI_LOG_FILE)" bash scripts/local-ui.sh
LOCAL_UI_ALT_CMD := PID_FILE="$(UI_ALT_PID_FILE)" LOG_FILE="$(UI_ALT_LOG_FILE)" PROJECT_PATH="ui_alt" UI_PORT="5560" bash scripts/local-ui.sh
STOP_API_CMD := bash scripts/local-api-stop.sh
STOP_UI_CMD := PID_FILE="$(UI_PID_FILE)" bash scripts/local-ui-stop.sh
STOP_UI_ALT_CMD := PID_FILE="$(UI_ALT_PID_FILE)" bash scripts/local-ui-stop.sh
endif

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
	@awk 'BEGIN {FS=":.*?## "}; /^[a-zA-Z_-]+:.*?##/ {printf "%-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST) > .local/.make-help.tmp
	@for target in local-up local-down local-venv local-npm local-postgres-up local-postgres-down local-minio-up local-minio-down minio-init test-db-up test-db-down local-api-up local-api-down local-ui-up local-ui-down local-ui-alt-start local-ui-alt-stop db-up db-down minio-up minio-down up down build rebuild completely-rebuild logs help test audit; do \
		grep -E "^$${target} " .local/.make-help.tmp || true; \
	done
	@rm -f .local/.make-help.tmp

.PHONY: test
test: ## Run unit tests
	$(MAKE) test-db-up
	DATABASE_URL=postgresql+psycopg://$(TEST_DB_USER):$(TEST_DB_PASSWORD)@$(TEST_DB_HOST):$(TEST_DB_PORT)/$(TEST_DB_NAME) \
		ENV=ci_test \
		API_PORT=4175 \
		PID_FILE="$(PID_DIR)/uvicorn-test.pid" \
		LOG_FILE="$(PID_DIR)/uvicorn-test.log" \
		$(LOCAL_API_CMD)
	@ready=; \
	for i in 1 2 3; do \
		API_BASE=http://localhost:4175 API_PREFIX= API_WAIT_TIMEOUT=$(API_WAIT_TIMEOUT) $(PYTHON_BIN) scripts/wait-for-api.py && ready=1 && break; \
		PID_FILE="$(PID_DIR)/uvicorn-test.pid" $(STOP_API_CMD) || true; \
		DATABASE_URL=postgresql+psycopg://$(TEST_DB_USER):$(TEST_DB_PASSWORD)@$(TEST_DB_HOST):$(TEST_DB_PORT)/$(TEST_DB_NAME) \
			ENV=ci_test \
			API_PORT=4175 \
			PID_FILE="$(PID_DIR)/uvicorn-test.pid" \
			LOG_FILE="$(PID_DIR)/uvicorn-test.log" \
			$(LOCAL_API_CMD); \
	done; \
	if [ -z "$$ready" ]; then echo "API not ready; log: $(PID_DIR)/uvicorn-test.log"; exit 1; fi
	pytest -m "not api_smoke"; \
	status=$$?; \
	if [ $$status -eq 0 ]; then \
		API_BASE=http://localhost:4175 API_PREFIX=/api/v1 pytest -m api_smoke; \
		status=$$?; \
	fi; \
	PID_FILE="$(PID_DIR)/uvicorn-test.pid" $(STOP_API_CMD) || true; \
	$(MAKE) test-db-down; \
	exit $$status

.PHONY: audit audit-python audit-node
audit: audit-python audit-node ## Run dependency vulnerability audits

audit-python: ## Run pip-audit against API requirements
	$(PYTHON_BIN) -m pip_audit -r api/requirements.txt

audit-node: ## Run npm audit against UI lockfiles
	cd ui && npm audit --package-lock-only
	cd ui_alt && npm audit --package-lock-only

.PHONY: build
build: ## Build services with compose
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) build $(if $(NO_CACHE),--no-cache,)

.PHONY: up
up: ## Start services with compose
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) up -d

.PHONY: down
down: ## Stop services with compose
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) down

.PHONY: completely-rebuild
completely-rebuild: ## Drop containers and volumes, then rebuild services
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) kill --all || true
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) down -v --remove-orphans --timeout 0 || true
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) build

.PHONY: rebuild
rebuild: ## Stop containers, remove them (keep volumes), then rebuild services
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) kill --all || true
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) down --remove-orphans --timeout 0 || true
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) build

.PHONY: logs
logs: ## Tail logs from compose services
	$(CONTAINER_ENGINE)-compose -p $(COMPOSE_PROJECT_NAME) --env-file /dev/null -f $(COMPOSE_FILE) logs -f

.PHONY: db-up
db-up: ## Start standalone Postgres with podman (no port exposed unless DB_PORT is set)
	$(CONTAINER_ENGINE) run -d --name $(DB_CONTAINER_NAME) \
		--env POSTGRES_USER=$(POSTGRES_USER) \
		--env POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		--env POSTGRES_DB=$(POSTGRES_DB) \
		$(DB_PORT_FLAG) \
		-v $(CURDIR)/ci/init/flow_init.sql:/docker-entrypoint-initdb.d/00_flow_init.sql:ro \
		-v $(CURDIR)/ci/init/flow_seed.sql:/docker-entrypoint-initdb.d/01_flow_seed.sql:ro \
		-v $(DB_VOLUME):/var/lib/postgresql \
		$(DB_IMAGE)

.PHONY: db-down
db-down: ## Stop and remove standalone Postgres container started by db-up
	-$(CONTAINER_ENGINE) stop $(DB_CONTAINER_NAME)
	-$(CONTAINER_ENGINE) rm $(DB_CONTAINER_NAME)

.PHONY: minio-up
minio-up: ## Start standalone MinIO with podman (no ports exposed unless MINIO_PORT is set)
	$(CONTAINER_ENGINE) run -d --name $(MINIO_CONTAINER_NAME) \
		--env MINIO_ROOT_USER=$(MINIO_ROOT_USER) \
		--env MINIO_ROOT_PASSWORD=$(MINIO_ROOT_PASSWORD) \
		$(MINIO_PORT_FLAG) \
		$(MINIO_CONSOLE_PORT_FLAG) \
		-v $(MINIO_VOLUME):/data \
		$(MINIO_IMAGE) server /data --console-address ":9001"
	$(MAKE) minio-init

.PHONY: minio-init
minio-init: ## Ensure MinIO default bucket exists (ignore if already present)
	$(CONTAINER_ENGINE) run --rm \
		--env MINIO_ROOT_USER=$(MINIO_ROOT_USER) \
		--env MINIO_ROOT_PASSWORD=$(MINIO_ROOT_PASSWORD) \
		--env MINIO_BUCKET=$(MINIO_BUCKET) \
		--env MINIO_ENDPOINT=$(MINIO_ENDPOINT) \
		--entrypoint /bin/sh \
		$(MINIO_MC_IMAGE) -c '\
			for i in 1 2 3 4 5 6 7 8 9 10; do \
				mc alias set local "$$MINIO_ENDPOINT" "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null 2>&1 && \
				mc mb --ignore-existing local/"$$MINIO_BUCKET" >/dev/null 2>&1 && exit 0; \
				sleep 1; \
			done; \
			exit 1'

.PHONY: minio-down
minio-down: ## Stop and remove standalone MinIO container started by minio-up
	-$(CONTAINER_ENGINE) stop $(MINIO_CONTAINER_NAME)
	-$(CONTAINER_ENGINE) rm $(MINIO_CONTAINER_NAME)

.PHONY: test-db-up
test-db-up: ## Start temporary Postgres for tests (no volume)
	$(CONTAINER_ENGINE) run -d --name $(TEST_DB_CONTAINER_NAME) \
		--env POSTGRES_USER=$(TEST_DB_USER) \
		--env POSTGRES_PASSWORD=$(TEST_DB_PASSWORD) \
		--env POSTGRES_DB=$(TEST_DB_NAME) \
		$(TEST_DB_PORT_FLAG) \
		$(DB_IMAGE)
	@ready=; \
	for i in 1 2 3 4 5 6 7 8 9 10; do \
		if $(CONTAINER_ENGINE) exec $(TEST_DB_CONTAINER_NAME) pg_isready -U $(TEST_DB_USER) -d $(TEST_DB_NAME) >/dev/null 2>&1; then \
			ready=1; break; \
		fi; \
		sleep 1; \
	done; \
	if [ -z "$$ready" ]; then echo "Test DB not ready"; exit 1; fi
	$(CONTAINER_ENGINE) cp $(CURDIR)/ci/init/flow_init.sql $(TEST_DB_CONTAINER_NAME):/tmp/flow_init.sql
	$(CONTAINER_ENGINE) cp $(CURDIR)/ci/init/flow_seed.sql $(TEST_DB_CONTAINER_NAME):/tmp/flow_seed.sql
	$(CONTAINER_ENGINE) exec -e PGPASSWORD=$(TEST_DB_PASSWORD) $(TEST_DB_CONTAINER_NAME) \
		psql -U $(TEST_DB_USER) -d $(TEST_DB_NAME) -v ON_ERROR_STOP=1 -f /tmp/flow_init.sql
	$(CONTAINER_ENGINE) exec -e PGPASSWORD=$(TEST_DB_PASSWORD) $(TEST_DB_CONTAINER_NAME) \
		psql -U $(TEST_DB_USER) -d $(TEST_DB_NAME) -v ON_ERROR_STOP=1 -f /tmp/flow_seed.sql

.PHONY: test-db-down
test-db-down: ## Stop and remove temporary test Postgres container
	-$(CONTAINER_ENGINE) stop $(TEST_DB_CONTAINER_NAME)
	-$(CONTAINER_ENGINE) rm $(TEST_DB_CONTAINER_NAME)

.PHONY: local-postgres-up
local-postgres-up: ## Start local Postgres with host port mapping
	$(MAKE) db-up

.PHONY: local-postgres-down
local-postgres-down: ## Stop local Postgres started by local-postgres-up
	$(MAKE) db-down

.PHONY: local-minio-up
local-minio-up: ## Start local MinIO with host port mapping
	$(MAKE) minio-up

.PHONY: local-minio-down
local-minio-down: ## Stop local MinIO started by local-minio-up
	$(MAKE) minio-down

.PHONY: local-venv
local-venv: ## Create a local Python venv with dependencies
ifeq ($(OS),Windows_NT)
	$(PYTHON_BIN) -m venv .venv
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -r api/requirements.txt
else
	$(PYTHON_BIN) -m venv .venv && . $(ACTIVATE_VENV) && pip install --upgrade pip && pip install -r api/requirements.txt
endif

.PHONY: local-api-up
local-api-up: ## Run API locally (uvicorn)
	$(MAKE) test
	PID_FILE="$(API_PID_FILE)" LOG_FILE="$(PID_DIR)/uvicorn.log" $(LOCAL_API_CMD)

.PHONY: local-api-down
local-api-down: ## Stop local uvicorn using PID file
	PID_FILE="$(API_PID_FILE)" $(STOP_API_CMD)

.PHONY: local-npm
local-npm: ## Install UI dependencies in ./ui
	cd ui && npm install

.PHONY: local-ui-up
local-ui-up: ## Start UI locally (vite dev)
	$(LOCAL_UI_CMD)

.PHONY: local-ui-down
local-ui-down: ## Stop local UI dev server using PID file
	$(STOP_UI_CMD)

.PHONY: local-ui-alt-start
local-ui-alt-start: ## Start UI alt locally (vite dev on port 5560)
	$(LOCAL_UI_ALT_CMD)

.PHONY: local-ui-alt-stop
local-ui-alt-stop: ## Stop UI alt dev server using PID file
	$(STOP_UI_ALT_CMD)

.PHONY: local-up
local-up: local-postgres-up local-minio-up ## Start local Postgres, MinIO, API, and UI
	$(MAKE) local-api-up
	$(MAKE) local-ui-up

.PHONY: local-down
local-down: ## Stop local UI, API, MinIO, and Postgres
	$(MAKE) local-ui-down
	$(MAKE) local-api-down
	$(MAKE) local-minio-down
	$(MAKE) local-postgres-down
