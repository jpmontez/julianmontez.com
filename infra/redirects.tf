# www.<zone> only needs to resolve and be proxied so the redirect rule can
# answer; 192.0.2.1 is a reserved documentation address that is never reached.
resource "cloudflare_dns_record" "www" {
  zone_id = cloudflare_zone.this.id
  type    = "A"
  name    = "www.${var.zone_name}"
  content = "192.0.2.1"
  ttl     = 1
  proxied = true
}

# Zone entry point for Single Redirects. A zone has one ruleset per phase, so
# add any other redirect rules for the zone to this resource.
resource "cloudflare_ruleset" "redirects" {
  zone_id = cloudflare_zone.this.id
  name    = "default"
  kind    = "zone"
  phase   = "http_request_dynamic_redirect"

  rules = [{
    description = "Redirect www to apex"
    expression  = "(http.host eq \"www.${var.zone_name}\")"
    action      = "redirect"
    action_parameters = {
      from_value = {
        status_code           = 301
        preserve_query_string = true
        target_url = {
          expression = "concat(\"https://${var.zone_name}\", http.request.uri.path)"
        }
      }
    }
  }]
}
