# 10 — Setup do Claude Code: MCPs, Skills, Subagents, Scripts

> Análise opinionada sobre o que vale instalar para este projeto especificamente. Princípio: cada ferramenta extra é overhead cognitivo e contextual. Só entra se o ganho for claro.

---

## TL;DR — O setup mínimo recomendado

**MCPs (3):** sqlite, github, context7
**Subagents (2):** bcb-research, docs-fetcher
**Skills (3):** add-indicator, smoke-test-milestone, debug-collection
**Scripts (5):** setup.sh, inspect-db.sh, validate-build.sh, install_cron.sh, install_systemd.sh
**Hooks (2):** PreToolUse para git push, SessionStart para status

Tudo isso em conjunto deve cortar 30–50% dos tokens consumidos durante a implementação e reduzir bastante o ping-pong de tentativa-e-erro.

---

## MCPs

### 🟢 Instalar

#### 1. **SQLite MCP** — essencial

```bash
claude mcp add sqlite -- uvx mcp-server-sqlite --db-path ./data/indicadores.db
```

**Por quê é essencial aqui:**

- Você vai inspecionar o banco constantemente (verificar que migrations rodaram, validar agregações, conferir backfills)
- Sem o MCP, cada inspeção exige escrever Python ou abrir terminal → tokens gastos
- Com o MCP, Claude Code roda `SELECT` direto e analisa o resultado
- Especialmente útil nos Milestones 1, 3, 4 (DB-heavy)

**Economia estimada:** muito alta. Cada validação de schema/dados que seria 50–200 tokens vira ~10.

#### 2. **GitHub MCP** — útil

```bash
claude mcp add github --env GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx -- npx -y @modelcontextprotocol/server-github
```

**Por quê:**

- Permite criar/ler issues, PRs, gerenciar releases
- Útil para registrar bugs descobertos durante implementação como issues
- O Claude Code pode validar que o push deu certo, ler logs do GitHub Actions (caso adicione algum)
- Não essencial, mas baixo overhead de setup

**Economia estimada:** baixa para esse projeto (deploy é por push direto, sem PRs)

**Token a usar:** PAT com escopo `repo` apenas para o repo `indicadoreseconomicoshoje`.

#### 3. **Context7 MCP** — alto valor

```bash
claude mcp add context7 -- npx -y @upstash/context7-mcp
```

**Por quê é importante:**

- Astro, Tailwind, python-telegram-bot e httpx mudam de versão para versão
- Training data do Claude Code pode estar desatualizada (especialmente para Astro 4 → 5)
- Context7 puxa docs versionadas direto da fonte, sob demanda
- Evita aquele ciclo "Claude propõe API antiga → erro → você corrige → Claude propõe outra antiga"

**Economia estimada:** média–alta nos Milestones 6 e 8 (Astro e Bot)

### 🟡 Considerar

#### 4. **Playwright MCP** — só se precisar validar visual

```bash
claude mcp add playwright -- npx -y @playwright/mcp
```

**Por quê pode valer:**

- Tirar screenshots do site durante desenvolvimento
- Validar que mobile não quebra
- Debugar layout sem você precisar abrir o browser

**Por quê pode não valer:**

- Você abre o navegador de qualquer jeito durante dev
- Adiciona dependência pesada (browsers headless) só para conveniência

**Recomendação:** instalar somente no Milestone 6 (site). Remover depois.

### 🔴 Não instalar

| MCP                                  | Por quê não                                                                                                                                      |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Filesystem**                       | Claude Code já tem acesso ao diretório atual. Só ajudaria se precisasse mexer em `~/.config/systemd/` — e isso é uma vez só, melhor fazer manual |
| **Brave Search**                     | Web search já é nativo                                                                                                                           |
| **PostgreSQL**                       | Você não usa Postgres                                                                                                                            |
| **Sentry/DataDog/Slack/Jira/Linear** | Projeto de uma pessoa, sem necessidade                                                                                                           |
| **Sequential Thinking**              | Marketing puro; o Claude Code já raciocina passo a passo no thinking nativo                                                                      |
| **Memory MCP**                       | CLAUDE.md já cobre                                                                                                                               |
| **Vercel MCP**                       | Deploy é por git push. Vercel UI cobre o resto                                                                                                   |
| **Telegram MCP**                     | Você vai testar o bot pelo próprio Telegram. Não há ganho                                                                                        |

