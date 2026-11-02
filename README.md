# Metravo

Metravo watches the Polish property portals — Otodom, OLX, Morizon and bailiff
auctions — and sends every new flat or house that matches your search to
Telegram. Each user signs in with their email, gets **their own database**, and
can download it at any time.

It runs entirely on **free tiers**, with no bank card anywhere, and every
secret is kept **in GitHub only**.

- Website: https://metravo.pages.dev
- API: https://metravo-api.onrender.com (`/api/health`, `/docs`)
- Setting it up from zero: **[docs/SETUP.md](docs/SETUP.md)** — every account, every value, where it comes from and where it goes

Contents: [How it works](#how-it-works) · [Who does what](#who-does-what) ·
[Run it locally](#run-it-locally) · [Tests](#tests) · [From push to production](#from-push-to-production) ·
[Monitoring and alerts](#monitoring-and-alerts) · [Everyday tasks](#everyday-tasks) ·
[Repository map](#repository-map) · [Troubleshooting](#troubleshooting)

---

## How it works

```
               ┌──────────────────────────── GitHub ────────────────────────────┐
               │ code · Secrets (the one place settings live) · Actions ci→deploy│
               └──────┬───────────────────────┬─────────────────────┬────────────┘
       OpenTofu apply │      copies secrets,   │ deploy              │ setWebhook
                      ▼                        ▼                     ▼
 Browser ──► Cloudflare Pages ──HTTPS──► Render: FastAPI API ◄──webhook── Telegram
             (Angular site)             + scan scheduler + health monitor     ▲
                                          │        │         │                │ listings, alerts
          Cloudflare Worker (cron 5 min) ─┤        │         └────────────────┘
          checks site + API, alerts admin │        ▼
                         Firebase Auth ◄──┘   Turso (libSQL)
                       (email link, Google)   ├─ metravo-control — accounts, plans, chats, channels
                                              └─ u-<id> — one database per user: searches, listings
                                                      ▲
                     Otodom · OLX · Morizon · Komornik ┘ fetched once per scan for all users
```

**A user's journey**

1. Lands on the website, reads what it does, enters an email. Firebase emails a
   sign-in link (or they use Google). On first sign-in the API creates the
   account **and a database of their own** in Turso.
2. A short tour explains the app. They save a search: buy or rent, flat or
   house, city, budget, area, rooms, price per m², year built, words that must
   appear, portals, and **how often to check** (once a day by default).
3. They connect Telegram in **two clicks**: "Open Telegram", then "Start".
4. Inside the API a scheduler runs every minute. It scans the searches that are
   due, drops duplicates and anything outside the filters, and sends what is
   new. The website, Telegram and error messages are in English, Polish,
   Ukrainian or Russian.

**Plans**

| | Free | Pro (on sale from `PRO_AVAILABLE_FROM`) |
|---|---|---|
| Price | 0 zł | 19 zł / month |
| Saved searches | 1 | 5 |
| Checked | once a day | up to every hour |
| Portals | otodom, olx, morizon | + bailiff auctions (komornik) |
| Delivered to | Telegram | Telegram + email, WhatsApp, Viber, Signal (tick to duplicate) |
| Price-drop alerts | — | yes |
| Your database | download | download + direct credentials |

Payments are off for now (`BILLING_PROVIDER=none`), so Pro is shown as
"coming soon". The extra channels can be ticked today; each starts delivering
as soon as its sender is built, and the user's choice is kept until then (see
`backend/app/services/notifications/`).

---

## Who does what

| Service | Responsible for | Free allowance | Described in |
|---|---|---|---|
| **GitHub** | code, secrets, CI, deploys | unlimited Actions minutes (public repo) | `.github/workflows/` |
| **Cloudflare Pages** | serves the website | unlimited | `infra/terraform/cloudflare.tf` |
| **Cloudflare Workers** | uptime watcher, every 5 min | 100 000 requests/day, cron and KV included | `infra/terraform/monitoring.tf`, `infra/worker/uptime.js` |
| **Render** | runs the API, the scan scheduler and the health monitor | 750 h/month (enough for 24/7) | `render.yaml` |
| **Turso** | the control database + one database per user | free plan | created by CLI; users' databases by the app |
| **Firebase Auth** | email-link and Google sign-in | free | Firebase console |
| **Telegram** | the bot that delivers listings and alerts | free | webhook set by the deploy |
| **OpenTofu** | infrastructure as code, state encrypted in the repo | free | `infra/terraform/` |

**Two kinds of database.** The *control* database is ours: who exists, which
plan, which database belongs to whom, Telegram chats, channel choices. Each
*user* database holds only that user's searches, listings and price changes,
so we can hand out credentials to it without exposing anyone else.

**Why the API scans by itself.** GitHub's scheduled runs on free runners are
delayed by hours and spend minutes. The API instead runs a background
`ScanScheduler`. It also requests its own `/api/health` every 10 minutes:
without that, Render's free instance falls asleep after 15 idle minutes, and a
sleeping scheduler never fires.

**Why Render is not in Terraform.** Render's API does not create free services,
and its Terraform provider cannot update them
([issue #80](https://github.com/render-oss/terraform-provider-render/issues/80)).
Render is described by `render.yaml` instead, which is Render's own
infrastructure-as-code. The full split is in
[infra/terraform/README.md](infra/terraform/README.md).

---

## Run it locally

Requirements: Python 3.11+, Node 24+. No accounts are needed.

```bash
make install
make api      # terminal 1 → http://localhost:8000/docs
make web      # terminal 2 → http://localhost:4200
```

Sign in with any email; no password is needed. The local backend uses stand-ins:
- saved portal pages instead of live scraping;
- a test payment page instead of Stripe;
- a log instead of Telegram;
- SQLite files in `backend/data/` instead of Turso.

`admin@metravo.test` also sees the Admin page.

---

## Tests

```bash
make lint     # ruff
make test     # pytest (backend/tests/unit) + vitest (frontend)
make e2e      # Cypress, with `make api` and `make web` running
```

Every end-to-end case is listed with its expected result in
**[e2e/TEST_CASES.md](e2e/TEST_CASES.md)**. The list covers the landing page, sign-in, the
tour, every search filter, listings, alerts, plans, data export, admin,
languages and phones. CI runs all three levels on every push.

---

## From push to production

```
push ──► ci.yml
          ├─ backend:  ruff + pytest
          ├─ frontend: vitest + production build + uptime-worker tests
          └─ e2e:      API with stand-ins + site → Cypress
      ──► deploy.yml (main only, only after a green CI)
          1. find the API address on Render
          2. OpenTofu apply: Pages project, uptime Worker → site address
          3. copy GitHub Secrets to Render, start the API deploy
          4. build the site with the API address, publish it to Pages
          5. point the Telegram bot's webhook at the API
```

Code that fails CI never reaches production, which is why `render.yaml` has
`autoDeploy: false`.

---

## Monitoring and alerts

Admins are the accounts listed in `ADMIN_EMAILS` that have connected
Telegram. They receive these alerts:

| What | Who notices | When |
|---|---|---|
| Site or API is down | Cloudflare Worker, outside our servers | 2 failed checks in a row (5-minute interval); again when it is back |
| Memory ≥ 80 % of the instance limit | API health monitor | as soon as it happens, and when it recovers |
| CPU ≥ 80 % of the limit for 5 minutes | API health monitor | the instance is too small for the load |
| A scan crashed | API health monitor | on the first crash |
| A portal failed 3 scans in a row | API health monitor | e.g. a portal changed its page or blocks us |

**Admin → System** shows memory, CPU, the last scan, active alerts and the
latest warnings and errors. Full logs are in Render → `metravo-api` → Logs.
Opening the Worker's URL shows its last check.

---

## Everyday tasks

| Task | How |
|---|---|
| Change code | branch → PR → merge to `main`; it deploys itself |
| Change a secret | GitHub Secrets → next deploy, or Actions → deploy → Run workflow |
| Change infrastructure | edit `infra/terraform/*.tf` → merge |
| Change the Pro launch date | `PRO_AVAILABLE_FROM` in `render.yaml` |
| Turn on payments | three Stripe secrets + `BILLING_PROVIDER: stripe` ([docs/SETUP.md](docs/SETUP.md#later-turning-on-payments)) |
| Add a delivery channel | a `ChannelSender` subclass in `services/notifications/senders/`, registered in `core/container.py`; set `live=True` in `channels.py` |
| Add a portal | `connectors/<portal>/connector.py` (extend `BaseConnector`) → `CONNECTOR_CLASSES` → fixture page + test → allow it in `billing/plans.py` |
| Add a language | a catalog in `backend/app/core/i18n/catalogs/` and a folder in `frontend/src/app/core/i18n/locales/`; the compiler and the tests list every missing key |

---

## Repository map

```
backend/                 FastAPI — one folder per service in app/services/
  app/core/              config, database, errors, i18n, base classes, DI container
  app/services/          auth · users · tenants · searches · listings · connectors · scanning
                         notifications · telegram · billing · monitoring · export · admin · system
  tests/unit/            unit tests, mirroring the services
frontend/                Angular — app/core (base classes, i18n, UI) + app/features (one per area)
e2e/                     Cypress specs + TEST_CASES.md
infra/terraform/         OpenTofu: Pages project, uptime Worker
infra/worker/            the uptime Worker's code and tests
.github/workflows/       ci · deploy
.github/scripts/         deploy.py (secrets → Render) · tfstate.sh (encrypted state)
render.yaml              the API service on Render
docs/                    SETUP (step by step) · ARCHITECTURE · CODING_STANDARD
AGENTS.md                rules for AI agents working here
```

---

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Site loads but shows nothing | The API is starting or deploying. Open `/api/health` and wait a minute |
| "This sign-in method is switched off" | Firebase → Authentication → Sign-in method → enable it (Google, or Email link) |
| Sign-in link does nothing | Firebase → Authentication → Settings → Authorized domains must contain `metravo.pages.dev` |
| Render deploy fails right after start | Render → Logs → "Invalid configuration: …" names the missing or broken secret |
| Bot is silent | The latest deploy's step "Point the Telegram bot" must say `Webhook was set` |
| "Infrastructure (OpenTofu)" was skipped | `TF_STATE_PASSPHRASE` or `CLOUDFLARE_API_TOKEN` is missing |
| No admin alerts | Your email must be in `ADMIN_EMAILS` **and** your account must have Telegram connected |
| OLX finds nothing | OLX blocks some server IPs (403); the other portals are unaffected and you get an alert after 3 failures |
| CI is red without a code change | Usually GitHub itself; re-run the failed jobs |
