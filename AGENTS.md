# AGENTS.md

Instructions for any AI agent (Claude Code, Codex, Cursor, …) working in this
repository. Read this file, then `docs/CODING_STANDARD.md` and
`docs/ARCHITECTURE.md`, before changing anything. The README is the human
guide; this file is how to *work* here.

## The product in two lines

A multi-tenant flat/house scanner: each user signs in by email, gets their own
Turso database, saves searches, and receives new listings in Telegram. It runs
entirely on free tiers, with every secret held in GitHub Secrets.

## Non-negotiables

1. **Zero cost.** Nothing may require a paid plan or a bank card. A new
   external service must have a free tier *and* sit behind an interface with
   a local fake (see the table in `docs/ARCHITECTURE.md`).
2. **Secrets live only in GitHub Secrets.** Never commit, log, print or
   return a secret. Hosts receive them from `.github/workflows/deploy.yml`.
   `.env.example` documents every variable.
3. **Green before done.** `make lint`, `make test` and `make e2e` pass on every
   commit. CI blocks a deploy otherwise.
4. **Works without accounts.** Every feature must run locally and in tests with
   fake adapters (`APP_ENV=e2e`), with no network.
5. **No bot-detection circumvention.** Do not add IP rotation, proxies,
   CAPTCHA solving or fingerprint spoofing to get past a portal that blocks
   us. A blocked portal returns an error for that source; the scan goes on.

## How to think — the roles to wear

Switch between these deliberately. Most mistakes come from staying in one role
too long.

### Analyst — before writing code
- Restate the request as a user-visible outcome and its acceptance check
  ("a Free user cannot pick a 15-minute interval; the option is shown locked").
- Find the existing code that already does half of it (`grep` the service
  folder first). Most features here are a new field and a rule in one service.
- Name what is out of scope, and the decision a human must make, if any. Ask
  only when the answer changes what you build.

### Architect — where it goes
- One capability = one folder in `backend/app/services/<service>/` and one in
  `frontend/src/app/features/<service>/`. A service owns its tables and routes.
- Dependencies point one way: `router → service → repository → Database`.
  Wire objects only in `core/container.py`.
- Control DB (ours: users, plans, links) vs tenant DB (the user's: searches,
  listings). Put data in the database of whoever owns it.
- Prefer a new implementation of an existing interface over a new code path:
  `PaymentProvider`, `IdentityProvider`, `TenantProvisioner`, `PageFetcher`,
  `BaseConnector`, `BaseCommand`.
- Infrastructure that a free tier lets us manage as code goes in
  `infra/terraform` (OpenTofu); what it does not (Render free) goes in
  `render.yaml`. Explain any exception in `infra/terraform/README.md`.

### Pragmatic engineer — while writing code
Straight from *The Pragmatic Programmer*:
- **DRY**: one home for each piece of knowledge. Shared behaviour goes in a
  base class (`BaseRepository`, `BaseService`, `BaseConnector`, `BasePage`,
  `BaseApiService`), never copied.
- **Orthogonality**: a change to billing never touches connectors.
- **Crash early**: invalid config fails in `Settings.validate()` at startup;
  domain errors are typed (`core/errors.py`) and mapped to HTTP in one place.
- **Tracer bullets**: make the thinnest end-to-end path work first (fake
  adapter → API → UI → e2e), then widen it.
- **No broken windows**: fix lint, flaky tests and stale docs as you pass.
- **Don't program by coincidence**: if you do not know why it works, find out
  before committing.

### Zero-cost engineer — before adding anything that runs
- Check the free allowance and what happens when it runs out. Write it in
  `docs/ARCHITECTURE.md` → *Free stack*.
- The API is a Render free instance (512 MB, shared CPU, sleeps when idle):
  no heavy dependencies, no headless browsers, no in-memory caches that grow.
- Portals are fetched once per scan for all users (`FetchCache`). Keep it so:
  load on portals must not grow with the number of users.
- GitHub Actions minutes are for CI and deploy only. No schedules there.

### Simplicity & OOP — reviewing your own diff
- Small classes with one reason to change; names that read as the domain
  (`ListingFilter.accepts`, `Search.is_due`).
- Composition through constructor injection; inheritance only for the
  documented base classes.
- No speculative options, flags or layers. Three similar lines are fine; a
  framework for them is not.
- Comments say *why*, never *what*. Match the surrounding code's density.
- Delete code you replaced. Do not leave fallbacks "just in case".

### Tester — proving it works
- Bug fix: a failing test first.
- Backend unit tests in `backend/tests/unit/<service>/` mirror the service;
  use the `container`, `sign_in`, `clock` fixtures and `make_search`.
  No network, no sleeping (`FixedClock.advance`).
- Frontend logic in core classes gets a Vitest spec next to it.
- A new user journey gets a Cypress spec in `e2e/cypress/e2e/`; select
  elements by `data-cy`.
- Portal parsing changes: save a real results page to
  `backend/tests/fixtures/pages/` and assert on it.
- Look at UI changes in a browser at desktop width and at phone width (≤ 390 px).

### Security reviewer — before every commit
- User input reaches SQL only as parameters. Tenant data is read only through
  `TenantService.database_for(user_id)` of the signed-in user.
- Webhooks (Telegram, Stripe) verify their secret or signature.
- Admin routes depend on `admin_user`. The credentials endpoint returns only
  the caller's own database.

### Operator — after merging
- Deploy = merge to `main`; watch `ci` then `deploy` in Actions.
- Check `https://metravo-api.onrender.com/api/health` and the site.
- A failing deploy step names the missing secret; see README §8.

## Map of the code

| You want to… | Look in |
|---|---|
| change settings / env vars | `backend/app/core/config.py`, `backend/.env.example` |
| wire a new class | `backend/app/core/container.py` |
| add a search field | `searches/models.py` → `repository.py` (SCHEMA + columns) → `schemas.py` → `service._validate` → frontend `search.model.ts` + `search-form.component.html` |
| add a filter rule | `scanning/listing_filter.py` |
| add a portal | `connectors/<portal>/connector.py` + `connectors/registry.py` + fixture + test |
| change plans or prices | `billing/plans.py` (the only place tariffs are defined) |
| change the scan schedule | `scanning/scheduler.py`, `searches/models.py` (`SCAN_INTERVALS`) |
| add a Telegram command | `telegram/commands/<name>.py` (extend `BaseCommand`) + `container._telegram_dispatcher` |
| change the look | `frontend/src/styles.css` (all styles; pages only combine its classes) |
| change infrastructure | `infra/terraform/*.tf`, `render.yaml`, `.github/workflows/deploy.yml` |

## Commands

```bash
make install            # once
make api / make web     # run locally on :8000 / :4200 with fake adapters
make lint && make test  # ruff + pytest + vitest
make e2e                # Cypress, with api and web running
```

Node 24+ is required by Angular. If `node -v` is older, use
`~/.local/node/current/bin` when present (the Makefile does).

## Schema changes

`BaseRepository.migrate()` only runs `CREATE TABLE IF NOT EXISTS`. Adding a
column to an existing table needs an explicit migration for databases that
already exist in production. Write it, and test it against a database created
with the old schema.

## Definition of done

- [ ] The acceptance check from the Analyst step passes, by test and by eye.
- [ ] `make lint`, `make test`, `make e2e` are green.
- [ ] Docs that describe the change are updated in the same commit: README
      (human guide), `docs/ARCHITECTURE.md`, `.env.example`,
      `infra/terraform/README.md`.
- [ ] No secret, no paid dependency, no circumvention code added.
- [ ] Commit message says *why*, in the imperative.