### Importante: Tool Search está ligado por padrão

O Claude Code 2026 usa **Tool Search** (lazy loading). Os tools dos MCPs só entram no contexto quando o Claude precisa, então conectar 3 MCPs não inflaciona o contexto. Antes era preocupação real; hoje não é mais.

---

## Subagents

Subagents rodam em contexto isolado e devolvem só o resumo. Use-os para tarefas que poluiriam o contexto principal.

### 🟢 Criar

#### 1. **`bcb-research`** — pesquisa de séries no SGS

`.claude/agents/bcb-research.md`:

```markdown
---
name: bcb-research
description: Pesquisa séries do SGS/BCB. Use quando precisar mapear um indicador novo a um connector_config, ou validar que um series_id está correto e ativo.
tools: WebFetch, WebSearch
---

Você é especialista no Sistema Gerenciador de Séries Temporais (SGS) do Banco Central do Brasil.

Quando recebe o nome de um indicador (ex: "INPC", "IGP-M"):

1. Pesquise no SGS (https://www3.bcb.gov.br/sgspub/localizarseries/localizarSeries.do) se a série existe
2. Identifique o código numérico (`series_id`) da série mensal acumulada
3. Confirme a frequência, unidade e data de início da série
4. Confirme via amostragem da API: GET https://api.bcb.gov.br/dados/serie/bcdata.sgs.{id}/dados/ultimos/3?formato=json

Devolva apenas:

- series_id confirmado
- nome oficial da série
- frequência
- unidade
- data de início
- exemplo de 3 valores recentes

Se houver mais de uma série candidata (ex: "CDI" tem 4 séries), liste todas com suas diferenças.
```

**Por quê isolar:** pesquisas externas trazem muito ruído (HTML, snippets longos). Subagent absorve e devolve só o essencial.

#### 2. **`docs-fetcher`** — busca de documentação

`.claude/agents/docs-fetcher.md`:

```markdown
---
name: docs-fetcher
description: Busca e resume documentação técnica de uma biblioteca específica. Use quando precisar de docs atualizados de Astro, Tailwind, python-telegram-bot, httpx, matplotlib, etc.
tools: WebFetch, WebSearch, mcp__context7
---

Você busca documentação técnica e devolve o necessário para resolver a tarefa em questão.

Recebe: nome da biblioteca + tópico específico (ex: "Astro: como definir getStaticPaths").

Faz:

1. Tenta primeiro via Context7 MCP (mais confiável e versionado)
2. Se faltar, busca na doc oficial da biblioteca
3. Para Astro especificamente, prefere docs.astro.build
4. Para python-telegram-bot, prefere docs.python-telegram-bot.org

Devolve:

- API/sintaxe relevante
- Exemplo de código mínimo funcionando
- Link da fonte
- Se houver uma quebra entre versões recentes, alertar

Não faça suposições baseadas em conhecimento de treinamento. Sempre verifique a doc real.
```

### 🔴 Não criar

- **code-reviewer** genérico — não há time, é você revisando
- **test-runner** — pode ser um script bash simples
- **deploy-agent** — `python -m pipeline.cli publish` já é a interface

---

## Skills

Skills são workflows reutilizáveis com auto-invocação. Crie quando você se pegar repetindo o mesmo "modo de operar".

### 🟢 Criar

#### 1. **`add-indicator`** — adicionar novo indicador ao catálogo

`.claude/skills/add-indicator/SKILL.md`:

````markdown
---
name: add-indicator
description: Adiciona um novo indicador econômico ao sistema. Use quando o usuário pedir para adicionar IGP-M, SELIC, INPC, ou qualquer outro indicador novo ao catálogo.
---

# Adicionar Indicador

Workflow para adicionar um indicador novo. Não pular etapas.

## Passos

1. **Pesquisa da fonte** — invoque o subagent `bcb-research` para confirmar series_id, frequência, data de início

2. **Validação** — confirme com o usuário:
   - Code (ex: "IGPM")
   - Slug URL (ex: "igp-m")
   - Categoria (ver `docs/03-data-model.md`)
   - Frequência confirmada
   - Source URL institucional

3. **Long description** — escreva ou peça ao usuário um markdown explicando o que é o indicador (3 seções: O que é, Para que serve, Fonte). Use os existentes em `docs/08-indicators-catalog.md` como template.

4. **SEO templates** — gere meta_title e meta_description seguindo o padrão dos existentes.

5. **Migration** — crie `pipeline/db/migrations/NNN_add_<code>.sql` com `INSERT OR IGNORE`. Use UUID v4 fixo (gere uma vez, não muda em re-execuções).

6. **Atualizar catálogo** — adicione entrada em `docs/08-indicators-catalog.md`.

7. **Aplicar e backfill**:
   ```bash
   python -m pipeline.cli migrate
   python -m pipeline.cli backfill <CODE>
   python -m pipeline.cli build
   ```
````

8. **Validação final**:
   - Conta de valores no SQLite > 0
   - JSON gerado em `site/data/<slug>.json`
   - PNGs gerados em `site/public/charts/`
   - Página local renderiza: `cd site && pnpm dev`

9. **Deploy**: `python -m pipeline.cli deploy`

````

#### 2. **`smoke-test-milestone`** — validar fim de milestone

`.claude/skills/smoke-test-milestone/SKILL.md`:

```markdown
---
name: smoke-test-milestone
description: Executa smoke test de um milestone do plano de implementação. Use quando o usuário disser "vamos validar o milestone X" ou "smoke test do M3".
---

# Smoke Test de Milestone

1. Leia `docs/09-implementation-plan.md` na seção do milestone informado.

2. Para cada item da checklist "Entregas":
   - Verifique se está no código
   - Marque como ✅ ou ❌ no relatório

3. Execute os comandos da seção "Smoke test" do milestone.

4. Capture stdout e stderr de cada comando.

5. Devolva relatório estruturado:

````

## Milestone N — <título>

Entregas:

- ✅ ...
- ❌ ... (motivo)

Smoke test:

- Comando: <cmd>
  Resultado: <pass/fail>
  Output: <relevant lines>

Status: PASS | PARTIAL | FAIL
Próximos passos: <se PARTIAL ou FAIL>

```

6. Não avance para o próximo milestone sem PASS.
```

#### 3. **`debug-collection`** — investigar erro de coleta

`.claude/skills/debug-collection/SKILL.md`:

````markdown
---
name: debug-collection
description: Investiga erro de coleta de indicador. Use quando uma execução de `pipeline collect` retornar erro ou notificação Telegram de erro chegar.
---

# Debug de Coleta

1. **Identifique a falha**:
   ```sql
   SELECT * FROM collection_logs
   WHERE status = 'error'
   ORDER BY started_at DESC LIMIT 5;
   ```
````

(use o SQLite MCP)

2. **Inspecione a configuração**:

   ```sql
   SELECT code, connector_type, connector_config, last_collected_at
   FROM indicators WHERE code = ?;
   ```

3. **Reproduza isoladamente** o erro com Python REPL — chamar o connector diretamente, sem o pipeline:

   ```python
   from pipeline.connectors.bcb import BCBSGSConnector
   from datetime import date
   BCBSGSConnector().fetch({"series_id": <id>}, since=date(2024, 1, 1))
   ```

4. **Categorize o erro**:
   - HTTP 4xx → series_id inválido ou janela de datas vazia
   - HTTP 5xx → BCB indisponível, agendar retry
   - JSONDecodeError → BCB devolveu HTML (manutenção)
   - ParseError → formato de dado mudou na fonte

5. **Recomende a ação**:
   - Retry imediato
   - Aguardar e retry mais tarde
   - Atualizar config do indicador
   - Reportar mudança de formato (issue)

````

### 🔴 Não criar

- **`generate-changelog`** — formato de commit já está definido no CLAUDE.md
- **`commit`** — Claude Code já tem skill nativa boa para isso
- Skills "porque pode" — só skill quando você se pegar fazendo a mesma sequência 3+ vezes

---

## Scripts (bash)

São complementares aos comandos do CLI Python. Vão em `scripts/` no repositório.

### `scripts/setup.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Bootstrap completo do projeto numa máquina nova
python3 -m venv .venv
.venv/bin/pip install -U pip
.venv/bin/pip install -r pipeline/requirements.txt

