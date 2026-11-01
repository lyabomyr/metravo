import { defineConfig } from 'cypress';

/**
 * End-to-end tests drive the real frontend against the real backend.
 * The backend runs with APP_ENV=e2e: dev sign-in, fake payments, saved
 * portal pages and an in-memory Telegram — so no external account is needed.
 */
export default defineConfig({
  e2e: {
    baseUrl: process.env.WEB_URL ?? 'http://localhost:4200',
    env: {
      apiUrl: process.env.API_URL ?? 'http://localhost:8000',
      telegramSecret: process.env.TELEGRAM_WEBHOOK_SECRET ?? 'dev-webhook-secret',
      adminEmail: 'admin@metravo.test',
    },
    video: false,
    viewportWidth: 1280,
    viewportHeight: 900,
  },
});
