ENGINE ?= podman
COMPOSE_ENGINE ?= $(ENGINE)-compose
COMPOSE_FILE ?= ci/docker-compose.yml
COMPOSE_PROJECT_NAME ?= flow_gen2
DEFAULT_GOAL := help

.PHONY: help db-logs db-ps db-reset api-run api-up api-logs app-up app-down rebuild completely-rebuild status

help:
	@echo "Available targets:"
	@echo "  app-up         Start API, UI test, and nginx proxy containers (no rebuild)"
	@echo "  app-up-build   Build and start API, UI test, and nginx proxy containers"
	@echo "  app-down       Stop containers"
	@echo "  ui-test-up     Start UI test container on port 5557 (no rebuild)"
	@echo "  ui-test-up-build Build and start UI test container"
	@echo "  ui-test-down   Stop UI test container"
	@echo "  db-logs   Tail Postgres logs"
	@echo "  db-ps     Show compose process status"
	@echo "  db-reset  Stop and remove containers and volumes"
	@echo "  api-up    Start API container on port 5556 (no rebuild)"
	@echo "  api-up-build Build and start API container on port 5556"
	@echo "  api-logs  Tail API container logs"
	@echo "  rebuild   Rebuild all services without dropping volumes"
	@echo "  completely-rebuild Rebuild all services and drop volumes"
	@echo "  status    Show running containers for this project"

db-logs:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) logs -f postgres

db-ps:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps

db-reset:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v

api-run:
	uvicorn api.main:app --host 0.0.0.0 --port 5556 --reload

api-up:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d api

api-up-build:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build api

api-logs:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) logs -f api

ui-test-up:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d ui_api_test

ui-test-up-build:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build ui_api_test

ui-test-down:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) stop ui_api_test

app-up:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d api ui_api_test nginx

app-up-build:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build api ui_api_test nginx

app-down:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

rebuild:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

completely-rebuild:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

status:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps
