resource "cloudflare_web_analytics_site" "this" {
  count = var.web_analytics ? 1 : 0

  account_id   = var.account_id
  zone_tag     = cloudflare_zone.this.id
  auto_install = true
  lite         = var.web_analytics_exclude_eu

  lifecycle {
    # The API reports `lite` only under `ruleset.lite`, so the provider (v5.26) reads it
    # back as null and would show a permanent diff. It is still applied on create.
    ignore_changes = [lite]
  }
}
