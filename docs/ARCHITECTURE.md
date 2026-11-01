# Architecture

## The product in one paragraph

A person signs in with their email, gets **their own database**, saves one or
more searches (city, budget, area, portals), and connects Telegram in two
clicks. A scanner reads Otodom, OLX, Morizon and bailiff auctions, keeps what
matches each search, and sends new flats and price drops to Telegram. Free
gets one search every two hours; Pro (19 zł/month) gets five searches every
15 minutes, bailiff auctions, price-drop alerts and direct credentials to
their database. Everyone can download their data.

## Runtime

```
 Browser ─ Angular (Cloudflare Pages)
              │ Bearer <session JWT>
              ▼
          FastAPI (Render free) ──────────────┐
            ▲        ▲        ▲               │
   Telegram │ Stripe │  cron  │               ▼
   webhook  │ webhook│ (opt.) │      Control DB (Turso)        ← service management
                                     users · tenants · plans
                                     subscriptions · telegram
                                              │ knows where each one is
                                              ▼
                                     User DBs (Turso, one each)
                                     searches · listings · price_changes

 GitHub Actions (scan.yml) ── python -m app.cli scan ──► portals ─► user DBs ─► Telegram
```

- The **API** only answers requests: it never scrapes. That keeps it inside
  the free tier's memory and lets it sleep.
- The **scanner** is a CLI run by GitHub Actions on free runners.
- **Two kinds of database.** The control database is ours — it decides who
  exists, what they pay and where their data lives. Each user's database
  holds only their searches and listings; we can hand out credentials to it
  without exposing anybody else.

## Free stack

| Piece | Service | Free allowance | If it is outgrown |
|---|---|---|---|
| Frontend | Cloudflare Pages | unlimited bandwidth, commercial use OK | — |
| API | Render free web service | 750 h/month (one service 24/7); sleeps after 15 min idle | Koyeb free / Fly.io paid |
| Scanner | GitHub Actions | unlimited minutes on public repos, 2 000 min/month private | self-hosted runner |
| Scan trigger | cron-job.org | free, every minute | — |
| Databases | Turso | free plan includes a limited number of databases — check the current quota | Turso paid, or one shared DB (see below) |
| Sign-in | Firebase Auth (email link + Google) | free; Google sends the emails, no domain needed | — |
| Payments | Stripe | no monthly fee, a cut per payment only | — |

Every external service sits behind an interface with a local fake, so the
whole product runs and is tested with no account at all.

| Interface | Production | Local / tests |
|---|---|---|
| `Database` | `TursoDatabase` | `SqliteDatabase` |
| `TenantProvisioner` | `TursoTenantProvisioner` | `SqliteTenantProvisioner` |
| `IdentityProvider` | `FirebaseIdentityProvider` | `DevIdentityProvider` |
| `PaymentProvider` | `StripePaymentProvider` | `FakePaymentProvider` |
| `TelegramClient` | `HttpTelegramClient` | `RecordingTelegramClient` |
| `PageFetcher` | `HttpPageFetcher` (+ curl fallback for Otodom) | `FixturePageFetcher` |

## Backend services

Each folder under `backend/app/services/` owns its tables, logic and routes.

| Service | Owns | HTTP |
|---|---|---|
| `auth` | identity providers, session tokens | `POST /api/auth/session`, `GET /api/auth/me` |
| `users` | `users` (control DB) | — |
| `tenants` | `tenants` (control DB), provisioning, credentials | `GET /api/database`, `POST /api/database/credentials` |
| `export` | — (reads the user DB) | `GET /api/export/database.sqlite`, `GET /api/export/listings.csv` |
| `searches` | `searches` (user DB) | `/api/searches` CRUD |
| `listings` | `listings`, `price_changes` (user DB) | `GET /api/listings`, `GET /api/listings/price-changes` |
| `connectors` | one sub-folder per portal | — |
| `scanning` | filter, fetch cache, scan run | `POST /api/scan/mine`, `/all` (admin), `/cron` |
| `telegram` | `telegram_chats`, `telegram_link_tokens` (control DB), commands | `POST /api/telegram/link`, `/chats`, `/webhook` |
| `billing` | plans, `subscriptions` (control DB), providers | `/api/billing/plans`, `/checkout`, `/portal`, `/webhook` |
| `admin` | — (reads the control DB) | `/api/admin/overview`, `/users`, `/users/{id}/plan` |
| `system` | — | `GET /api/health`, `GET /api/config` |

## Key flows

**Sign-in.** Frontend gets a credential from Firebase (or an email, in dev) →
`POST /api/auth/session` → the provider verifies it → account is created on
first sign-in **and its database is provisioned** → we return our own JWT.

**Telegram in two clicks.** The page creates a one-time token as it renders,
so “Open Telegram” is a plain `t.me/<bot>?start=<token>` link (click 1).
The user taps **Start** (click 2); the webhook receives `/start <token>`,
links the chat, and the page — polling every 3 s — notices on its own.
Tokens expire after 30 minutes and work once.

**A scan.** For every user, take the searches whose plan interval has
elapsed. For each portal, build the URL from the search and fetch it
**once per run for everyone** (`FetchCache`) — portals see the same load with
one user or a thousand. Filter per search, drop cross-portal duplicates by
price + area + street, store, and send new flats (and, on Pro, price drops).

**Payments.** `POST /api/billing/checkout` → Stripe Checkout → Stripe calls
`/api/billing/webhook` (signature-checked) → the plan changes. Cancelling in
the Customer Portal sends another webhook → back to Free. In test mode the
fake provider plays Stripe with two small pages in the frontend.

## If Turso's free database quota runs out

`TenantProvisioner` is the seam. A `SharedSchemaProvisioner` that keeps
free users in one database (rows keyed by user) and gives a dedicated
database to Pro users only is a single new class plus one line in
`core/container.py`; nothing else changes.
