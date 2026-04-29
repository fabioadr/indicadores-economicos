#!/usr/bin/env bash
# Instala o bot Telegram como user service do systemd
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SERVICE_DIR="$HOME/.config/systemd/user"
mkdir -p "$SERVICE_DIR"

cat > "$SERVICE_DIR/indicadores-bot.service" <<EOF
[Unit]
Description=Indicadores Econômicos Hoje - Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=$REPO
ExecStart=$REPO/.venv/bin/python -m pipeline.bot
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now indicadores-bot
loginctl enable-linger "$USER" 2>/dev/null || true
echo "✓ Bot rodando como user service."
echo "  Status: systemctl --user status indicadores-bot"
echo "  Logs:   journalctl --user -u indicadores-bot -f"