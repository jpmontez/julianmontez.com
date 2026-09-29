resource "cloudflare_dns_record" "this" {
  for_each = var.dns_records

  zone_id  = cloudflare_zone.this.id
  type     = each.value.type
  name     = each.value.name == "@" ? var.zone_name : "${each.value.name}.${var.zone_name}"
  content  = each.value.content
  ttl      = each.value.ttl
  proxied  = each.value.proxied
  priority = each.value.priority
  comment  = each.value.comment
}
