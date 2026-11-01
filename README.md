# Metravo

Сервіс, який шукає квартири й будинки (купівля або оренда) на Otodom, OLX,
Morizon і на аукціонах комірників і надсилає нові оголошення в Telegram.
Кожен користувач входить своїм імейлом і отримує **власну базу даних**: може
її завантажити, а на Pro — підключитися до неї напряму.

Усе працює на **безкоштовних тарифах** і без жодної картки. Секрети
зберігаються **лише в GitHub**.

- Сайт: https://metravo.pages.dev
- API: https://metravo-api.onrender.com (`/api/health`, `/docs`)

Зміст:
1. [Як це влаштовано](#1-як-це-влаштовано)
2. [Хто за що відповідає](#2-хто-за-що-відповідає)
3. [Запуск локально](#3-запуск-локально--без-жодних-акаунтів)
4. [Розгортання з нуля, крок за кроком](#4-розгортання-з-нуля-крок-за-кроком)
5. [Що відбувається при кожному пуші](#5-що-відбувається-при-кожному-пуші)
6. [Щоденна робота](#6-щоденна-робота)
7. [Структура репозиторію](#7-структура-репозиторію)
8. [Якщо щось не працює](#8-якщо-щось-не-працює)

---

## 1. Як це влаштовано

```
                 ┌───────────────────────────── GitHub ─────────────────────────────┐
                 │  код · Secrets (єдине місце налаштувань) · Actions: ci → deploy  │
                 └───────┬──────────────────────┬───────────────────────┬───────────┘
          OpenTofu apply │      копіює секрети, │ деплой                │ setWebhook
                         ▼                      ▼                       ▼
 Браузер ──► Cloudflare Pages ──HTTPS──► Render: FastAPI ◄──webhook── Telegram
             (сайт, Angular)            + планувальник сканувань        ▲
                                          │        │        │           │ нові оголошення
                                          │        │        └───────────┘
                         Firebase Auth ◄──┘        ▼
                      (вхід за імейлом)    Turso (libSQL)
                                           ├─ metravo-control — база керування
                                           └─ u-<id> — окрема база кожного користувача
                                                   ▲
                       Otodom · OLX · Morizon · Komornik ── сканер читає сторінки пошуку
```

**Шлях користувача:**
1. Вводить імейл і отримує лист від Firebase. Після входу бекенд створює йому акаунт і **окрему базу** в Turso.
2. Зберігає пошук: купівля чи оренда, квартира чи будинок, місто, бюджет, площа, кімнати, ціна за м², обов'язкові слова, портали, **як часто перевіряти** (за замовчуванням раз на день).
3. Підключає Telegram у **2 кліки**: «Open Telegram» → «Start».
4. API раз на хвилину перевіряє, яким пошукам уже час, сканує портали, відкидає зайве й дублікати і надсилає нове в Telegram.

**Тарифи:**

| | Free | Pro (у продажі з 15.11.2026) |
|---|---|---|
| Ціна | 0 zł | 19 zł/міс |
| Пошуків | 1 | 5 |
| Перевірка | не частіше ніж раз на 6 год | до разу на 15 хв |
| Портали | otodom, olx, morizon | + komornik |
| Сповіщення про зниження ціни | — | так |
| Прямий доступ до своєї бази | — (лише завантаження) | так |

Поки що оплата вимкнена (`BILLING_PROVIDER=none`), і Pro показано як «coming soon».

---

## 2. Хто за що відповідає

| Сервіс | Роль | Безкоштовно | Де описаний |
|---|---|---|---|
| **GitHub** | код, секрети, CI (тести) і деплой | так (публічний репозиторій — без ліміту хвилин) | `.github/workflows/` |
| **Cloudflare Pages** | віддає сайт (зібраний Angular) | так | `infra/terraform/cloudflare.tf` |
| **Render** | запускає API на FastAPI і **планувальник сканувань** у ньому ж | так, 750 год/міс | `render.yaml` |
| **Turso** | база керування + окрема база на кожного користувача | так | створюється CLI, бази користувачів — кодом |
| **Firebase Auth** | вхід за посиланням на пошту і через Google | так | консоль Firebase |
| **Telegram (BotFather)** | бот, що надсилає оголошення | так | вебхук ставить деплой |
| **OpenTofu** | описує інфраструктуру кодом, стан зашифровано | так | `infra/terraform/` |

**Дві бази даних, бо в них різні власники:**
- **База керування** (`metravo-control`) — наша. Тут зберігаються користувачі, тарифи, підписки, Telegram-чати, а також яка база кому належить.
- **База користувача** (`u-<id>`) — його. Тут його пошуки, оголошення й зміни цін. Тому користувачу можна видати креди саме до неї, не відкриваючи нікого іншого.

**Чому Render не в Terraform.** API Render не дозволяє створювати безкоштовні
сервіси, а Terraform-провайдер не вміє їх оновлювати
([issue #80](https://github.com/render-oss/terraform-provider-render/issues/80)).
Тому Render описаний у `render.yaml` — це Infrastructure-as-Code від самого
Render. Повний розподіл — у [infra/terraform/README.md](infra/terraform/README.md).

**Чому сканування всередині API, а не в GitHub cron.** Розклад GitHub на
безкоштовних раннерах запізнюється на години й витрачає хвилини. Тому API
запускає потік `ScanScheduler`. Раз на хвилину він сканує пошуки, яким уже час,
а кожні 10 хв звертається до власного `/api/health`. Без цього безкоштовний
Render засинає після 15 хв тиші.

---

## 3. Запуск локально — без жодних акаунтів

Потрібні Python 3.11+ і Node 24+.

```bash
make install
make api      # термінал 1 → http://localhost:8000/docs
make web      # термінал 2 → http://localhost:4200
```

Увійти можна з будь-яким імейлом, без пароля. Бекенд працює з
підробками замість зовнішніх сервісів:
- збережені сторінки порталів замість живого скрапінгу;
- тестова сторінка оплати;
- лог замість Telegram;
- SQLite-файли в `backend/data/` замість Turso.

`admin@metravo.test` бачить сторінку Admin.

```bash
make lint     # ruff
make test     # pytest (backend/tests/unit) + vitest (frontend)
make e2e      # Cypress — при запущених make api і make web
```

---

## 4. Розгортання з нуля, крок за кроком

Кожен акаунт створюється **один раз**. Кожне значення кладеться в **GitHub →
репозиторій → Settings → Secrets and variables → Actions**. На Render і
Cloudflare руками нічого не вписується.

> **Secret** — приховане значення (токени, ключі). **Variable** — відкрите (імейл адміна).

### Крок 1. Turso — бази даних

```bash
brew install tursodatabase/tap/turso
turso auth signup                           # вхід через GitHub
turso db create metravo-control             # база керування
turso db show metravo-control --url         # → CONTROL_DB_URL
turso db tokens create metravo-control      # → CONTROL_DB_TOKEN
turso auth api-tokens mint metravo          # → TURSO_API_TOKEN
turso org list                              # → TURSO_ORG
```

| Secret | Навіщо |
|---|---|
| `CONTROL_DB_URL` | адреса бази керування |
| `CONTROL_DB_TOKEN` | доступ до неї |
| `TURSO_API_TOKEN` | право **створювати бази користувачам** і видавати їм креди |
| `TURSO_ORG` | в якій організації Turso їх створювати |

### Крок 2. Firebase — вхід

1. https://console.firebase.google.com → **Add project**, назва `metravo`, Analytics вимкнути.
2. **Build → Authentication → Get started → Sign-in method**: увімкнути **Email/Password → Email link (passwordless)** і **Google**.
3. **Project settings → General → Your apps → `</>`** → зареєструвати вебзастосунок → скопіювати блок `firebaseConfig`. Можна разом із `const firebaseConfig = …`, бекенд розуміє обидва формати.
4. **Authentication → Settings → Authorized domains → Add domain** → `metravo.pages.dev`.

| Secret | Навіщо |
|---|---|
| `FIREBASE_PROJECT_ID` | бекенд перевіряє, що вхід підписав саме цей проєкт |
| `FIREBASE_WEB_CONFIG` | сайт показує форму входу. Це не секрет за задумом Firebase, але зберігаємо його разом з рештою |

### Крок 3. Telegram — бот

1. У Telegram написати **@BotFather** → `/newbot` → ім'я та username (наприклад `metravo_pl_bot`) → він дасть токен.
2. Придумати секрет для вебхука: `openssl rand -hex 32`.

| Secret | Навіщо |
|---|---|
| `TELEGRAM_BOT_TOKEN` | бот надсилає повідомлення |
| `TELEGRAM_BOT_USERNAME` | будує посилання `t.me/<bot>?start=<код>` для підключення у 2 кліки |
| `TELEGRAM_WEBHOOK_SECRET` | Telegram додає його до кожного запиту, а чужі запити відкидаються |

### Крок 4. Cloudflare — сайт

1. https://dash.cloudflare.com → реєстрація.
2. **My Profile → API Tokens → Create Token** → шаблон **Edit Cloudflare Workers** → Create.
3. **Account ID** — на головній сторінці акаунта, праворуч.

| Secret | Навіщо |
|---|---|
| `CLOUDFLARE_API_TOKEN` | OpenTofu створює проєкт Pages, а `wrangler` викладає сайт |
| `CLOUDFLARE_ACCOUNT_ID` | у який акаунт |

Проєкт `metravo` руками не створюється. Перший деплой сам створить його через
API Cloudflare з цим токеном, і з'явиться адреса `https://metravo.pages.dev`.

### Крок 5. Ключ стану інфраструктури

```bash
openssl rand -hex 32
```

| Secret | Навіщо |
|---|---|
| `TF_STATE_PASSPHRASE` | OpenTofu шифрує ним файл стану. Стан лежить у гілці `infra-state`, і без ключа його не прочитати |

### Крок 6. Код на GitHub

```bash
git push -u origin main
```

### Крок 7. Render — API

1. https://render.com → **Sign in with GitHub** → дозволити доступ до репозиторію `metravo`.
2. **New → Blueprint** → репозиторій `metravo` → **Apply**. Render створить сервіс `metravo-api` з `render.yaml`. Перший запуск впаде, бо ще немає налаштувань, так і має бути.
3. **Account Settings → API Keys → Create API Key**.

| Secret | Навіщо |
|---|---|
| `RENDER_API_KEY` | деплой передає секрети на Render, запускає деплой і дізнається адресу API |

`JWT_SECRET` (підпис сесій користувачів) Render генерує сам, і він нікуди не передається.

### Крок 8. (Необов'язково) Адмін

**Variables → New** → `ADMIN_EMAILS` = твій імейл. Тоді тобі відкриється сторінка Admin.

### Крок 9. Перший деплой

Будь-який пуш у `main` → **ci** (тести) → після успіху **deploy**. Вручну:
**Actions → deploy → Run workflow**.

### Крок 10. Перевірка

1. https://metravo-api.onrender.com/api/health → `{"status":"ok"}`.
2. https://metravo.pages.dev → увійти своїм імейлом. Лист прийде від Firebase.
3. Зберегти пошук → **Open Telegram** → **Start**.
4. **Listings → Check now** → оголошення з'являться на сайті і в Telegram.
5. **Plan** → Free 0 zł (поточний), Pro — «coming soon».

**Підсумок — усі налаштування:**

| Тип | Назва |
|---|---|
| Secret | `CONTROL_DB_URL`, `CONTROL_DB_TOKEN`, `TURSO_API_TOKEN`, `TURSO_ORG` |
| Secret | `FIREBASE_PROJECT_ID`, `FIREBASE_WEB_CONFIG` |
| Secret | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET` |
| Secret | `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` |
| Secret | `TF_STATE_PASSPHRASE`, `RENDER_API_KEY` |
| Variable (необов'язково) | `ADMIN_EMAILS`; `API_URL` / `FRONTEND_URL` — лише для власних доменів |
| Пізніше, для оплати | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PRO` |

---

## 5. Що відбувається при кожному пуші

```
push → ci.yml
        ├─ backend:  ruff + pytest
        ├─ frontend: vitest + production build
        └─ e2e:      API (з підробками) + сайт → Cypress
     → deploy.yml (лише main і лише після зеленого CI)
        1. OpenTofu  — застосовує infra/terraform → адреса сайту
        2. Render    — копіює секрети з GitHub, запускає деплой API → адреса API
        3. Сайт      — збирає з адресою API, wrangler викладає на Pages
        4. Telegram  — setWebhook на <API>/api/telegram/webhook
```

Код, який не пройшов CI, у продакшн не потрапляє. Тому в `render.yaml` стоїть
`autoDeploy: false`.

---

## 6. Щоденна робота

| Задача | Що зробити |
|---|---|
| Змінити код | гілка → PR → злити в `main`. Деплой спрацює сам |
| Змінити секрет | GitHub Secrets → наступний деплой (або **Run workflow**) |
| Змінити інфраструктуру | редагувати `infra/terraform/*.tf` → злити в `main` |
| Змінити дату запуску Pro | `PRO_AVAILABLE_FROM` у `render.yaml` |
| Увімкнути оплату | три Stripe-секрети в GitHub + `BILLING_PROVIDER: stripe` у `render.yaml` (див. [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)) |
| Додати портал | `backend/app/services/connectors/<portal>/connector.py` (успадкувати `BaseConnector`, заповнити `URL_TEMPLATES`, реалізувати `parse()`) → `CONNECTOR_CLASSES` у `connectors/registry.py` → збережена сторінка в `tests/fixtures/pages/` + тест → дозволити в тарифі (`billing/plans.py`) |
| Подивитися логи API | Render → `metravo-api` → Logs |

---

## 7. Структура репозиторію

```
backend/                  FastAPI — по папці на сервіс у app/services/
  app/core/               конфіг, база, помилки, базові класи, DI-контейнер
  app/services/           auth · users · tenants · searches · listings · connectors
                          scanning · telegram · billing · export · admin · system
  tests/unit/             юніт-тести, повторюють структуру сервісів
  tests/fixtures/pages/   збережені сторінки порталів для тестів і e2e
frontend/                 Angular — app/core (базові класи) + app/features (по одній на сервіс)
e2e/                      Cypress, один сценарій на шлях користувача
infra/terraform/          OpenTofu — інфраструктура кодом
.github/workflows/        ci · deploy
.github/scripts/          deploy.py (секрети → Render) · tfstate.sh (зашифрований стан)
render.yaml               сервіс API на Render
docs/
  ARCHITECTURE.md         архітектура докладно (англ.)
  CODING_STANDARD.md      єдиний стандарт коду — прочитати перед змінами
  DEPLOYMENT.md           розгортання коротко (англ.)
AGENTS.md                 правила для AI-агентів, які працюють з репозиторієм
```

---

## 8. Якщо щось не працює

| Симптом | Причина і що зробити |
|---|---|
| Сайт відкривається, але нічого не вантажиться | API спить або ще деплоїться. Відкрий `/api/health` і зачекай хвилину |
| `/api/config` повертає 500 | Подивись у Render → Logs. Найчастіше причина в зіпсованому `FIREBASE_WEB_CONFIG` |
| Деплой Render падає одразу після старту | Render → Logs → «Invalid configuration: …». Бракує секрету або він неправильний |
| Лист для входу не приходить або посилання не спрацьовує | Firebase → Authorized domains: має бути `metravo.pages.dev` |
| Бот мовчить | Actions → останній deploy → крок «Point the Telegram bot» має показати `Webhook was set` |
| Крок «Infrastructure (OpenTofu)» пропущено | Немає `TF_STATE_PASSPHRASE` або `CLOUDFLARE_API_TOKEN` |
| OLX нічого не знаходить | OLX блокує деякі IP (403). Скан інших порталів від цього не страждає |
| Червоний CI, хоча код не змінювався | Часто це збій GitHub. Run → **Re-run failed jobs** |
