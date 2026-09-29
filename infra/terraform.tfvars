# Site data for julianmontez.com. This is the only infra file with personal values.
# zone_name, account_id and state_passphrase come from TF_VAR_* environment variables.

# The apex CNAME to julianmontez-com.pages.dev is deliberately absent: at cutover
# the Worker custom domain (owned by Wrangler, `npm run deploy`) replaces it.
dns_records = {
  # Fastmail DKIM
  dkim_fm1 = { type = "CNAME", name = "fm1._domainkey", content = "fm1.julianmontez.com.dkim.fmhosted.com" }
  dkim_fm2 = { type = "CNAME", name = "fm2._domainkey", content = "fm2.julianmontez.com.dkim.fmhosted.com" }
  dkim_fm3 = { type = "CNAME", name = "fm3._domainkey", content = "fm3.julianmontez.com.dkim.fmhosted.com" }

  # Fastmail inbound mail
  mx_1 = { type = "MX", name = "@", content = "in1-smtp.messagingengine.com", priority = 10 }
  mx_2 = { type = "MX", name = "@", content = "in2-smtp.messagingengine.com", priority = 20 }

  # Content exactly as stored by Cloudflare: SPF unquoted, the verification tokens quoted.
  spf                      = { type = "TXT", name = "@", content = "v=spf1 include:spf.messagingengine.com ?all" }
  github_pages_proof       = { type = "TXT", name = "_github-pages-challenge-jpmontez", content = "\"1fe32baa3d5d88c404da972571154b\"" }
  google_site_verification = { type = "TXT", name = "@", content = "\"google-site-verification=mfH-SpFw8H8tD2xdL--42buMEWw6AUY0asHqDXW1D10\"", ttl = 3600 }
}

# Settings changed from Cloudflare's defaults (the API reports a modified_on date for these).
zone_settings = {
  always_use_https = "on"
  challenge_ttl    = 3600
  ipv6             = "on"
  rocket_loader    = "off"
  ssl              = "flexible" # TODO: move to "strict" (Full (strict)) at cutover; see TODO.md
}

redirect_www_to_apex     = true
web_analytics            = true
web_analytics_exclude_eu = true

# WAF custom rules (Security → Security rules), evaluated in order.
# Rationale: infra/README.md › WAF custom rules.
waf_custom_rules = [
  {
    description = "Block SEO and foreign-search crawlers"
    action      = "block"
    expression  = "(lower(http.user_agent) contains \"ahrefs\") or (lower(http.user_agent) contains \"semrush\") or (lower(http.user_agent) contains \"mj12bot\") or (lower(http.user_agent) contains \"yandex\") or (lower(http.user_agent) contains \"baidu\") or (lower(http.user_agent) contains \"sogou\")"
  },
  {
    # Verified bots, feeds, sitemaps, hashed assets and link previews can't solve a challenge.
    description                 = "Allow verified bots, feeds and link previews"
    action                      = "skip"
    skip_remaining_custom_rules = true
    skip_phases                 = ["http_ratelimit", "http_request_firewall_managed"]
    skip_products               = ["bic"]
    expression                  = "(cf.client.bot) or (http.request.uri.path in {\"/feed.xml\" \"/rss.xml\" \"/robots.txt\" \"/sitemap-index.xml\" \"/sitemap-0.xml\" \"/favicon.png\"}) or (starts_with(http.request.uri.path, \"/_astro/\")) or (http.user_agent contains \"facebookexternalhit\") or (http.user_agent contains \"Mastodon/\")"
  },
  {
    # Pure hosting/datacenter and proxy-seller networks (Hetzner, OVH, DigitalOcean, Vultr, Linode,
    # Contabo, GoDaddy, IONOS, ColoCrossing, Rayobyte, ...). Comes before the challenge rules,
    # because a challenge ends evaluation. See infra/README.md for the full classification.
    description = "Block hosting networks"
    action      = "block"
    expression  = "(ip.src.asnum in {6724 7393 8560 11878 12876 14061 16125 16276 18450 19437 20454 20473 20738 23033 23470 24940 25264 26347 26496 27176 30083 32244 32475 36352 36943 39020 46606 50673 51167 51540 53667 55293 61317 63018 63023 63949 197540 198571 199610 200373 201924 206575 208046 210558 210920 211252 212047 213230 264649 397630 398101 398493})"
  },
  {
    description = "Challenge automation user agents"
    action      = "managed_challenge"
    expression  = "(lower(http.user_agent) contains \"bot\") or (lower(http.user_agent) contains \"crawl\") or (lower(http.user_agent) contains \"spider\") or (lower(http.user_agent) contains \"scrap\") or (lower(http.user_agent) contains \"python-\") or (lower(http.user_agent) contains \"go-http-client\") or (lower(http.user_agent) contains \"headless\") or (http.user_agent eq \"\")"
  },
  {
    # Hyperscale clouds and VPN-exit hosts, where real people browse: AWS, Google Cloud, Microsoft,
    # Oracle, Alibaba, Tencent, Huawei, Leaseweb, M247, Datacamp/CDN77, Clouvider, HostRoyale,
    # F.N.S. Holdings, xTom, Performive, Nexeon, Yandex and Zoho corporate egress; and Tor (T1,
    # plus the Emerald Onion exit operator).
    description = "Challenge cloud, VPN and Tor networks"
    action      = "managed_challenge"
    expression  = "(ip.src.asnum in {2639 3214 7203 7224 8075 9009 13238 14618 16509 27411 30633 31898 37963 45102 46562 60068 60781 62240 131199 132203 136907 205544 206074 206092 206150 206164 207990 212238 395954 396507 396982}) or (ip.src.country eq \"T1\")"
  },
]

# Off: WAF custom rules can't skip it, and it would challenge feed readers on cloud hosts.
bot_fight_mode = false

# Block AI bots, AI Labyrinth on, disallow AI training, JS detections on.
bot_settings = {
  ai_bots_protection = "block"
  crawler_protection = "enabled"
  ai_training        = "disallow"
  enable_js          = true
}

# Existing resources to import (IDs from cf-terraforming / the Cloudflare API).
adopt = {
  zone_id = "5b0415cdb7b927055198abe37d3b1afe"
  dns_records = {
    dkim_fm1                 = "bd15a094e9d04f83555f1f70b718428b"
    dkim_fm2                 = "256fce2e1cb76a059a50682eef190356"
    dkim_fm3                 = "7b007e7895db9fb79bfe389f7405cf5f"
    mx_1                     = "91ae9655d3d3a1e870936e410d286623"
    mx_2                     = "5fc055ed033ef7621ce49e307ba28d79"
    spf                      = "8d888166f384f8b419b9126d0db263ce"
    github_pages_proof       = "58f7b9c592eaf919ee819660b91335ec"
    google_site_verification = "c7642221f4f207b0e419b596782f517e"
  }
  www_record_id         = "9c0782ed9eb083537ee94fc9e8794397"
  redirect_ruleset_id   = "af6bc3d7ab784ab89b36bac845d30362"
  web_analytics_site_id = "1101079dbc614be09716f65f2664ad1c"
  waf_custom_ruleset_id = "8deac5f1a1124836baa336cbc88a6621"
}
