# Запуск у продакшн — покроково

## Спершу головне: хто що створює

**Користувачі нічого не створюють.** Людина вводить імейл → їй автоматично
створюється акаунт і **власна база** (`u-<id>` у Turso). Це вже працює в коді
(`AuthService.sign_in` → `TenantService.ensure`).

Шість акаунтів нижче — **твої, власника сервісу, один раз на весь сервіс**.
Через них сервіс сам створює бази, логінить людей, шле повідомлення і бере
оплату для всіх користувачів.

| Сервіс | Навіщо | Безкоштовно |
|---|---|---|
| Turso | Хостинг баз: твоя база керування + окрема база на кожного користувача | так |
| Firebase | Вхід за імейлом (посилання на пошту) і через Google | так |
| BotFather | Створює Telegram-бота, який шле оголошення | так |
| Stripe | Приймає оплату за Pro | без абонплати, лише % з платежу |
| Render | Хостинг бекенду (API) | так, 750 год/міс |
| Cloudflare Pages | Хостинг сайту (Angular) | так |
| cron-job.org | Будильник: тримає API «теплим» і запускає скан кожні 15 хв | так |

Де що зберігати:
- **Render → Environment** — налаштування API.
- **GitHub → Settings → Secrets and variables → Actions** — для деплою сайту і сканера.
  *Secrets* — приховані значення, *Variables* — публічні адреси.

Нічого з цього не комітиться в репозиторій.

---

## Крок 1. Turso — бази даних (5 хв)

```bash
brew install tursodatabase/tap/turso
turso auth signup                                # логін через GitHub
turso db create metravo-control                  # база керування сервісом
turso db show metravo-control --url              # → CONTROL_DB_URL
turso db tokens create metravo-control           # → CONTROL_DB_TOKEN
turso auth api-tokens mint metravo               # → TURSO_API_TOKEN
turso org list                                   # → TURSO_ORG (твій slug)
```

| Значення | Для чого | Куди |
|---|---|---|
| `CONTROL_DB_URL` | адреса бази керування (юзери, плани, хто де живе) | Render + GitHub **Secret** |
| `CONTROL_DB_TOKEN` | доступ до неї | Render + GitHub **Secret** |
| `TURSO_API_TOKEN` | дозволяє сервісу **створювати бази юзерам** і видавати їм креди | Render + GitHub **Secret** |
| `TURSO_ORG` | у якій організації створювати бази | Render + GitHub **Secret** |

## Крок 2. Firebase — вхід (5 хв)

1. https://console.firebase.google.com → **Add project** → назва `metravo`, Analytics вимкнути.
2. **Build → Authentication → Get started → Sign-in method**:
   увімкнути **Email/Password → Email link (passwordless sign-in)** і **Google**.
3. **Project settings (шестерня) → General → Your apps → `</>` (Web)** → назва `metravo-web` → скопіювати об'єкт `firebaseConfig`.

| Значення | Для чого | Куди |
|---|---|---|
| `FIREBASE_PROJECT_ID` | бекенд перевіряє, що токен входу виданий саме твоїм проєктом | Render |
| `FIREBASE_WEB_CONFIG` | весь `firebaseConfig` одним рядком JSON — сайт показує форму входу | Render |

`FIREBASE_WEB_CONFIG` публічний за задумом Firebase, це не секрет.

## Крок 3. Telegram-бот (2 хв)

1. У Telegram відкрити **@BotFather** → `/newbot` → ім'я `Metravo` → username, наприклад `metravo_pl_bot`.
2. Він дасть токен виду `123456:ABC...`.
3. Придумати довгий випадковий рядок для вебхука: `openssl rand -hex 32`.

| Значення | Для чого | Куди |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | бот шле повідомлення | Render + GitHub **Secret** |
| `TELEGRAM_BOT_USERNAME` | будує посилання `t.me/<bot>?start=…` (2 кліки) | Render + GitHub **Variable** |
| `TELEGRAM_WEBHOOK_SECRET` | Telegram підписує ним кожен виклик, чужі запити відкидаються | Render + GitHub **Secret** |

## Крок 4. Stripe — оплата, частина 1 (5 хв)

1. https://dashboard.stripe.com/register. Залишайся в **Test mode** (перемикач угорі), поки не захочеш брати справжні гроші.
2. **Product catalog → Add product** → `Metravo Pro`, **Recurring**, `19 PLN` / month → зберегти → скопіювати **Price ID** (`price_...`).
3. **Developers → API keys** → **Secret key** (`sk_test_...`).
4. **Settings → Billing → Customer portal** → дозволити скасування підписки.
5. *(опційно)* **Settings → Payment methods** → увімкнути BLIK, Przelewy24.

