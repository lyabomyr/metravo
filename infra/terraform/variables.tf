variable "state_passphrase" {
  description = "Encrypts the state file. GitHub Secret TF_STATE_PASSPHRASE (openssl rand -hex 32)."
  type        = string
  sensitive   = true
}

variable "cloudflare_account_id" {
  description = "GitHub Secret CLOUDFLARE_ACCOUNT_ID."
  type        = string
}

variable "site_name" {
  description = "Cloudflare Pages project name; the site is served at <name>.pages.dev."
  type        = string
  default     = "metravo"
}

variable "api_url" {
  description = "Public address of the API, watched by the uptime Worker."
  type        = string
}

variable "admin_emails" {
  description = "Comma-separated; their linked Telegram chats get the alerts. GitHub Variable ADMIN_EMAILS."
  type        = string
  default     = ""
}

variable "telegram_bot_token" {
  description = "GitHub Secret TELEGRAM_BOT_TOKEN — the uptime Worker sends alerts with it."
  type        = string
  sensitive   = true
}

variable "control_db_url" {
  description = "GitHub Secret CONTROL_DB_URL — the Worker reads the admins' chat ids from it."
  type        = string
  sensitive   = true
}

variable "control_db_token" {
  description = "GitHub Secret CONTROL_DB_TOKEN."
  type        = string
  sensitive   = true
}
