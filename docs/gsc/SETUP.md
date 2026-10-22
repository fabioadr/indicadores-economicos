# Setup — acesso à Search Console API

Pré-requisito humano (uma vez). O pipeline **não** cria o projeto GCP nem
adiciona a service account no GSC. Sem estes passos, `gsc-collect` falha
loud com 403.

Smoke depois do código: `python -m pipeline.cli gsc-sites`.

## 1. Google Cloud

1. Crie (ou reutilize) um projeto GCP só para isto.
2. APIs e serviços → **Ativar** "Search Console API"
   (`webmasters.googleapis.com`).
3. IAM e administrador → Contas de serviço → **Criar**:
   - Nome sugerido: `gsc-reader`
   - Papéis no GCP: nenhum é necessário para ler o GSC.
4. Na conta criada → Chaves → Adicionar chave → JSON.
5. Grave o arquivo em `pipeline/secrets/gsc-sa.json` (gitignored).
   Copie o `client_email` (formato `gsc-reader@…iam.gserviceaccount.com`).

## 2. Search Console — autorizar a service account

Isto **não** é o IAM do GCP. Sem este passo a API devolve 403.

1. [Search Console](https://search.google.com/search-console) → propriedade
   do site → Configurações → Usuários e permissões → **Adicionar usuário**.
2. Cole o `client_email`.
3. Permissão:
   - **Restrito** — suficiente para Performance (query/page/clicks).
   - **Total** — preferível se quisermos o relatório de IA (AI Overviews /
     AI Mode). Várias fontes dizem que Restrito esconde essa superfície.

## 3. `siteUrl` — tem que bater exatamente

No GSC, abra a propriedade e copie o identificador:

| Tipo | Valor em `GSC_SITE_URL` | Nota |
|---|---|---|
| Domínio | `sc-domain:indicadoreseconomicoshoje.com.br` | **Preferível**: cobre apex e www |
| Prefixo | `https://indicadoreseconomicoshoje.com.br/` | Barra final conta |

Os dumps manuais em `Consultas.csv` / `Páginas.csv` misturam apex e www.
Propriedade de domínio elimina essa diluição na coleta.

## 4. `.env`

Em `pipeline/.env` (nunca commitar):

```
GSC_SITE_URL=sc-domain:indicadoreseconomicoshoje.com.br
GSC_CREDENTIALS_PATH=./pipeline/secrets/gsc-sa.json
```

## 5. Smoke

```bash
source .venv/bin/activate
python -m pipeline.cli migrate
python -m pipeline.cli gsc-sites
```

`gsc-sites` deve listar a propriedade com `siteFullUser` ou
`siteRestrictedUser`. Depois:

```bash
python -m pipeline.cli gsc-collect          # últimos ~7 dias
python -m pipeline.cli gsc-collect --backfill  # 16 meses, primeira vez
python -m pipeline.cli gsc-report
```

Atraso típico dos dados: 2–3 dias. `dataState=final` (padrão do coletor).

## Cadência

Cron semanal (segunda 08:00) via `scripts/install_cron.sh`: `gsc-collect`
e, se ok, `gsc-report`. Não dispara `build`/`deploy`. Dados ficam no SQLite
local — não vão para `site/data/` nem para o git.
