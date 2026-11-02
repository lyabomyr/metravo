# Architecture

## The product in one paragraph

A person signs in with their email, saves one or more searches — buy or rent, flat or house, city, price from–to, area, rooms, price
per m², words that must appear, portals, how often to check (daily by
default) — and connects Telegram in two clicks. A scanner reads Otodom, OLX,
Morizon and bailiff auctions, keeps what matches each search, and sends new
flats and price drops to Telegram. Free gets one search checked once a day;
Pro ($10/month, on sale from the day in `PRO_AVAILABLE_FROM`) gets five
searches checked up to every hour, bailiff auctions, price-drop alerts, and
the same listings duplicated to email, WhatsApp, Viber and Signal. Everyone
can download their listings as CSV for their own analysis. The
website, Telegram and API errors speak English, Polish, Ukrainian and Russian.

## Runtime

```
 Browser ─ Angular (Cloudflare Pages)
              │ Bearer <session JWT>
              ▼
          FastAPI (Render free) ──────────────┐
          + ScanScheduler + HealthMonitor     │
            ▲        ▲                        ▼
   Telegram │ Stripe │                One database (Turso)
                                     users · plans · subscriptions · telegram
                                     searches · search_matches   (per user_id)
                                     portal_listings · listing_prices (each offer once)

 ScanScheduler (every minute) ──► due searches ──► portals ─► database ─► FanOutNotifier ─► channels
                                └─► HealthMonitor ─► memory / CPU / scan / portal alerts ─► admins' Telegram
 Cloudflare Worker (cron 5 min) ──► site + /api/health ─► down / back-up alerts ─► admins' Telegram
 GitHub Actions ── ci on every push · deploy after green CI on main (no schedules)
```

- The **API also scans.** `ScanScheduler` runs in a background thread started
  with the app (`SCHEDULER_ENABLED=true`). Each minute it scans the searches
  whose own interval has elapsed; runs never overlap. GitHub minutes are spent
  only on CI and deploys.
- **Staying awake.** Render's free service sleeps after 15 idle minutes, and a
  sleeping scheduler never fires, so in production the scheduler also requests
  its own `/api/health` every 10 minutes.
- **Secrets in one place.** GitHub Secrets hold every setting.
  `.github/scripts/deploy.py` copies them to Render and reads back both public
  URLs (Render service, Cloudflare Pages project) for the build and the
  Telegram webhook. `render.yaml` holds only fixed, non-secret settings.
- **Infrastructure as code.** `infra/terraform` (OpenTofu) declares what the
  free tiers let us manage as code — the Cloudflare Pages project — with its
  state encrypted on the `infra-state` branch. Render's free service is
  described by `render.yaml` instead, because Render's API cannot create or
  update free services.
- **Monitoring.** `services/monitoring` reads memory and CPU against the
  container's limits (cgroup, or `MEMORY_LIMIT_MB` / `CPU_CORES`), tracks
  crashed scans and portals failing in a row, and alerts admins when a problem
  starts and when it ends. A down server cannot report itself, so a Worker
  outside it (`infra/worker/uptime.js`) checks the site and the API every 5
  minutes. Admin → System shows the same numbers and the last warnings.
- **Channels.** `services/notifications` keeps, per user, which channels get
  listings. `FanOutNotifier` sends to each switched-on channel that has a
  `ChannelSender`; Telegram is the first. A channel without a sender yet can
  still be ticked and starts delivering the day its sender is added.
- **Languages.** The backend translates with `core/i18n` (one catalog per
  language, `Accept-Language` for API errors, the user's saved language for
  Telegram). The frontend has a dictionary per language and section under
  `core/i18n/locales/`, checked for completeness by the compiler.
- **One database, each offer once.** Everything lives in one Turso database.
  An offer is stored once in `portal_listings` (`ListingCatalog`), with one
  shared price history in `listing_prices`, and is written only when it is
  new, its price moved or a day has passed. `search_matches` says which
  search matched it, for whom, and the price that user was last told; that
  row is who gets notified. Searches and matches carry a `user_id` and their
  repositories extend `OwnedRepository`: opened for one user, every query
  filters by it, so a service cannot forget the filter. Signing up is one row
  insert: nothing to provision, nothing to fail.

## Free stack