| Значення | Для чого | Куди |
|---|---|---|
| `STRIPE_SECRET_KEY` | створює сторінку оплати і портал керування підпискою | Render |
| `STRIPE_PRICE_PRO` | яку ціну продавати | Render |

## Крок 5. Render — бекенд (5 хв)

1. https://render.com → логін через GitHub.
2. **New → Blueprint** → обрати репозиторій `metravo` → Render прочитає `render.yaml`.
3. Він попросить значення з кроків 1–4, а ще:

| Значення | Що вписати |
|---|---|
| `ADMIN_EMAILS` | твій імейл — тобі відкриється сторінка Admin |
| `FRONTEND_URL` | `https://metravo.pages.dev` (з кроку 7) |
| `CORS_ORIGINS` | те саме, що `FRONTEND_URL` |
| `PUBLIC_API_URL` | адреса, яку дасть Render, напр. `https://metravo-api.onrender.com` |
| `CRON_SECRET` | `openssl rand -hex 32` |
| `STRIPE_WEBHOOK_SECRET` | поки `pending`, заміниш після кроку 6 |

`JWT_SECRET` Render згенерує сам.

4. **Apply** → дочекатися деплою → відкрити `https://<api>/api/health` → має бути `{"status":"ok"}`.

## Крок 6. Stripe — оплата, частина 2 (2 хв)

**Developers → Webhooks → Add endpoint**:
- URL: `https://<api>/api/billing/webhook`
- Events: `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`

Скопіювати **Signing secret** (`whsec_...`) → у Render замінити `STRIPE_WEBHOOK_SECRET` → **Save** (Render перезапуститься).
Так бекенд перевіряє, що оплата справді прийшла від Stripe.

## Крок 7. Cloudflare Pages — сайт (5 хв)

1. https://dash.cloudflare.com → **Workers & Pages → Create → Pages → Upload assets** → назва проєкту **`metravo`** → завантажити будь-який порожній файл (наступні деплої робитиме GitHub).
2. **My Profile → API Tokens → Create Token** → шаблон **Edit Cloudflare Workers** → Create.
3. **Account ID** — на головній сторінці акаунта, праворуч.

| Значення | Для чого | Куди |
|---|---|---|
| `CLOUDFLARE_API_TOKEN` | GitHub викладає новий сайт після кожного пушу | GitHub **Secret** |
| `CLOUDFLARE_ACCOUNT_ID` | у який акаунт викладати | GitHub **Secret** |

4. Повернутися у **Firebase → Authentication → Settings → Authorized domains** → додати `metravo.pages.dev`.

## Крок 8. GitHub — секрети (5 хв)

Репозиторій → **Settings → Secrets and variables → Actions**.

**Secrets:**
`CONTROL_DB_URL`, `CONTROL_DB_TOKEN`, `TURSO_API_TOKEN`, `TURSO_ORG`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_SECRET`,
`CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`

**Variables:**

| Назва | Значення |
|---|---|
| `API_URL` | `https://<api>.onrender.com` |
| `FRONTEND_URL` | `https://metravo.pages.dev` |
| `TELEGRAM_BOT_USERNAME` | username бота |

Далі **Actions → deploy → Run workflow**: сайт викладеться, бот отримає адресу вебхука.

## Крок 9. cron-job.org — розклад (5 хв)

Безкоштовний Render засинає без запитів, а сам GitHub запускає розклад раз на 1–2 год.
Обидві проблеми закриває cron-job.org.

1. https://cron-job.org → реєстрація.
2. **Job 1 — «не спати»:** `GET https://<api>/api/health`, кожні 10 хв.
3. GitHub → **Settings (профілю) → Developer settings → Fine-grained tokens** → лише репозиторій `metravo` → **Actions: Read and write** → токен.
4. **Job 2 — «скан»:** кожні 15 хв, `POST https://api.github.com/repos/lyabomyr/metravo/actions/workflows/scan.yml/dispatches`
   - headers: `Authorization: Bearer <токен з п.3>`, `Accept: application/vnd.github+json`
   - body: `{"ref":"main"}`

## Перевірка

1. Відкрити `https://metravo.pages.dev` → увійти своїм імейлом (лист прийде від Firebase).
2. Онбординг → зберегти пошук → **Open Telegram** → **Start**.
3. **Listings → Scan now** → оголошення на сайті і в Telegram.
4. **Plan → Upgrade** → тестова картка `4242 4242 4242 4242`, будь-яка дата в майбутньому, будь-який CVC → бейдж стає **PRO**.
5. **My data → Read-only credentials** → URL і токен **твоєї власної** Turso-бази.

Коли все працює — у Stripe вимкнути Test mode, повторити крок 4 (п.2–3) і крок 6 для live-ключів і оновити їх у Render.
