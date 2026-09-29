# Zone entry point for WAF custom rules (Security → Security rules → Custom rules).
# A zone has one ruleset per phase; every custom rule lives in this resource, in order.
resource "cloudflare_ruleset" "waf_custom" {
  count = length(var.waf_custom_rules) > 0 ? 1 : 0

  zone_id = cloudflare_zone.this.id
  name    = "default"
  kind    = "zone"
  phase   = "http_request_firewall_custom"

  rules = [for r in var.waf_custom_rules : {
    description = r.description
    expression  = r.expression
    action      = r.action
    enabled     = r.enabled
    logging     = r.action == "skip" ? { enabled = r.logging } : null
    action_parameters = r.action == "skip" ? {
      ruleset  = r.skip_remaining_custom_rules ? "current" : null
      phases   = r.skip_phases
      products = r.skip_products
    } : null
  }]
}
