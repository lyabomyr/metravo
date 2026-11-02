# Uptime watcher: a Worker that checks the API and the website every 5 minutes
# and alerts the admins in Telegram. Free: cron triggers and KV are part of
# the Workers free plan. The code is in ../worker/uptime.js.

resource "cloudflare_workers_kv_namespace" "uptime" {
  account_id = var.cloudflare_account_id
  title      = "metravo-uptime"
}

resource "cloudflare_workers_script" "uptime" {
  account_id         = var.cloudflare_account_id
  script_name        = "metravo-uptime"
  content            = file("${path.module}/../worker/uptime.js")
  main_module        = "uptime.js"
  compatibility_date = "2026-10-01"

  bindings = [
    { name = "STATE", type = "kv_namespace", namespace_id = cloudflare_workers_kv_namespace.uptime.id },
    { name = "API_URL", type = "plain_text", text = var.api_url },
    { name = "SITE_URL", type = "plain_text", text = "https://${cloudflare_pages_project.site.subdomain}" },
    { name = "ADMIN_EMAILS", type = "plain_text", text = var.admin_emails },
    { name = "TELEGRAM_BOT_TOKEN", type = "secret_text", text = var.telegram_bot_token },
    { name = "CONTROL_DB_URL", type = "secret_text", text = var.control_db_url },
    { name = "CONTROL_DB_TOKEN", type = "secret_text", text = var.control_db_token },
  ]
}

resource "cloudflare_workers_cron_trigger" "uptime" {
  account_id  = var.cloudflare_account_id
  script_name = cloudflare_workers_script.uptime.script_name
  schedules   = [{ cron = "*/5 * * * *" }]
}
