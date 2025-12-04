ENGINE ?= podman
COMPOSE_FILE ?= ci/docker-compose.yml
COMPOSE_PROJECT_NAME ?= flow_gen2
DEFAULT_GOAL := help

.PHONY: help db-logs db-ps db-reset api-run api-up api-logs app-up app-down rebuild completely-rebuild status

help:
	@echo "Available targets:"
	@echo "  app-up    Build and start API (and Postgres via depends_on)"
	@echo "  app-down  Stop containers"
	@echo "  ui-test-up     Build and start UI test container on port 5557"
	@echo "  ui-test-down   Stop UI test container"
	@echo "  db-logs   Tail Postgres logs"
	@echo "  db-ps     Show compose process status"
	@echo "  db-reset  Stop and remove containers and volumes"
	@echo "  api-up    Build and start API container on port 5556"
	@echo "  api-logs  Tail API container logs"
	@echo "  rebuild   Rebuild all services without dropping volumes"
	@echo "  completely-rebuild Rebuild all services and drop volumes"
	@echo "  status    Show running containers for this project"

db-logs:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) logs -f postgres

db-ps:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps

db-reset:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v

api-run:
	uvicorn api.main:app --host 0.0.0.0 --port 5556 --reload

api-up:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build api

api-logs:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) logs -f api

ui-test-up:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build ui_api_test

ui-test-down:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) stop ui_api_test

app-up:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build api

app-down:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

rebuild:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

completely-rebuild:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

status:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps
