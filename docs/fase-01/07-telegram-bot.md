# 07 — Telegram Bot

## Propósito

Interface principal de operação do sistema, acessível de qualquer lugar via app do Telegram. Substitui um admin web na Fase 1.

## Setup

1. Criar bot via @BotFather → obter `BOT_TOKEN`
2. Iniciar conversa com o bot → obter `CHAT_ID` (via `https://api.telegram.org/bot{TOKEN}/getUpdates`)
3. Configurar `.env` com ambos
4. Bot só responde ao `CHAT_ID` autorizado (whitelist single-user)

## Stack

- `python-telegram-bot` v21+ (async)
- Roda como `systemd --user` service no notebook
- Long polling (não webhook — não precisa expor porta)

## Comandos

| Comando | Argumentos | Resposta |
|---|---|---|
| `/start` | — | Apresentação curta + lista de comandos |
| `/help` | — | Mesma coisa que `/start` |
| `/status` | — | Resumo: quantidade de indicadores ativos, último deploy, erros nas últimas 24h |
| `/indicadores` | — | Lista todos os indicadores com código, frequência, última coleta |
| `/coletar <code>` | code do indicador ou `all` | Roda coleta imediata, responde com resultado |
| `/publicar` | — | Roda build + deploy imediato |
| `/logs` | `[n]` (opcional, default 10) | Últimas n entradas do log de coleta |
| `/erros` | — | Erros das últimas 24h |
| `/cancelar` | — | Para qualquer operação em andamento |

## Notificações automáticas (push do bot pro usuário)

| Evento | Mensagem |
|---|---|
| Coleta com sucesso e dados novos | ✅ Resumo do que foi coletado |
| Coleta com erro | ❌ Indicador, erro, hora |
| Build/deploy com sucesso | 🚀 URL do site + indicadores atualizados |
| Build/deploy com erro | ❌ Erro detalhado |
| Indicador atrasado | ⚠️ Avisar se passou X dias além do `expected_release_day` sem dado novo |

## Templates de resposta

### `/status`

```
📊 Indicadores Econômicos Hoje

Indicadores ativos: 3
Último deploy: 2026-04-28 07:15 (com 2 atualizações)
Próxima coleta: amanhã 07:00

Erros nas últimas 24h: 0
```

### `/indicadores`

```
📋 Indicadores ativos

🏛 IPCA (mensal)
   Última coleta: 28/04 07:15 ✅
   Último valor: 0,56% (mar/2026)

💰 CDI (mensal)
   Última coleta: 28/04 07:15 ✅
   Último valor: 0,93% (mar/2026)

🏠 TR (mensal)
   Última coleta: 28/04 07:15 ✅
   Último valor: 0,17% (mar/2026)
```

### `/coletar IPCA`

```
🔄 Coletando IPCA...

✅ Concluído
   1 valor novo: 0,56% (mar/2026)
   Recalculou agregações.
   Pronto para publicar com /publicar.
```

### Notificação de erro

```
❌ ERRO na coleta

Indicador: IPCA
Hora: 28/04 07:15
Erro: HTTP 503 ao buscar série 433 do BCB

Tente novamente em alguns minutos com /coletar IPCA
```

## Estrutura do código

```
pipeline/bot/
├── __init__.py
├── handlers.py           # async handlers para cada comando
├── notifications.py      # funções send_*
├── formatters.py         # templates de mensagem
└── auth.py               # decorator @authorized_only
```

### Decorator de autorização

```python
def authorized_only(func):
    @functools.wraps(func)
    async def wrapper(update, context):
        if update.effective_chat.id != int(config.TELEGRAM_CHAT_ID):
            await update.message.reply_text("⛔ Não autorizado.")
            return
        return await func(update, context)
    return wrapper
```

Todo handler usa esse decorator.

### Notificações disparadas pelo pipeline

O pipeline não importa o módulo do bot diretamente. Em vez disso:

- Pipeline grava notificações pendentes em uma tabela `notifications` ou usa um arquivo de queue (`pipeline/queue/notifications.jsonl`)
- Bot tem uma `JobQueue` task que verifica a queue a cada 30s e envia

Alternativa simples: pipeline manda direto via `httpx.post` para a Bot API. Mais acoplado, mas elimina a queue. Decisão: **mandar direto**, é simples o suficiente.

```python
# pipeline/bot/notifications.py
def send_message(text: str):
    httpx.post(
        f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": config.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=10,
    )
```

## systemd service

```ini
# ~/.config/systemd/user/indicadores-bot.service
[Unit]
Description=Indicadores Econômicos Hoje - Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=%h/indicadoreseconomicos
ExecStart=%h/indicadoreseconomicos/.venv/bin/python -m pipeline.bot
Restart=on-failure
RestartSec=10

[Install]
WantedBy=default.target
```

Habilita com:
```bash
systemctl --user enable indicadores-bot
systemctl --user start indicadores-bot
loginctl enable-linger $USER  # mantém ativo mesmo sem login interativo
```

## Limites de mensagens

- Telegram: 4096 chars por mensagem
- Se a resposta for maior, dividir em chunks
- Logs longos: enviar como arquivo de texto (`send_document`)
