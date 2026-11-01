# Metravo

New flats from Otodom, OLX, Morizon and bailiff auctions — matched to your
search and sent to your Telegram. Every user gets their own database, can
download it at any time, and on Pro can connect to it directly.

Runs entirely on free tiers: Angular on Cloudflare Pages, FastAPI on Render,
Turso databases, Firebase sign-in, Stripe payments, scans on GitHub Actions.

## Run it locally — no accounts needed

```bash
make install
make api      # terminal 1 → http://localhost:8000/docs
make web      # terminal 2 → http://localhost:4200
```

Sign in with any email. The backend runs with fake adapters: saved portal
pages instead of live scraping, a test payment page instead of Stripe,
logged messages instead of Telegram. `admin@metravo.test` sees the admin
page.

Node 24+ and Python 3.11+ are required.

## Tests

```bash
make lint     # ruff
make test     # backend pytest (backend/tests/unit) + frontend vitest
make e2e      # Cypress (e2e/) — with `make api` and `make web` running
```

CI runs all three on every push; see `.github/workflows/ci.yml`.

## Repository

```
backend/              FastAPI — one folder per service under app/services/
  tests/unit/         unit tests, mirroring the services
  tests/fixtures/     saved portal pages used by tests and e2e
frontend/             Angular — app/core (base classes) + app/features (one per service)
e2e/                  Cypress end-to-end tests
docs/
  ARCHITECTURE.md     how it fits together, the free stack, the main flows
  CODING_STANDARD.md  the one standard for all code here — read before contributing
  DEPLOYMENT.md       one-time setup of every free account, step by step
.github/workflows/    ci · deploy · scan
render.yaml           the API on Render
```

## Adding a portal

1. `backend/app/services/connectors/<portal>/connector.py` — extend
   `BaseConnector`, set `URL_TEMPLATE`, implement `parse()`.
2. Add the class to `CONNECTOR_CLASSES` in `connectors/registry.py`.
3. Save a results page to `backend/tests/fixtures/pages/<host>.html` and add
   a test to `tests/unit/connectors/test_parsers.py`.
4. Allow it in a plan in `billing/plans.py`.