cd site
pnpm install
cd ..

mkdir -p data pipeline/logs site/data site/public/charts

cp -n pipeline/.env.example pipeline/.env || true
echo "✓ Setup completo. Edite pipeline/.env com suas credenciais."
````

### `scripts/inspect-db.sh`

```bash
#!/usr/bin/env bash
# Atalhos para queries comuns sem precisar lembrar a sintaxe

DB="${DB_PATH:-./data/indicadores.db}"
case "${1:-}" in
  indicators) sqlite3 -header -column "$DB" "SELECT code, slug, frequency, active, last_collected_at FROM indicators;" ;;
  values)
    code="${2:?uso: inspect-db.sh values <CODE>}"
    sqlite3 -header -column "$DB" "
      SELECT reference_date, value, ytd, last_12m
      FROM indicator_values v JOIN indicators i ON v.indicator_id = i.id
      WHERE i.code = '$code' ORDER BY reference_date DESC LIMIT 24;
    " ;;
  errors)
    sqlite3 -header -column "$DB" "
      SELECT started_at, indicator_id, error_message
      FROM collection_logs WHERE status = 'error' ORDER BY started_at DESC LIMIT 10;
    " ;;
  builds)
    sqlite3 -header -column "$DB" "
      SELECT started_at, status, indicators_updated, git_commit_sha
      FROM build_logs ORDER BY started_at DESC LIMIT 10;
    " ;;
  *) echo "uso: inspect-db.sh {indicators|values <CODE>|errors|builds}" ;;
esac
```

### `scripts/validate-build.sh`

```bash
#!/usr/bin/env bash
# Confere que o build gerou os artefatos esperados
set -e
ERRORS=0

check() {
  if [[ -e "$1" ]]; then
    echo "✓ $1"
  else
    echo "✗ FALTANDO: $1"
    ERRORS=$((ERRORS + 1))
  fi
}

check site/data/indicators.json
check site/data/ipca.json
check site/data/cdi.json
check site/data/tr.json
check site/public/charts/ipca-history.png
check site/public/charts/cdi-history.png
check site/public/charts/tr-history.png

if [[ $ERRORS -gt 0 ]]; then
  echo "❌ $ERRORS arquivos faltando."
  exit 1
fi
echo "✓ Build válido."
```

### `scripts/install_cron.sh`

```bash
#!/usr/bin/env bash
# Instala entrada cron para o pipeline diário
set -e
REPO="$(cd "$(dirname "$0")/.." && pwd)"
CRON_LINE="0 7 * * * cd $REPO && $REPO/.venv/bin/python -m pipeline.cli collect --all && $REPO/.venv/bin/python -m pipeline.cli publish >> $REPO/pipeline/logs/cron.log 2>&1"

(crontab -l 2>/dev/null | grep -v "pipeline.cli collect"; echo "$CRON_LINE") | crontab -
echo "✓ Cron instalado:"
crontab -l | grep pipeline.cli
```

### `scripts/install_systemd.sh`

```bash
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
```

---

## Hooks

Hooks executam scripts em eventos do Claude Code. Não exagerar para não criar fricção.

### 🟢 Criar

#### Hook 1: PreToolUse — confirmar git push

`.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash(git push.*)",
        "hooks": [
          {
            "type": "command",
            "command": "echo '⚠️  git push pendente. Confirme antes de aprovar a aprovação manual no Claude Code.'"
          }
        ]
      }
    ]
  }
}
```

Razão: deploy vai para produção. Forçar uma respiração antes do push evita acidentes.

#### Hook 2: SessionStart — status rápido

