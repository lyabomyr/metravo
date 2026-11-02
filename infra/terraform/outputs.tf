output "site_url" {
  description = "Public address of the website — becomes FRONTEND_URL for the API."
  value       = "https://${cloudflare_pages_project.site.subdomain}"
}

output "uptime_worker" {
  description = "The uptime Worker; open its URL to see the last known state."
  value       = cloudflare_workers_script.uptime.script_name
}
