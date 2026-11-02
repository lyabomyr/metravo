# Infrastructure — OpenTofu

What can be described as code on the free tiers lives here. It is applied by
`.github/workflows/deploy.yml` on every deploy; nobody runs it by hand.

| Piece | Managed by | Why |
|---|---|---|
| Cloudflare Pages project (the website) | **here** — `cloudflare.tf` | |
| Uptime watcher: Worker, 5-minute cron, KV for its state | **here** — `monitoring.tf`, code in `../worker/uptime.js` | |
| API on Render | `render.yaml` (Render Blueprint) | Render's API refuses to create free-tier services, and the Terraform provider cannot update them ([issue #80](https://github.com/render-oss/terraform-provider-render/issues/80)). The Blueprint is Render's own infrastructure-as-code. |
| API settings (secrets) on Render | `.github/scripts/deploy.py` | copied from GitHub Secrets on every deploy |
| Turso control database | created once with the `turso` CLI | no maintained provider; users' databases are created by the app itself |
| Firebase authorised domain | once, by hand | managing it needs Identity Platform, which requires a billing account |
| Telegram webhook | the deploy workflow (`setWebhook`) | no provider |

## State

The state file is encrypted (AES-GCM, key from GitHub Secret
`TF_STATE_PASSPHRASE`) and kept on the orphan branch `infra-state` of this
repository — free, no extra account, and unreadable without the key. It
must be encrypted: it holds the uptime Worker's secret bindings (bot token,
control database token). The
deploy job is serialised (`concurrency: deploy`), so two runs never write it
at once.

## Changing infrastructure

Edit the `.tf` files, open a PR, merge. The next deploy applies it.

To run locally (needs the secrets in your shell):

```bash
export CLOUDFLARE_API_TOKEN=… TF_VAR_cloudflare_account_id=… TF_VAR_state_passphrase=…
../../.github/scripts/tfstate.sh pull
tofu init && tofu plan
```

Never commit `terraform.tfstate` to `main`; `.gitignore` keeps it out.
