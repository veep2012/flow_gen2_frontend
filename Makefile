CONTAINER_ENGINE ?= podman
DB_CONTAINER_NAME ?= flow_gen2_postgres_local
DB_IMAGE ?= postgres:18.1
BACKEND_INIT_DIR ?= ../flow_gen2_backend/ci/init
DB_VOLUME ?= flow_gen2_local_pg_data
DB_PORT ?= 5432
POSTGRES_USER ?= flow_user
POSTGRES_PASSWORD ?= flow_pass
POSTGRES_DB ?= flow_db
APP_DB_USER ?= app_user
APP_DB_PASSWORD ?= app_pass
MINIO_CONTAINER_NAME ?= flow_gen2_minio_local
MINIO_IMAGE ?= minio/minio:RELEASE.2025-09-07T16-13-09Z
MINIO_VOLUME ?= flow_gen2_local_minio_data
MINIO_PORT ?= 9000
MINIO_CONSOLE_PORT ?= 9001
MINIO_ROOT_USER ?= flow_minio
MINIO_ROOT_PASSWORD ?= change_me_now
MINIO_BUCKET ?= flow-default
MINIO_MC_IMAGE ?= minio/mc:latest
API_CONTAINER_NAME ?= flow_gen2_api_local
API_IMAGE ?= localhost/flow_gen2_api:latest
API_PORT ?= 5556
API_WAIT_TIMEOUT ?= 30
APP_ENV ?= local
APP_USER ?= KONI
ALLOWED_ORIGINS ?= http://localhost,http://localhost:5558,http://127.0.0.1:5558
UI_NODE_IMAGE ?= node:22.14.0-alpine
UI_NODE_MODULES_VOLUME ?= flow_gen2_frontend_ui_node_modules
UI_CONTAINER_NAME ?= flow_gen2_frontend_ui_local
UI_PORT ?= 5558
UI_HOST ?= 0.0.0.0
FRONTEND_IMAGE_TAG ?= flow-gen2-frontend:local
DOCKERFILE_UI ?= ci/Dockerfile.ui
VITE_API_BASE_URL ?= /api/v1
VITE_AUTH_START_URL ?= /oauth2/start
VITE_ALLOWED_HOSTS ?= flow_ui,frontend,flow_frontend,localhost,127.0.0.1

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
	@awk 'BEGIN {FS=":.*?## "}; /^[a-zA-Z0-9_-]+:.*?##/ {printf "%-24s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: test
test: local-ui-test local-ui-lint local-ui-build ## Run frontend validation

.PHONY: local-postgres-up
local-postgres-up: ## Start local Postgres with backend init SQL from the sibling backend repo
	@test -d "$(BACKEND_INIT_DIR)" || (echo "Backend init directory not found: $(BACKEND_INIT_DIR)" >&2; exit 1)
	-$(CONTAINER_ENGINE) rm -f $(DB_CONTAINER_NAME) >/dev/null 2>&1
	$(CONTAINER_ENGINE) run -d --name $(DB_CONTAINER_NAME) \
		--env POSTGRES_USER=$(POSTGRES_USER) \
		--env POSTGRES_PASSWORD=$(POSTGRES_PASSWORD) \
		--env POSTGRES_DB=$(POSTGRES_DB) \
		-p $(DB_PORT):5432 \
		-v $(abspath $(BACKEND_INIT_DIR)):/docker-entrypoint-initdb.d:ro \
		-v $(DB_VOLUME):/var/lib/postgresql \
		$(DB_IMAGE)
	@ready=; \
	for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30; do \
		if $(CONTAINER_ENGINE) exec $(DB_CONTAINER_NAME) pg_isready -U $(POSTGRES_USER) -d $(POSTGRES_DB) >/dev/null 2>&1 && \
			$(CONTAINER_ENGINE) exec -e PGPASSWORD=$(POSTGRES_PASSWORD) $(DB_CONTAINER_NAME) \
				psql -U $(POSTGRES_USER) -d $(POSTGRES_DB) -Atqc "SELECT 1 FROM ref.users LIMIT 1" >/dev/null 2>&1; then \
			ready=1; break; \
		fi; \
		sleep 1; \
	done; \
	if [ -z "$$ready" ]; then echo "Local Postgres not ready or init SQL did not finish"; exit 1; fi

