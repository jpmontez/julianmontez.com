# Adopts existing resources listed in var.adopt; with adopt = {} (a fresh setup)
# none of these blocks do anything. Import blocks stay in place after adoption so
# a lost state can be rebuilt with a single `tofu apply`.

import {
  for_each = var.adopt.zone_id == null ? toset([]) : toset([var.adopt.zone_id])
  to       = cloudflare_zone.this
  id       = each.value
}

import {
  for_each = var.adopt.dns_records
  to       = cloudflare_dns_record.this[each.key]
  id       = "${var.adopt.zone_id}/${each.value}"
}

import {
  for_each = var.adopt.zone_id == null ? {} : var.zone_settings
  to       = cloudflare_zone_setting.this[each.key]
  id       = "${var.adopt.zone_id}/${each.key}"
}

import {
  for_each = var.adopt.www_record_id == null ? toset([]) : toset([var.adopt.www_record_id])
  to       = cloudflare_dns_record.www[0]
  id       = "${var.adopt.zone_id}/${each.value}"
}

import {
  for_each = var.adopt.redirect_ruleset_id == null ? toset([]) : toset([var.adopt.redirect_ruleset_id])
  to       = cloudflare_ruleset.redirects[0]
  id       = "zones/${var.adopt.zone_id}/${each.value}"
}

import {
  for_each = var.adopt.web_analytics_site_id == null ? toset([]) : toset([var.adopt.web_analytics_site_id])
  to       = cloudflare_web_analytics_site.this[0]
  id       = "${var.account_id}/${each.value}"
}

import {
  for_each = var.adopt.waf_custom_ruleset_id == null ? toset([]) : toset([var.adopt.waf_custom_ruleset_id])
  to       = cloudflare_ruleset.waf_custom[0]
  id       = "zones/${var.adopt.zone_id}/${each.value}"
}

import {
  for_each = var.adopt.zone_id == null ? toset([]) : toset([var.adopt.zone_id])
  to       = cloudflare_bot_management.this
  id       = each.value
}
