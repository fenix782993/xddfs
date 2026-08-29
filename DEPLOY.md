# 🚀 DEPLOY ULTRA
1. Create GitHub repository and upload this project.
2. Render → New Blueprint → select repository.
3. Render reads render.yaml and creates PostgreSQL.
4. Set BOT_TOKEN, ADMIN_IDS, ADMIN_CHANNEL_ID, BOT_USERNAME, WEBAPP_URL.
5. Add bot as admin in the mission channel.
6. Mission format:
`/mission add | Подписка на канал | 500 | subscribe | @channel`
7. Admin:
`/admin`, `/give ID AMOUNT`, `/take ID AMOUNT`, `/ban ID`
8. PvP:
`/duel USER_ID`, `/accept MATCH_ID`
9. Configure Telegram Mini App URL to the Render HTTPS URL.

Before a public launch, add Telegram WebApp initData signature validation, rate limiting, migrations, audit logs, monitoring, automated tests and stricter anti-abuse controls.