.PHONY: local-postgres-down
local-postgres-down: ## Stop and remove local Postgres
	-$(CONTAINER_ENGINE) stop $(DB_CONTAINER_NAME)
	-$(CONTAINER_ENGINE) rm $(DB_CONTAINER_NAME)

.PHONY: local-minio-up
local-minio-up: ## Start local MinIO and ensure the default bucket exists
	-$(CONTAINER_ENGINE) rm -f $(MINIO_CONTAINER_NAME) >/dev/null 2>&1
	$(CONTAINER_ENGINE) run -d --name $(MINIO_CONTAINER_NAME) \
		--env MINIO_ROOT_USER=$(MINIO_ROOT_USER) \
		--env MINIO_ROOT_PASSWORD=$(MINIO_ROOT_PASSWORD) \
		-p $(MINIO_PORT):9000 \
		-p $(MINIO_CONSOLE_PORT):9001 \
		-v $(MINIO_VOLUME):/data \
		$(MINIO_IMAGE) server /data --console-address ":9001"
	@ready=; \
	for i in 1 2 3 4 5 6 7 8 9 10; do \
		if curl -fsS http://localhost:$(MINIO_PORT)/minio/health/ready >/dev/null 2>&1; then \
			ready=1; break; \
		fi; \
		sleep 1; \
	done; \
	if [ -z "$$ready" ]; then echo "Local MinIO not ready"; exit 1; fi
	$(CONTAINER_ENGINE) run --rm \
		--env MINIO_ROOT_USER=$(MINIO_ROOT_USER) \
		--env MINIO_ROOT_PASSWORD=$(MINIO_ROOT_PASSWORD) \
		--env MINIO_BUCKET=$(MINIO_BUCKET) \
		--entrypoint /bin/sh \
		$(MINIO_MC_IMAGE) -c '\
			for i in 1 2 3 4 5 6 7 8 9 10; do \
				mc alias set local "http://host.containers.internal:$(MINIO_PORT)" "$$MINIO_ROOT_USER" "$$MINIO_ROOT_PASSWORD" >/dev/null 2>&1 && \
				mc mb --ignore-existing local/"$$MINIO_BUCKET" >/dev/null 2>&1 && exit 0; \
				sleep 1; \
			done; \
			exit 1'

.PHONY: local-minio-down
local-minio-down: ## Stop and remove local MinIO
	-$(CONTAINER_ENGINE) stop $(MINIO_CONTAINER_NAME)
	-$(CONTAINER_ENGINE) rm $(MINIO_CONTAINER_NAME)

.PHONY: local-api-up
local-api-up: local-postgres-up local-minio-up ## Start the local API container from the backend image
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	API_CONTAINER_NAME=$(API_CONTAINER_NAME) \
	API_IMAGE=$(API_IMAGE) \
	API_PORT=$(API_PORT) \
	API_WAIT_TIMEOUT=$(API_WAIT_TIMEOUT) \
	APP_ENV=$(APP_ENV) \
	APP_USER=$(APP_USER) \
	ALLOWED_ORIGINS=$(ALLOWED_ORIGINS) \
	APP_DB_USER=$(APP_DB_USER) \
	APP_DB_PASSWORD=$(APP_DB_PASSWORD) \
	POSTGRES_DB=$(POSTGRES_DB) \
	DB_PORT=$(DB_PORT) \
	MINIO_PORT=$(MINIO_PORT) \
	MINIO_BUCKET=$(MINIO_BUCKET) \
	MINIO_ROOT_USER=$(MINIO_ROOT_USER) \
	MINIO_ROOT_PASSWORD=$(MINIO_ROOT_PASSWORD) \
	bash scripts/local-api-container.sh up

.PHONY: local-api-down
local-api-down: ## Stop and remove the local API container
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	API_CONTAINER_NAME=$(API_CONTAINER_NAME) \
	bash scripts/local-api-container.sh down

