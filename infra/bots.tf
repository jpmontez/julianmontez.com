# Zone bot settings (Security → Settings, AI Crawl Control). Attributes left null in
# var.bot_settings are not managed and keep their live values.
resource "cloudflare_bot_management" "this" {
  zone_id            = cloudflare_zone.this.id
  fight_mode         = var.bot_fight_mode
  ai_bots_protection = var.bot_settings.ai_bots_protection
  crawler_protection = var.bot_settings.crawler_protection
  ai_training        = var.bot_settings.ai_training
  enable_js          = var.bot_settings.enable_js
}