| Piece | Service | Free allowance | If it is outgrown |
|---|---|---|---|
| Frontend | Cloudflare Pages | unlimited bandwidth, commercial use OK | — |
| Uptime watcher | Cloudflare Worker + cron + KV | 100 000 requests/day; KV writes only on state change | — |
| API + scanner | Render free web service | 750 h/month (one service 24/7); kept awake by its own ping | Render Starter |
| CI / deploy | GitHub Actions | unlimited on public repos, 2 000 min/month private; no schedules | — |
| Database | Turso, one database | free plan storage and row reads — check the current quota | Turso paid |
| Sign-in | Firebase Auth (email link + Google) | free; Google sends the emails, no domain needed | — |
| Payments | off for now (`BILLING_PROVIDER=none`); Stripe later | Stripe: no monthly fee, a cut per payment | — |

Every external service sits behind an interface with a local fake, so the
whole product runs and is tested with no account at all.

| Interface | Production | Local / tests |
|---|---|---|
| `Database` | `TursoDatabase` | `SqliteDatabase` |
| `IdentityProvider` | `FirebaseIdentityProvider` | `DevIdentityProvider` |
| `PaymentProvider` | `NoPaymentsProvider` now, `StripePaymentProvider` later | `FakePaymentProvider` |
| `TelegramClient` | `HttpTelegramClient` | `RecordingTelegramClient` |
| `PageFetcher` | `HttpPageFetcher` (+ curl fallback for Otodom) | `FixturePageFetcher` |

## Backend services

Each folder under `backend/app/services/` owns its tables, logic and routes.

| Service | Owns | HTTP |
|---|---|---|
| `auth` | identity providers, session tokens | `POST /api/auth/session`, `GET /api/auth/me`, `PUT /api/auth/me/locale` |
| `users` | `users` | — |
| `export` | — (reads the caller's listings) | `GET /api/export/listings.csv` |
| `searches` | `searches` (rows per user) | `/api/searches` CRUD |
| `listings` | `portal_listings`, `listing_prices` (each offer once), `search_matches` (per user) | `GET /api/listings`, `GET /api/listings/price-changes` |
| `connectors` | one sub-folder per portal | — |
| `scanning` | filter, fetch cache, scan run | `POST /api/scan/mine`, `/all` (admin), `/cron` |
| `telegram` | `telegram_chats`, `telegram_link_tokens`, commands, `TelegramSender` | `POST /api/telegram/link`, `/chats`, `/webhook` |
| `notifications` | `notification_settings`, channel catalog, fan-out | `GET /api/notifications/channels`, `PUT /channels/{code}` |
| `monitoring` | probe, health monitor, admin alerts, recent logs | `GET /api/admin/system` |
| `billing` | plans, `subscriptions`, providers | `/api/billing/plans`, `/checkout`, `/portal`, `/webhook` |
| `admin` | — (accounts and plans only) | `/api/admin/overview`, `/users`, `/users/{id}/plan` |
| `system` | — | `GET /api/health`, `GET /api/config` |

## Key flows

**Sign-in.** Frontend gets a credential from Firebase (or an email, in dev) →
`POST /api/auth/session` → the provider verifies it → account is created on
first sign-in → we return our own JWT.

**Telegram in two clicks.** The page creates a one-time token as it renders,
so “Open Telegram” is a plain `t.me/<bot>?start=<token>` link (click 1).
The user taps **Start** (click 2); the webhook receives `/start <token>`,
links the chat, and the page — polling every 3 s — notices on its own.
Tokens expire after 30 minutes and work once. Right after the greeting, in
the background so the webhook answers at once, `ScanService.deliver_now`
sends the listings found before the chat existed (nobody had been told about
them) and scans any search that was never checked.

**Setup is resumable.** Every sign-in lands on `/welcome`, which skips the
steps already done and moves on to the listings when nothing is left, so an
account created in a sign-in that failed halfway is still taken through
setup.

**A scan.** For every user who has a search, take the searches whose own interval has
elapsed (never faster than the plan allows). For each portal, build the URL from the search and fetch it
**once per run for everyone** (`FetchCache`) — portals see the same load with
one user or a thousand. Filter per search, drop cross-portal duplicates by
price + area + street, store, and send new flats (and, on Pro, price drops).

**Payments.** `POST /api/billing/checkout` → Stripe Checkout → Stripe calls
`/api/billing/webhook` (signature-checked) → the plan changes. Cancelling in
the Customer Portal sends another webhook → back to Free. In test mode the
fake provider plays Stripe with two small pages in the frontend.

## Why one database, not one per user

Each user once had their own Turso database. Creating it was a network call
in the middle of signing up that could fail (and did), the free plan caps
how many databases an account may have, and every schema change had to
reach every database. Searches and listings are small; one database with a
`user_id` on each row holds thousands of users. Users still take their data
with them, as a CSV of their listings.