.PHONY: local-api-logs
local-api-logs: ## Tail logs from the local API container
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	API_CONTAINER_NAME=$(API_CONTAINER_NAME) \
	bash scripts/local-api-container.sh logs

.PHONY: local-up
local-up: ## Start local Postgres, MinIO, API, and UI
	$(MAKE) local-api-up
	VITE_API_BASE_URL=http://localhost:$(API_PORT)/api/v1 $(MAKE) local-ui-up

.PHONY: local-down
local-down: ## Stop local UI, API, MinIO, and Postgres
	$(MAKE) local-ui-down
	$(MAKE) local-api-down
	$(MAKE) local-minio-down
	$(MAKE) local-postgres-down

.PHONY: lint
lint: local-ui-lint ## Run frontend lint and formatting checks

.PHONY: build
build: local-ui-build ## Build frontend assets into ui/dist

.PHONY: image-build
image-build: ## Build the frontend runtime image
	$(CONTAINER_ENGINE) build \
		-f $(DOCKERFILE_UI) \
		-t $(FRONTEND_IMAGE_TAG) \
		--build-arg VITE_API_BASE_URL=$(VITE_API_BASE_URL) \
		--build-arg VITE_AUTH_START_URL=$(VITE_AUTH_START_URL) \
		--build-arg VITE_ALLOWED_HOSTS=$(VITE_ALLOWED_HOSTS) \
		.

.PHONY: local-npm
local-npm: ## Refresh UI dependencies in the managed node_modules volume
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	bash scripts/local-ui-container.sh run install

.PHONY: local-ui-up
local-ui-up: ## Start the persistent containerized UI dev server
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_CONTAINER_NAME=$(UI_CONTAINER_NAME) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	UI_PORT=$(UI_PORT) \
	UI_HOST=$(UI_HOST) \
	VITE_API_BASE_URL=$(VITE_API_BASE_URL) \
	VITE_AUTH_START_URL=$(VITE_AUTH_START_URL) \
	VITE_ALLOWED_HOSTS=$(VITE_ALLOWED_HOSTS) \
	bash scripts/local-ui-container.sh up

.PHONY: local-ui-down
local-ui-down: ## Stop and remove the persistent containerized UI dev server
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_CONTAINER_NAME=$(UI_CONTAINER_NAME) \
	bash scripts/local-ui-container.sh down

.PHONY: local-ui-logs
local-ui-logs: ## Tail logs from the persistent containerized UI dev server
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_CONTAINER_NAME=$(UI_CONTAINER_NAME) \
	bash scripts/local-ui-container.sh logs

.PHONY: local-ui-test
local-ui-test: ## Run UI unit tests in a short-lived container
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	bash scripts/local-ui-container.sh run test

.PHONY: local-ui-lint
local-ui-lint: ## Run UI lint and formatting checks in a short-lived container
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	bash scripts/local-ui-container.sh run lint

.PHONY: local-ui-build
local-ui-build: ## Run the UI production build in a short-lived container
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	VITE_API_BASE_URL=$(VITE_API_BASE_URL) \
	VITE_AUTH_START_URL=$(VITE_AUTH_START_URL) \
	VITE_ALLOWED_HOSTS=$(VITE_ALLOWED_HOSTS) \
	bash scripts/local-ui-container.sh run build

.PHONY: local-ui-audit
local-ui-audit: ## Run npm audit against the frontend lockfile
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	bash scripts/local-ui-container.sh run audit

.PHONY: local-ui-reset
local-ui-reset: ## Remove the UI container and dependency volume
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_CONTAINER_NAME=$(UI_CONTAINER_NAME) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	bash scripts/local-ui-container.sh reset

.PHONY: local-ui-hard-reset
local-ui-hard-reset: ## Remove the UI container, dependency volume, and pinned Node image
	CONTAINER_ENGINE=$(CONTAINER_ENGINE) \
	UI_CONTAINER_NAME=$(UI_CONTAINER_NAME) \
	UI_NODE_IMAGE=$(UI_NODE_IMAGE) \
	UI_NODE_MODULES_VOLUME=$(UI_NODE_MODULES_VOLUME) \
	bash scripts/local-ui-container.sh hard-reset
