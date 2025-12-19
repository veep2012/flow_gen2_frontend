ENGINE ?= podman
COMPOSE_ENGINE ?= $(ENGINE)-compose
COMPOSE_FILE ?= ci/docker-compose.yml
COMPOSE_PROJECT_NAME ?= flow_gen2
DEFAULT_GOAL := help

.PHONY: help db-reset api-run app-up app-down rebuild completely-rebuild status

help:
	@echo "Available targets:"
	@echo "  app-up         Start API, UI test, and nginx proxy containers (no rebuild)"
	@echo "  app-down       Stop containers"
	@echo "  db-reset       Stop and remove containers and volumes"
	@echo "  rebuild        Rebuild all services without dropping volumes"
	@echo "  completely-rebuild Rebuild all services and drop volumes"
	@echo "  status         Show running containers for this project"

db-reset:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v

api-run:
	uvicorn api.main:app --host 0.0.0.0 --port 5556 --reload

app-up:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d api ui_api_test nginx

app-down:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

rebuild:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

completely-rebuild:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d --build

status:
	$(COMPOSE_ENGINE) -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps
