output "site_url" {
  description = "Public address of the website — becomes FRONTEND_URL for the API."
  value       = "https://${cloudflare_pages_project.site.subdomain}"
}
