output "zone_id" {
  description = "Zone ID. Export as CLOUDFLARE_ZONE_ID for `cf` commands."
  value       = cloudflare_zone.this.id
}

output "name_servers" {
  description = "Cloudflare nameservers to set at your registrar."
  value       = cloudflare_zone.this.name_servers
}
