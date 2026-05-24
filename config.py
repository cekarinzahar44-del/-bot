import os

# ─── Все переменные задаются в панели BotHost ──────────────
# Settings → Environment Variables

BOT_TOKEN = os.environ["BOT_TOKEN"]

# ID администраторов через запятую: 123456789,987654321
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "0").split(",")))

# Контакт поддержки
SUPPORT_USERNAME = os.environ.get("SUPPORT_USERNAME", "@support")
