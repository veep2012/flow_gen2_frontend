ENGINE ?= podman
COMPOSE_FILE ?= ci/docker-compose.yml
COMPOSE_PROJECT_NAME ?= flow_gen2
DEFAULT_GOAL := help

.PHONY: help db-up db-down db-logs db-ps db-reset

help:
	@echo "Available targets:"
	@echo "  db-up     Start Postgres via $(ENGINE) compose"
	@echo "  db-down   Stop containers"
	@echo "  db-logs   Tail Postgres logs"
	@echo "  db-ps     Show compose process status"
	@echo "  db-reset  Stop and remove containers and volumes"

db-up:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) up -d postgres

db-down:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down

db-logs:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) logs -f postgres

db-ps:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) ps

db-reset:
	$(ENGINE) compose -p $(COMPOSE_PROJECT_NAME) -f $(COMPOSE_FILE) down -v
