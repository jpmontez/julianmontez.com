variable "account_id" {
  description = "Cloudflare account ID. Set via TF_VAR_account_id (it is an identifier, not a secret)."
  type        = string
}

variable "zone_name" {
  description = "Apex domain of the site, e.g. example.com. CI sets it from the SITE_DOMAIN repository variable via TF_VAR_zone_name."
  type        = string
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
