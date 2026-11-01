# The website. Files are uploaded by the deploy workflow (wrangler); this only
# declares that the project exists and which branch is production.
resource "cloudflare_pages_project" "site" {
  account_id        = var.cloudflare_account_id
  name              = var.site_name
  production_branch = "main"
}

# The project was first created by the deploy workflow, before Terraform
# managed it. Adopt it instead of failing on "already exists".
import {
  to = cloudflare_pages_project.site
  id = "${var.cloudflare_account_id}/${var.site_name}"
}
