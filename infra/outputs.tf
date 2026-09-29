output "zone_id" {
  description = "Zone ID. Export as CLOUDFLARE_ZONE_ID for `cf` commands."
  value       = cloudflare_zone.this.id
}

output "name_servers" {
  description = "Cloudflare nameservers to set at your registrar."
  value       = cloudflare_zone.this.name_servers
}

output "web_analytics_site_tag" {
  description = "Web Analytics site tag, or null when disabled."
  value       = one(cloudflare_web_analytics_site.this[*].site_tag)
}
