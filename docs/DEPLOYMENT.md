# Deployment

Everything below is free. Each step is a one-time setup of a few minutes;
nothing is deployed until its secret exists, so the repo stays green
before and during setup.

Order matters only where noted.

## 1. Turso — the databases

```bash
brew install tursodatabase/tap/turso
turso auth signup
turso db create metravo-control                 # the service-management DB
turso db show metravo-control --url             # → CONTROL_DB_URL
turso db tokens create metravo-control          # → CONTROL_DB_TOKEN
turso auth api-tokens mint metravo              # → TURSO_API_TOKEN (creates user DBs)
turso org list                                  # → TURSO_ORG
```

## 2. Firebase — sign-in

1. console.firebase.google.com → Add project (Analytics off).
2. Build → Authentication → Sign-in method → enable **Email link** and **Google**.
3. Authentication → Settings → Authorised domains → add your Pages domain (`metravo.pages.dev`).
4. Project settings → Your apps → Web app → copy the config object.
   - `FIREBASE_PROJECT_ID` = `projectId`
   - `FIREBASE_WEB_CONFIG` = the whole object as one line of JSON (it is public by design).

## 3. Telegram — the bot

1. Talk to @BotFather → `/newbot` → `TELEGRAM_BOT_TOKEN`, and the username → `TELEGRAM_BOT_USERNAME`.
2. Make up a long random `TELEGRAM_WEBHOOK_SECRET`.

## 4. Stripe — payments

1. Sign up; stay in **test mode** until you are ready to charge.
2. Product catalogue → add “Metravo Pro”, recurring, 19 PLN/month → copy the price id → `STRIPE_PRICE_PRO`.
3. Developers → API keys → secret key → `STRIPE_SECRET_KEY`.
4. *(after step 5)* Developers → Webhooks → add `https://<api>/api/billing/webhook`
   with events `checkout.session.completed`, `customer.subscription.updated`,
   `customer.subscription.deleted` → signing secret → `STRIPE_WEBHOOK_SECRET`.
5. Settings → Payment methods → enable cards, BLIK, Przelewy24 as you like.
6. Settings → Billing → Customer portal → enable cancellation.

## 5. Render — the API

1. render.com → New → **Blueprint** → this repository. `render.yaml` defines everything.
2. Fill in the values it asks for (all from steps 1–4), plus:
   - `ADMIN_EMAILS` — your email
   - `FRONTEND_URL`, `CORS_ORIGINS` — `https://metravo.pages.dev`
   - `PUBLIC_API_URL` — the Render URL, e.g. `https://metravo-api.onrender.com`
   - `CRON_SECRET` — a long random string
3. Free services sleep after 15 minutes. Add a cron-job.org job that GETs
   `https://<api>/api/health` every 10 minutes so Telegram replies stay instant.

## 6. Cloudflare Pages — the frontend

1. dash.cloudflare.com → Workers & Pages → Create → Pages → **Direct upload** → name it `metravo`.
2. My profile → API tokens → template “Edit Cloudflare Workers” → `CLOUDFLARE_API_TOKEN`; account id → `CLOUDFLARE_ACCOUNT_ID`.

## 7. GitHub — secrets and variables

Settings → Secrets and variables → Actions.

| Secret | From |
|---|---|
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | step 6 |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET` | step 3 |
| `CONTROL_DB_URL`, `CONTROL_DB_TOKEN`, `TURSO_API_TOKEN`, `TURSO_ORG` | step 1 |

| Variable | Value |
|---|---|
| `API_URL` | the Render URL |
| `FRONTEND_URL` | `https://metravo.pages.dev` |
| `TELEGRAM_BOT_USERNAME` | step 3 |

Push to `main` (or Actions → deploy → Run workflow): the frontend is
published and the Telegram webhook is registered.

## 8. The 15-minute scan schedule

GitHub runs `scan.yml` on its own cron, but delays free scheduled runs by an
hour or more. For a dependable 15 minutes:

1. github.com/settings/personal-access-tokens → fine-grained → this repo only → *Actions: Read and write*.
2. cron-job.org → new job, every 15 min, `POST https://api.github.com/repos/<owner>/metravo/actions/workflows/scan.yml/dispatches`
   - headers: `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`
   - body: `{"ref":"main"}`

Each run scans only the searches that are due under their plan, so extra
triggers cost nothing.

## Checks after deploying

- `https://<api>/api/health` → `{"status":"ok"}`
- Sign in on the site, save a search, connect Telegram, press “Scan now”.
- Buy Pro with Stripe's test card `4242 4242 4242 4242` → plan badge turns PRO.
