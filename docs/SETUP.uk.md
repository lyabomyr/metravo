# Запуск у продакшн — покроково

## Головне

- **Користувачі нічого не створюють.** Людина вводить імейл, і для неї
  автоматично створюється акаунт і **власна база** (`u-<id>` у Turso).
- **Секрети зберігаються в одному місці — GitHub → Settings → Secrets and variables → Actions.**
  На Render і Cloudflare нічого вручну не вписується. Під час кожного деплою
  `.github/workflows/deploy.yml` сам передає секрети на Render і сам дізнається
  адреси сайту й API. Тому `API_URL` і `FRONTEND_URL` задавати не треба.
- **Сканування працює всередині API**, без GitHub cron і без cron-job.org.
  API раз на хвилину перевіряє, які пошуки вже «на часі», а кожні 10 хвилин пінгує сам себе,
  щоб безкоштовний Render не заснув.
- **Оплата поки що вимкнена.** Усі на Free (0 zł). На сторінці тарифів Pro позначено
  «coming soon — from 15 November». Stripe підключається пізніше, одним рядком (див. кінець).

| Сервіс | Навіщо | Безкоштовно |
|---|---|---|
| Turso | база керування + окрема база на кожного користувача | так |
| Firebase | вхід за посиланням на пошту і через Google | так |
| BotFather | Telegram-бот | так |
| Render | API разом зі скануванням | так, 750 год/міс (вистачає на 24/7) |
| Cloudflare Pages | сайт | так |
| GitHub Actions | тести і деплой при пуші (без розкладу) | так |

---

## Що вже зроблено ✅

У GitHub Secrets уже лежать:

`CONTROL_DB_URL`, `CONTROL_DB_TOKEN`, `TURSO_API_TOKEN`, `TURSO_ORG`,
`FIREBASE_PROJECT_ID`, `FIREBASE_WEB_CONFIG`,
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET`,
`CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN`

| Секрет | Для чого |
|---|---|
| `CONTROL_DB_URL`, `CONTROL_DB_TOKEN` | база керування: користувачі, тарифи, де чия база |
| `TURSO_API_TOKEN`, `TURSO_ORG` | дає сервісу право створювати базу кожному новому користувачу |
| `FIREBASE_PROJECT_ID` | бекенд перевіряє, що вхід підписав саме твій Firebase |
| `FIREBASE_WEB_CONFIG` | сайт показує форму входу (публічний за задумом Firebase) |
| `TELEGRAM_BOT_TOKEN` | бот надсилає повідомлення |
| `TELEGRAM_BOT_USERNAME` | посилання `t.me/<bot>?start=…` для підключення у 2 кліки |
| `TELEGRAM_WEBHOOK_SECRET` | Telegram підписує ним свої запити, чужі відкидаються |
| `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID` | GitHub створює проєкт Pages (якщо його ще немає) і викладає сайт |

## Крок 1. Відправити код на GitHub (1 хв)

```bash
cd /Users/lubomirkacko/metravo && git push -u origin main
```

## Крок 1½. Ключ для стану інфраструктури (1 хв)

Інфраструктура описана кодом у `infra/terraform` (OpenTofu). Свій стан OpenTofu
шифрує і зберігає в гілці `infra-state` цього ж репозиторію. Ключ шифрування лежить лише в GitHub.

```bash
openssl rand -hex 32
```

| Секрет | Куди | Для чого |
|---|---|---|
| `TF_STATE_PASSPHRASE` | GitHub **Secret** | шифрує файл стану інфраструктури; без нього крок «Infrastructure» пропускається |

## Крок 2. Render — один раз (3 хв)

1. https://render.com → **Sign in with GitHub**.
2. **New → Blueprint** → обрати репозиторій `metravo` → **Apply**.
   Render прочитає `render.yaml`. Більше нічого вписувати не треба:
   `JWT_SECRET` Render згенерує сам, і він нікуди не передається.
   Перший запуск впаде, бо ще немає налаштувань. Так і має бути.
3. **Account Settings → API Keys → Create API Key** → скопіювати.

| Секрет | Куди | Для чого |
|---|---|---|
| `RENDER_API_KEY` | GitHub **Secret** | GitHub передає налаштування на Render і запускає деплой |

## Крок 3. (опційно) Адмін

GitHub → **Variables** → `ADMIN_EMAILS` = твій імейл. Тоді тобі відкриється сторінка Admin.

## Крок 4. Деплой

GitHub → **Actions → deploy → Run workflow**. Далі він запускатиметься сам після кожного зеленого CI на `main`.

Що він робить:
1. Застосовує `infra/terraform`: проєкт `metravo` у Cloudflare Pages, звідки бере адресу сайту (`https://metravo.pages.dev`).
2. Передає секрети на Render, разом з адресою сайту, і запускає деплой API. Звідти ж бере адресу API.
3. Збирає сайт з адресою API і викладає його.
4. Вказує Telegram-боту адресу вебхука.

Обидві адреси видно в лозі кроків «Infrastructure (OpenTofu)» і «API on Render».

Render лишається в `render.yaml`, а не в Terraform: API Render не дозволяє створювати
безкоштовні сервіси, а Terraform-провайдер не вміє їх оновлювати. Що і де описано, дивись у `infra/terraform/README.md`.

## Крок 5. Firebase — дозволити домен сайту (1 хв)

Firebase → **Authentication → Settings → Authorized domains → Add domain** →
домен сайту з кроку 4, наприклад `metravo.pages.dev`. Без цього вхід за посиланням не спрацює.

## Перевірка

1. `https://<api>/api/health` → `{"status":"ok"}`.
2. Відкрити сайт → увійти своїм імейлом (лист прийде від Firebase).
3. Зберегти пошук → **Open Telegram** → **Start**.
4. **Listings → Check now** → оголошення з'являться на сайті і в Telegram.
5. **Plan** → Free 0 zł (поточний), Pro 19 zł з позначкою «coming soon» і кнопкою «Available from 15 November».

## Як часто сканувати

Кожен пошук має поле **«Check for new»**: 15 хв, 30 хв, 1 год, 3 год, 6 год, 12 год або щодня.
За замовчуванням стоїть щодня. Free дозволяє не частіше ніж раз на 6 год, Pro — раз на 15 хв.
Дату запуску Pro можна змінити в `render.yaml`, у рядку `PRO_AVAILABLE_FROM`.

## Коли вмикати оплату (пізніше)

1. Stripe → продукт «Metravo Pro», 19 PLN/міс → `STRIPE_PRICE_PRO`; Developers → API keys → `STRIPE_SECRET_KEY`.
2. Webhooks → `https://<api>/api/billing/webhook` (події `checkout.session.completed`,
   `customer.subscription.updated`, `customer.subscription.deleted`) → `STRIPE_WEBHOOK_SECRET`.
3. Усі три покласти в GitHub Secrets. Деплой уже вміє їх передавати.
4. У `render.yaml` змінити `BILLING_PROVIDER` з `none` на `stripe` → пуш.