`.claude/settings.json` (adicionar):

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash scripts/inspect-db.sh indicators 2>/dev/null && echo '---' && bash scripts/inspect-db.sh builds 2>/dev/null | head -3"
          }
        ]
      }
    ]
  }
}
```

Razão: ao abrir uma sessão, o Claude Code já vê estado atual do sistema sem precisar consultar.

### 🔴 Não criar

- Hook `PostToolUse` para rodar pytest após cada edit — atrasa demais o desenvolvimento
- Hook para auto-formatar — ruff é rápido o suficiente para você rodar manualmente
- Hooks "porque é legal" — fricção desnecessária

---

## Convenções de uso do Claude Code

Para tirar o máximo do investimento:

### 1. Uma sessão por milestone

Cada milestone do `09-implementation-plan.md` deve ser uma sessão dedicada do Claude Code. Use `/clear` entre milestones. Isso evita que decisões antigas pesem no contexto do próximo trabalho.

### 2. Comece sempre com referência ao doc

Primeira mensagem de cada sessão:

> Leia `docs/09-implementation-plan.md` na seção Milestone N e os docs referenciados nas entregas. Em seguida, execute o milestone passo a passo. Não avance além do escopo. Ao final, rode a skill `smoke-test-milestone`.

Isso usa o CLAUDE.md (auto-loaded) + docs específicos (sob demanda) + skill como controle de qualidade.

### 3. Use `/compact` antes do contexto encher

Quando atingir ~70% do contexto numa sessão longa, rodar `/compact` preserva o essencial e libera espaço.

### 4. Delegue exploração para subagents

Quando for adicionar um indicador novo, em vez de "pesquise series_id do INCC" no chat principal, peça "use o subagent bcb-research para mapear o INCC". O contexto principal não enche com snippets de pesquisa.

### 5. Não use Claude Code para tarefas que um script resolve

Coletar todos os indicadores? `python -m pipeline.cli collect --all` direto no terminal. Não envolva o Claude Code para executar comandos triviais — ele consome tokens só para invocar bash.

### 6. Configure model selection

Para tarefas mecânicas (renomeação, ajuste de imports, lint), use Haiku via `/model haiku` na sessão. Para arquitetura, debugging complexo, design decisions: Opus. Para a maioria do dev: Sonnet.

---

## Resumo das instalações

```bash
# MCPs
claude mcp add sqlite -- uvx mcp-server-sqlite --db-path ./data/indicadores.db
claude mcp add github --env GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx -- npx -y @modelcontextprotocol/server-github
claude mcp add context7 -- npx -y @upstash/context7-mcp

# Estrutura no repo (criar antes da primeira sessão)
mkdir -p .claude/agents .claude/skills/{add-indicator,smoke-test-milestone,debug-collection} scripts

# Subagents → criar os 2 .md
# Skills → criar os 3 SKILL.md
# Scripts → criar os 5 .sh e dar chmod +x
# .claude/settings.json → adicionar os 2 hooks
```

## Estimativa de impacto

| Item                  | Tokens economizados/mês\* | Erros evitados                   |
| --------------------- | ------------------------- | -------------------------------- |
| SQLite MCP            | ~25k                      | Decisões com base em dado errado |
| Context7 MCP          | ~15k                      | Erros por API desatualizada      |
| Subagent bcb-research | ~10k por indicador novo   | series_id errado                 |
| Skill add-indicator   | ~5k por indicador         | Esquecer migration ou seed       |
| Skill smoke-test      | ~3k por milestone         | Avançar com bug                  |
| Hook git push         | —                         | Deploy acidental                 |

\*estimativas grossas, baseadas em assumir uso médio de Claude Code durante implementação dos 9 milestones e operação subsequente.

---

## O que NÃO instalar (resumo dos principais "vampiros de tempo")

| Item popular                    | Por quê pular                            |
| ------------------------------- | ---------------------------------------- |
| Filesystem MCP                  | Já temos acesso ao projeto               |
| Brave Search MCP                | Web search é nativo                      |
| Memory MCP                      | CLAUDE.md cumpre o papel                 |
| Sentry/Datadog MCP              | Sem observabilidade nesse projeto        |
| Vercel MCP                      | Deploy é git push                        |
| Telegram MCP                    | Você testa o bot direto no app           |
| 50+ subagents prontos de "kits" | Genéricos demais, não conhecem o projeto |
| Plugins de "AI persona"         | Marketing                                |
| Sequential Thinking MCP         | Thinking nativo já cobre                 |
