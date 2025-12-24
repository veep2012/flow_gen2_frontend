ENGINE ?= podman
COMPOSE_ENGINE ?= $(ENGINE)-compose
COMPOSE_FILE ?= ci/docker-compose.yml
COMPOSE_PROJECT_NAME ?= flow_gen2
PYTHON_BIN ?= /opt/homebrew/opt/python@3.11/bin/python3.11
DEFAULT_GOAL := help
OS := $(shell uname -s 2>/dev/null || echo Windows_NT)

# Cross-platform helpers and PID files
PID_DIR := .local
API_PID_FILE := $(PID_DIR)/uvicorn.pid
UI_PID_FILE := $(PID_DIR)/vite.pid
ifeq ($(OS),Windows_NT)
PYTHON_BIN ?= python
ACTIVATE_VENV := .venv\Scripts\Activate.ps1
VENV_PY := .venv\Scripts\python.exe
LOCAL_API_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-api.ps1 -PidFile "$(API_PID_FILE)"
LOCAL_UI_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-ui.ps1 -PidFile "$(UI_PID_FILE)"
STOP_API_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-api-stop.ps1 -PidFile "$(API_PID_FILE)"
STOP_UI_CMD := powershell -NoProfile -ExecutionPolicy Bypass -File scripts/local-ui-stop.ps1 -PidFile "$(UI_PID_FILE)"
else
ACTIVATE_VENV := .venv/bin/activate
VENV_PY := .venv/bin/python
LOCAL_API_CMD := PID_FILE="$(API_PID_FILE)" bash scripts/local-api.sh
LOCAL_UI_CMD := PID_FILE="$(UI_PID_FILE)" bash scripts/local-ui.sh
STOP_API_CMD := PID_FILE="$(API_PID_FILE)" bash scripts/local-api-stop.sh
STOP_UI_CMD := PID_FILE="$(UI_PID_FILE)" bash scripts/local-ui-stop.sh
endif

.PHONY: help db-reset app-up app-down rebuild completely-rebuild status local-postgres-up local-postgres-down local-venv local-api-up local-api-down local-npm local-ui-up local-ui-down local-up local-down

help:
	@echo "Available targets:"
	@echo "  app-up         Start API, UI test, and nginx proxy containers (no rebuild)"
	@echo "  app-down       Stop containers"
	@echo "  local-postgres-up   Start Postgres with host port mapping"
	@echo "  local-postgres-down Stop Postgres started locally"
	@echo "  local-venv     Create a local Python venv (.venv) with dependencies"
	@echo "  local-api-up   Run API locally (uvicorn) using local virtual env"
	@echo "  local-api-down Stop local uvicorn (by port 5556)"
	@echo "  local-npm      Install UI dependencies in ./ui"
	@echo "  local-ui-up    Start UI locally (vite dev) on port 5558"
	@echo "  local-ui-down  Stop local UI dev server"
	@echo "  local-up       Start local Postgres, API, and UI (dev mode)"
	@echo "  local-down     Stop local UI, API, and Postgres"
	@echo "  db-reset       Stop and remove containers and volumes"
	@echo "  rebuild        Rebuild all services without dropping volumes"
	@echo "  completely-rebuild Rebuild all services and drop volumes"
	@echo "  status         Show running containers for this project"

db-reset:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v

app-up:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d api ui_api_test nginx

app-down:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

local-postgres-up:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) --profile local up -d postgres_local

local-postgres-down:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) --profile local stop postgres_local

ifeq ($(OS),Windows_NT)
local-venv:
	$(PYTHON_BIN) -m venv .venv
	$(VENV_PY) -m pip install --upgrade pip
	$(VENV_PY) -m pip install -r api/requirements.txt
else
local-venv:
	$(PYTHON_BIN) -m venv .venv && . $(ACTIVATE_VENV) && pip install --upgrade pip && pip install -r api/requirements.txt
endif

local-api-up:
	$(LOCAL_API_CMD)

local-api-down:
	$(STOP_API_CMD)

local-npm:
	cd ui && npm install

local-ui-up:
	$(LOCAL_UI_CMD)

local-ui-down:
	$(STOP_UI_CMD)

local-up: local-postgres-up
	$(MAKE) local-api-up
	$(MAKE) local-ui-up

local-down:
	$(MAKE) local-ui-down
	$(MAKE) local-api-down
	$(MAKE) local-postgres-down

rebuild:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

completely-rebuild:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

status:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps
