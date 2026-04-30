# 03 — Conector IBGE SIDRA

## Visão geral

O SIDRA (Sistema IBGE de Recuperação Automática) é a API pública do IBGE para suas tabelas estatísticas. Ao contrário do BCB SGS, que tem uma estrutura uniforme de uma série numérica por endpoint, o SIDRA é multidimensional: cada tabela pode ter múltiplas variáveis, classificações, períodos e localidades.

## Endpoint base

```
https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos/{periodos}/variaveis/{variaveis}
?localidades={localidades}
&classificacao={classificacao}
```

### Parâmetros

| Parâmetro | Descrição | Exemplo |
|---|---|---|
| `{tabela}` | Código numérico da tabela agregada IBGE | `7060` (IPCA-15) |
| `{periodos}` | Períodos no formato YYYYMM, separados por vírgula. Aceita `all` ou intervalos `YYYYMM-YYYYMM` | `202401-202403` |
| `{variaveis}` | Códigos das variáveis | `355` (variação mensal %) |
| `{localidades}` | Código da localidade. Para Brasil agregado: `BR` ou `N1[all]` | `N1[all]` |
| `{classificacao}` | Filtro adicional opcional (ex: grupos de despesa) | `315[7170]` |

### Formato de resposta

A resposta é um array JSON. A estrutura é aninhada e exige navegação cuidadosa:

```json
[
  {
    "id": "355",
    "variavel": "IPCA-15 - Variação mensal",
    "unidade": "%",
    "resultados": [
      {
        "classificacoes": [],
        "series": [
          {
            "localidade": {
              "id": "1",
              "nivel": {"id": "N1", "nome": "Brasil"},
              "nome": "Brasil"
            },
            "serie": {
              "202401": "0.31",
              "202402": "0.78",
              "202403": "0.36"
            }
          }
        ]
      }
    ]
  }
]
```

**Observações:**

- Valor `"-"` significa "não disponível"
- Valor pode ser `"..."` em casos de dado suprimido
- Datas são strings `YYYYMM` (ano + mês concatenados)
- Decimais usam ponto, não vírgula
- API não tem autenticação
- Sem rate limit publicado; usar pausa de 1s entre chamadas

## Implementação

### Arquivo: `pipeline/connectors/ibge_sidra.py`

```python
from datetime import date
from dateutil.relativedelta import relativedelta
import time
import httpx
from .base import BaseConnector, RawDataPoint, FetchError, ParseError, register

SIDRA_BASE_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/"
    "{tabela}/periodos/{periodos}/variaveis/{variaveis}"
)
PAGINATION_PAUSE_SECONDS = 1.0
MAX_PERIODS_PER_REQUEST = 60  # 5 anos de dados mensais por chamada


@register("ibge_sidra")
class IBGESIDRAConnector(BaseConnector):
    """Conector para a API SIDRA v3 do IBGE."""

    def fetch(self, config, since=None, until=None):
        tabela = config["tabela"]
        variavel = config["variavel"]
        localidade = config.get("localidade", "N1[all]")
        classificacao = config.get("classificacao")

        until = until or date.today().replace(day=1)
        since = since or self._earliest_default(config)

        all_points = []
        for window in self._period_windows(since, until):
            points = self._fetch_window(
                tabela, variavel, window, localidade, classificacao
            )
            all_points.extend(points)
            time.sleep(PAGINATION_PAUSE_SECONDS)

        # Dedup, ordena
        seen = set()
        unique = []
        for p in sorted(all_points, key=lambda x: x.reference_date):
            if p.reference_date not in seen:
                seen.add(p.reference_date)
                unique.append(p)
        return unique

    def _period_windows(self, since: date, until: date):
        """Gera janelas de períodos no formato YYYYMM-YYYYMM."""
        cursor = since.replace(day=1)
        while cursor <= until:
            window_end = min(
                cursor + relativedelta(months=MAX_PERIODS_PER_REQUEST - 1),
                until,
            )
            yield (
                cursor.strftime("%Y%m"),
                window_end.strftime("%Y%m"),
            )
            cursor = window_end + relativedelta(months=1)

    def _fetch_window(self, tabela, variavel, window, localidade, classificacao):
        start, end = window
        periodos = f"{start}-{end}"
        url = SIDRA_BASE_URL.format(
            tabela=tabela, periodos=periodos, variaveis=variavel
        )
        params = {"localidades": localidade}
        if classificacao:
            params["classificacao"] = classificacao

        try:
            response = httpx.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise FetchError(
                f"Erro HTTP ao buscar SIDRA tabela={tabela} periodos={periodos}: {e}"
            ) from e
        except ValueError as e:
            raise ParseError(f"Resposta não-JSON do SIDRA: {e}") from e

        return list(self._parse_response(data))

    def _parse_response(self, data):
        """Navega a estrutura aninhada do SIDRA e extrai pontos."""
        if not isinstance(data, list) or not data:
            return

        for variavel_block in data:
            try:
                resultados = variavel_block.get("resultados", [])
            except AttributeError:
                continue

            for resultado in resultados:
                series = resultado.get("series", [])
                for serie_block in series:
                    serie = serie_block.get("serie", {})
                    for periodo_str, value_str in serie.items():
                        if value_str in ("-", "...", None, ""):
                            continue
                        try:
                            ref = self._parse_period(periodo_str)
                            value = float(str(value_str).replace(",", "."))
                        except (ValueError, KeyError) as e:
                            raise ParseError(
                                f"Item inválido no SIDRA: periodo={periodo_str}, valor={value_str} ({e})"
                            ) from e
                        yield RawDataPoint(
                            reference_date=ref,
                            value=value,
                            raw_value=str(value_str),
                        )

    def _parse_period(self, s: str) -> date:
        """SIDRA devolve YYYYMM para mensal. Converte para data do dia 1."""
        if len(s) != 6:
            raise ValueError(f"Período não-mensal não suportado: {s}")
        year = int(s[:4])
        month = int(s[4:])
        return date(year, month, 1)

    def _earliest_default(self, config) -> date:
        """Data de início padrão se a config não definir."""
        # SIDRA aceita 'all' mas é mais seguro especificar
        # Cada indicador define inception_date no DB; o connector recebe via since
        return date(1990, 1, 1)
```

### Tratamento de exceções

| Cenário | Comportamento |
|---|---|
| Tabela inexistente | HTTP 404 → `FetchError` |
| Variável inexistente | Resposta vazia ou erro estrutural → `ParseError` |
| Período sem dado (`"-"` ou `"..."`) | Ignora silenciosamente, não levanta erro |
| Vírgula como decimal (improvável no SIDRA, mas defensivo) | `replace(",", ".")` |
| Período não-mensal | `ParseError` (Fase 2 só suporta mensal) |
| Mais de uma localidade na resposta (BR + UFs) | Itera todas; quem chama deve garantir filtro `localidade` específico |

## connector_config para indicadores Fase 2

### IPCA-15

```json
{
  "tabela": 7060,
  "variavel": 355,
  "localidade": "N1[all]"
}
```

- Tabela 7060: IPCA-15 - Variação Mensal, Acumulada no Ano e Acumulada em 12 Meses
- Variável 355: variação mensal (%)
- N1[all]: agregado Brasil

> Os IDs acima devem ser validados via subagent `bcb-research` adaptado para SIDRA, ou via consulta manual em https://sidra.ibge.gov.br/tabela/7060 antes da implementação.

## Testes

`pipeline/connectors/tests/test_ibge_sidra.py` cobre:

1. Janela única com resposta completa
2. Janela com período faltante (`"-"`)
3. Múltiplas janelas (paginação)
4. HTTP 404 (tabela inválida)
5. JSON malformado
6. Resposta com múltiplas localidades (deve filtrar)
7. Período não-mensal (deve dar `ParseError`)

Use `respx` para mockar o httpx. Salve fixtures de respostas reais em `tests/fixtures/sidra/`.

## Backfill estimado para IPCA-15

- IPCA-15 começa em maio/2000 (~25 anos = ~300 períodos mensais)
- Com janelas de 60 períodos: ~5 chamadas + pausas = ~10s total

## Limites e quirks conhecidos do SIDRA

1. **Estrutura aninhada complexa**: 4 níveis (variavel → resultado → serie → serie). Cuidado ao navegar.
2. **Localidades múltiplas**: se `localidades=BR` retorna apenas Brasil; `N1[all]` retorna apenas Brasil também (N1 é o nível "Brasil"). Para regiões metropolitanas seria `N7[all]`.
3. **`all` em períodos**: aceito, mas pode ser lento e estourar timeout para tabelas grandes. Preferir intervalos.
4. **Cache do IBGE**: respostas têm cache server-side; mudanças de dados podem demorar até 1h para refletir.
5. **HTTP 4xx vs 5xx**: o IBGE eventualmente devolve 200 com array vazio em vez de 404 para parâmetros inválidos. O conector trata array vazio como "sem dados", não como erro.

## Estratégia de mock para testes

Fixture mínima válida em `tests/fixtures/sidra/ipca15_jan_mar_2024.json`:

```json
[
  {
    "id": "355",
    "variavel": "IPCA-15 - Variação mensal",
    "unidade": "%",
    "resultados": [
      {
        "classificacoes": [],
        "series": [
          {
            "localidade": {"id": "1", "nivel": {"id": "N1", "nome": "Brasil"}, "nome": "Brasil"},
            "serie": {
              "202401": "0.31",
              "202402": "0.78",
              "202403": "0.36"
            }
          }
        ]
      }
    ]
  }
]
```

## Decisão sobre o IPCA "principal"

O IPCA da Fase 1 vem do BCB SGS série 433. **Mantemos isso na Fase 2.** Não migrar o IPCA para SIDRA — abrir essa frente significaria revalidar a série inteira, o que é risco desnecessário sem ganho claro.

A migração do IPCA para SIDRA fica como item explícito do backlog de Fase 3, **se** houver justificativa (ex: precisar de granularidade regional).
