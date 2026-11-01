# Everyday commands. `make help` lists them.

NODE_PATH_PREFIX := $(if $(wildcard $(HOME)/.local/node/current/bin),PATH=$(HOME)/.local/node/current/bin:$$PATH,)
E2E_ENV := APP_ENV=e2e PAGE_FETCHER=fixtures FIXTURES_DIR=$(CURDIR)/backend/tests/fixtures/pages \
	CONTROL_DB_URL=sqlite:///$(CURDIR)/backend/data/control.db TENANT_SQLITE_DIR=$(CURDIR)/backend/data/tenants \
	ADMIN_EMAILS=admin@metravo.test SCAN_DELAY_SECONDS=0

.PHONY: help install api web test lint e2e build scan clean

help:          ## show this list
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/\t/'

install:       ## install backend, frontend and e2e dependencies
	cd backend && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd frontend && $(NODE_PATH_PREFIX) npm ci
	cd e2e && $(NODE_PATH_PREFIX) npm ci

api:           ## run the API on :8000 with fake adapters (no accounts needed)
	cd backend && $(E2E_ENV) .venv/bin/uvicorn app.main:create_app --factory --port 8000 --reload

web:           ## run the Angular app on :4200
	cd frontend && $(NODE_PATH_PREFIX) npx ng serve --port 4200

lint:          ## ruff
	cd backend && .venv/bin/ruff check .

test:          ## backend + frontend unit tests
	cd backend && .venv/bin/pytest
	cd frontend && $(NODE_PATH_PREFIX) npx ng test --watch=false

e2e:           ## Cypress — needs `make api` and `make web` running
	cd e2e && $(NODE_PATH_PREFIX) npx cypress run

build:         ## production build of the frontend
	cd frontend && $(NODE_PATH_PREFIX) npx ng build

scan:          ## one scan run with the current environment
	cd backend && .venv/bin/python -m app.cli scan

clean:         ## remove local databases
	rm -rf backend/data
