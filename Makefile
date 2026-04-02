CONTAINER_ENGINE ?= podman
UI_NODE_IMAGE ?= node:22.14.0-alpine
UI_NODE_MODULES_VOLUME ?= flow_gen2_frontend_ui_node_modules
UI_CONTAINER_NAME ?= flow_gen2_frontend_ui_local
UI_PORT ?= 5558
UI_HOST ?= 0.0.0.0
FRONTEND_IMAGE_TAG ?= flow-gen2-frontend:local
DOCKERFILE_UI ?= ci/Dockerfile.ui
VITE_API_BASE_URL ?= /api/v1
VITE_AUTH_START_URL ?= /oauth2/start

.DEFAULT_GOAL := help

.PHONY: help
help: ## Show available targets
	@awk 'BEGIN {FS=":.*?## "}; /^[a-zA-Z0-9_-]+:.*?##/ {printf "%-24s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

.PHONY: test
test: local-ui-test local-ui-lint local-ui-build ## Run frontend validation

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
