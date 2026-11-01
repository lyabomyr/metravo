# Coding standard

One standard for the whole repository — backend, frontend and tests.
If code and this document disagree, fix one of them in the same commit.

Principles come from *The Pragmatic Programmer*; the rules below are how they
apply here.

| Principle | What it means in this repo |
|---|---|
| **DRY** | Every piece of knowledge has one home. Shared behaviour lives in a base class (`BaseRepository`, `BaseConnector`, `BasePage`, …), never copy-pasted. |
| **Orthogonality** | A service owns its tables, its HTTP routes and its logic. Changing billing never touches connectors. |
| **Design by contract** | Interfaces are `ABC`s (Python) / abstract classes (TypeScript). Implementations are swappable: SQLite ↔ Turso, Stripe ↔ Fake, Firebase ↔ Dev login. |
| **Crash early** | Invalid config fails at startup, not on the first request. Domain errors are typed (`NotFound`, `Forbidden`, `LimitReached`) and mapped to HTTP in one place. |
| **Tracer bullets** | Every feature works end-to-end with fake adapters first, so it is testable without any external account. |
| **No broken windows** | Lint and tests are green on every commit; CI blocks merges otherwise. |
| **Don't program by coincidence** | A comment explains *why*, never *what*. If a number is magic, it gets a name. |

## Layout: one folder per service

```
backend/app/
  core/                 shared infrastructure: config, database, errors, base classes, DI container
  services/<service>/   one business capability
      models.py         domain dataclasses — no I/O
      repository.py     SQL for the tables this service owns (extends BaseRepository)
      service.py        business rules (extends BaseService) — no HTTP, no SQL
      router.py         HTTP only: parse request → call service → return schema
      schemas.py        request/response shapes (pydantic)
      <strategy>.py     interchangeable implementations of one ABC (e.g. providers/)
backend/tests/unit/<service>/   mirrors the service tree
frontend/src/app/
  core/                 API client, auth, base classes, shared UI
  features/<service>/   one folder per backend service it talks to
e2e/                    Cypress end-to-end tests
```

A file does one thing. If a file needs "and" to describe it, split it.

## Dependency direction

```
router → service → repository → Database
              ↘ other services (via constructor, never imports of routers)
```

- Routers never touch SQL. Services never import FastAPI. Repositories never
  call other repositories.
- Everything is wired in **one** place: `app/core/container.py`. Classes
  receive their collaborators in `__init__`; nothing reaches for globals.

## Base classes — extend, don't duplicate

| Base class | Location | Gives you |
|---|---|---|
| `Database` | `core/database.py` | `execute`, `query`, `query_one`; `SqliteDatabase` and `TursoDatabase` implement it |
| `BaseRepository` | `core/repository.py` | `SCHEMA` auto-migration, `_one`, `_all`, `_exec` helpers |
| `BaseService` | `core/service.py` | logger, `require()` guard that raises a typed error |
| `BaseConnector` | `services/connectors/base.py` | URL building, paging, retries, de-duplication inside a scan; a connector only implements `parse()` |
| `BaseCommand` | `services/telegram/commands/base.py` | one Telegram command = one class |
| `PaymentProvider` | `services/billing/providers/base.py` | checkout, portal, webhook parsing |
| `IdentityProvider` | `services/auth/providers/base.py` | turn a credential into a verified email |
| `TenantProvisioner` | `services/tenants/provisioners/base.py` | create a user's own database and issue credentials |
| `BaseApiService` | `frontend/src/app/core/api/base-api.service.ts` | typed HTTP with one base URL |
| `BasePage` | `frontend/src/app/core/ui/base-page.ts` | `loading` / `error` signals and `run()` for any request |

## Naming

- Python: `snake_case` functions, `PascalCase` classes, modules named after the
  one class they hold (`otodom/connector.py` → `OtodomConnector`).
- TypeScript: Angular style guide — `kebab-case.ts` files, `PascalCase` classes.
- Booleans read as questions: `is_due`, `has_credentials`.
- No abbreviations except the industry ones (`url`, `db`, `id`, `api`).

## Errors

Raise from `core/errors.py` only:

| Error | HTTP |
|---|---|
| `NotFound` | 404 |
| `Forbidden` | 403 |
| `Unauthorized` | 401 |
| `LimitReached` | 402 — the user's plan does not allow it |
| `Invalid` | 422 |

One exception handler maps them. Never return error dicts by hand.

## Tests

- **Unit, backend** (`backend/tests/unit/<service>`): no network, SQLite in a
  temp dir, fakes for every external service, a `FixedClock` instead of
  sleeping. Must run in seconds.
- **Unit, frontend** (`*.spec.ts` next to the file, Vitest): logic in core
  classes — not templates; templates are covered end to end.
- **End-to-end** (`e2e/`): Cypress drives the real frontend against the real
  backend running with fake adapters (`APP_ENV=e2e`). One spec per user journey.
- A bug fix starts with a failing test.

## Secrets & config

- All configuration comes from environment variables, read once in
  `core/config.py`. `.env.example` lists every variable with a comment.
- Secrets never go into the repo, logs or API responses — the only exception
  is the database-credentials endpoint, which returns the caller's *own*
  credentials on purpose.

## Cost rule

Everything must run on free tiers. A new dependency on a paid service needs a
free alternative behind the same interface (see `docs/ARCHITECTURE.md`).
