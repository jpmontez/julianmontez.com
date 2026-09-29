variable "account_id" {
  description = "Cloudflare account ID. Set via TF_VAR_account_id (it is an identifier, not a secret)."
  type        = string

  validation {
    condition     = can(regex("^[0-9a-f]{32}$", var.account_id))
    error_message = "account_id must be a 32-character hex Cloudflare account ID."
  }
}

variable "zone_name" {
  description = "Apex domain of the site, e.g. example.com. CI sets it from the SITE_DOMAIN repository variable via TF_VAR_zone_name."
  type        = string

  validation {
    condition     = can(regex("^([a-z0-9-]+\\.)+[a-z]{2,}$", var.zone_name))
    error_message = "zone_name must be a lowercase apex domain such as example.com."
  }
}

variable "dns_records" {
  description = <<-EOT
    DNS records to manage, keyed by a stable label of your choice. `name` is relative
    to the zone ("@" for the apex). Do not list the apex record for the site itself:
    the Worker custom domain (owned by Wrangler, `npm run deploy`) creates it.
  EOT
  type = map(object({
    type     = string
    name     = string
    content  = string
    ttl      = optional(number, 1) # 1 = automatic
    proxied  = optional(bool, false)
    priority = optional(number)
    comment  = optional(string)
  }))
  default = {}

  validation {
    condition     = alltrue([for r in values(var.dns_records) : contains(["A", "AAAA", "CAA", "CNAME", "MX", "NS", "SRV", "TXT"], r.type)])
    error_message = "dns_records[*].type must be one of A, AAAA, CAA, CNAME, MX, NS, SRV, TXT."
  }

  validation {
    condition     = alltrue([for r in values(var.dns_records) : r.type != "MX" || r.priority != null])
    error_message = "MX records need a priority."
  }
}

variable "zone_settings" {
  description = <<-EOT
    Zone settings to pin, as { setting_id = value }, e.g. { ssl = "strict", min_tls_version = "1.2" }.
    List only settings that differ from Cloudflare's defaults. Setting IDs:
    https://developers.cloudflare.com/api/resources/zones/subresources/settings/
  EOT
  type        = any
  default     = {}
}

variable "redirect_www_to_apex" {
  description = "Create a proxied placeholder `www` record and a zone redirect rule sending www.<zone> to the apex with a 301, keeping path and query string."
  type        = bool
  default     = true
}

variable "web_analytics" {
  description = "Enable Cloudflare Web Analytics with automatic beacon injection for the zone."
  type        = bool
  default     = true
}

variable "web_analytics_exclude_eu" {
  description = "Web Analytics \"lite\" mode: don't collect data from EU visitors."
  type        = bool
  default     = false
}

variable "adopt" {
  description = <<-EOT
    IDs of existing resources to import instead of creating. Leave empty ({}) for a fresh
    setup. When `zone_id` is set, every entry in `zone_settings` is imported too.
    Get the IDs with cf-terraforming or `cf` (see infra/README.md).
  EOT
  type = object({
    zone_id               = optional(string)
    dns_records           = optional(map(string), {}) # dns_records key => record ID
    www_record_id         = optional(string)
    redirect_ruleset_id   = optional(string)
    web_analytics_site_id = optional(string)
    waf_custom_ruleset_id = optional(string)
  })
  default = {}
}

variable "state_passphrase" {
  description = "Passphrase that encrypts state and plan files (min. 16 characters). Set via TF_VAR_state_passphrase; keep it in a password manager."
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.state_passphrase) >= 16
    error_message = "state_passphrase must be at least 16 characters."
  }
}

variable "waf_custom_rules" {
  description = <<-EOT
    WAF custom rules, evaluated in list order. Free plan: at most 5 rules.
    `skip_remaining_custom_rules` (ruleset "current"), `skip_phases`, `skip_products` and
    `logging` apply only when `action = "skip"`.
  EOT
  type = list(object({
    description                 = string
    expression                  = string
    action                      = string
    enabled                     = optional(bool, true)
    logging                     = optional(bool, true)
    skip_remaining_custom_rules = optional(bool, false)
    skip_phases                 = optional(list(string))
    skip_products               = optional(list(string))
  }))
  default = []

  validation {
    condition     = length(var.waf_custom_rules) <= 5
    error_message = "The Free plan allows at most 5 WAF custom rules."
  }

  validation {
    condition     = alltrue([for r in var.waf_custom_rules : contains(["block", "challenge", "js_challenge", "managed_challenge", "log", "skip"], r.action)])
    error_message = "waf_custom_rules[*].action must be block, challenge, js_challenge, managed_challenge, log or skip."
  }
}

variable "bot_fight_mode" {
  description = <<-EOT
    Bot Fight Mode (Security → Settings). It cannot be skipped by WAF custom rules, so leave it
    off when custom rules exempt feeds and verified bots. Other bot settings are left as-is.
  EOT
  type        = bool
  default     = false
}

variable "bot_settings" {
  description = <<-EOT
    Other bot settings to pin; null leaves a setting unmanaged. Values:
    ai_bots_protection "block" | "disabled" | "only_on_ad_pages" (Block AI bots);
    crawler_protection "enabled" | "disabled" (AI Labyrinth);
    ai_training: robots.txt policy for AI training crawlers (e.g. "disallow");
    enable_js: invisible JavaScript detections.
  EOT
  type = object({
    ai_bots_protection = optional(string)
    crawler_protection = optional(string)
    ai_training        = optional(string)
    enable_js          = optional(bool)
  })
  default = {}
}
