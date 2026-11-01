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
