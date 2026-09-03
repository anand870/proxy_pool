# ProxyPool local dev / ops shortcuts.
# Override any variable on the command line, e.g:  make health TOKEN=abc PORT=9443

PYTHON        ?= python
HOST          ?= 127.0.0.1
PORT          ?= 9443
CACERT        ?= gateway/tls.crt
# TOKEN falls back to AUTH_TOKEN from .env if present and not passed explicitly.
TOKEN         ?= $(shell [ -f .env ] && sed -n 's/^AUTH_TOKEN=//p' .env)
INSTANCE_NAME ?=
ZONE          ?=
GATEWAY_DOMAIN ?=

CURL = curl -sS --cacert $(CACERT) -H "Authorization: Bearer $(TOKEN)"

.DEFAULT_GOAL := help
.PHONY: help install install-dev gen-cert server scheduler fetchers \
        test test-all cov health get docker-up docker-down deploy clean clean-cert

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | \
	  awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Install runtime dependencies
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install ## Install runtime + test dependencies
	$(PYTHON) -m pip install pytest pytest-cov fakeredis

gen-cert: ## Generate self-signed gateway cert (GATEWAY_DOMAIN=, EXTERNAL_IP=, FORCE=1)
	GATEWAY_DOMAIN="$(GATEWAY_DOMAIN)" EXTERNAL_IP="$(EXTERNAL_IP)" FORCE="$(FORCE)" \
	  bash scripts/gen_gateway_cert.sh

server: ## Run the API server (HTTPS on $(PORT))
	$(PYTHON) proxyPool.py server

scheduler: ## Run the fetch/validate scheduler
	$(PYTHON) proxyPool.py schedule

fetchers: ## List active proxy fetchers
	$(PYTHON) proxyPool.py fetcher

test: ## Run unit + api tests
	pytest tests/unit/ tests/api/

test-all: ## Run the full test suite
	pytest

cov: ## Run tests with coverage report
	pytest --cov=. --cov-report=term-missing

health: ## GET /count/ against a running server
	$(CURL) https://$(HOST):$(PORT)/count/

get: ## GET /get/ against a running server
	$(CURL) https://$(HOST):$(PORT)/get/

docker-up: ## Build and start the docker compose stack
	docker compose up -d --build

docker-down: ## Stop the docker compose stack
	docker compose down

deploy: ## Remote-deploy to a GCP VM (INSTANCE_NAME=, ZONE=, env: AUTH_TOKEN, GATEWAY_DOMAIN)
	AUTH_TOKEN="$(AUTH_TOKEN)" GATEWAY_DOMAIN="$(GATEWAY_DOMAIN)" PORT="$(PORT)" \
	  bash remote_deploy.sh $(INSTANCE_NAME) $(ZONE)

clean: ## Remove python/test caches
	find . -name '__pycache__' -type d -prune -exec rm -rf {} + ; \
	rm -rf .pytest_cache .coverage htmlcov

clean-cert: ## Remove the generated gateway cert + key
	rm -f gateway/tls.crt gateway/tls.key
