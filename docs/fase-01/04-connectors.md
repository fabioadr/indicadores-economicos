# 04 — Conectores

## Filosofia

Cada fonte de dados é um conector. O core do pipeline não conhece detalhes de API: pega o `connector_type` do indicador, instancia a classe correspondente, e chama `fetch()`.

Adicionar uma nova fonte = adicionar um arquivo em `pipeline/connectors/` + registrar em um dict.

## Interface base

```python
# pipeline/connectors/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any

@dataclass
class RawDataPoint:
    """Ponto de dado normalizado retornado por qualquer conector."""
    reference_date: date  # 1º do mês para mensais
    value: float          # percentual, ex: 0.44 para 0,44%
    raw_value: str        # valor original como veio da fonte (auditoria)


class ConnectorError(Exception):
    """Erro genérico de conector."""


class FetchError(ConnectorError):
    """Erro ao buscar dados (rede, HTTP status, etc.)"""


class ParseError(ConnectorError):
    """Erro ao interpretar dados (formato inesperado)"""


class BaseConnector(ABC):
    """Interface base para todos os conectores."""

    @abstractmethod
    def fetch(
        self,
        config: dict[str, Any],
        since: date | None = None,
        until: date | None = None,
    ) -> list[RawDataPoint]:
        """
        Busca dados da fonte.
        - config: vem do indicators.connector_config (já parseado de JSON)
        - since: data inicial inclusive (None = desde o início da série)
        - until: data final inclusive (None = até hoje)
        Retorna lista ordenada por data ascendente.
        Lança FetchError ou ParseError em caso de erro.
        """
        ...


# Registry
CONNECTORS: dict[str, type[BaseConnector]] = {}

def register(name: str):
    def decorator(cls: type[BaseConnector]):
        CONNECTORS[name] = cls
        return cls
    return decorator

def get_connector(name: str) -> BaseConnector:
    if name not in CONNECTORS:
        raise ValueError(f"Connector desconhecido: {name}")
    return CONNECTORS[name]()
```

## BCB SGS Connector

### Especificação da API

- **Base URL**: `https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados`
- **Formato**: `?formato=json`
- **Janela**: `&dataInicial=DD/MM/YYYY&dataFinal=DD/MM/YYYY`
- **Limite**: máximo de 10 anos por requisição
- **Resposta**: array JSON `[{"data": "DD/MM/YYYY", "valor": "0.44"}, ...]`
- **Rate limit**: não documentado oficialmente; usar pausa de 1s entre chamadas conservativamente
- **HTTPS**: obrigatório
- **Sem autenticação**

### Implementação

```python
# pipeline/connectors/bcb.py
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import httpx
from .base import BaseConnector, RawDataPoint, FetchError, ParseError, register

BCB_BASE_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{series_id}/dados"
MAX_WINDOW_YEARS = 10
PAGINATION_PAUSE_SECONDS = 1.0


@register("bcb_sgs")
class BCBSGSConnector(BaseConnector):
    """Conector para o Sistema Gerenciador de Séries Temporais do BCB."""

    def fetch(self, config, since=None, until=None):
        series_id = config["series_id"]
        until = until or date.today()
        since = since or self._earliest_default()

        all_points = []
        for window_start, window_end in self._windows(since, until):
            points = self._fetch_window(series_id, window_start, window_end)
            all_points.extend(points)
            time.sleep(PAGINATION_PAUSE_SECONDS)

        # Dedup (janelas sobrepostas) e ordena
        seen = set()
        unique = []
        for p in sorted(all_points, key=lambda x: x.reference_date):
            if p.reference_date not in seen:
                seen.add(p.reference_date)
                unique.append(p)
        return unique

    def _windows(self, since: date, until: date):
        """Gera janelas de até 10 anos respeitando o limite da API."""
        cursor = since
        while cursor <= until:
            window_end = min(
                cursor + relativedelta(years=MAX_WINDOW_YEARS) - timedelta(days=1),
                until,
            )
            yield cursor, window_end
            cursor = window_end + timedelta(days=1)

    def _fetch_window(self, series_id, start, end):
        url = BCB_BASE_URL.format(series_id=series_id)
        params = {
            "formato": "json",
            "dataInicial": start.strftime("%d/%m/%Y"),
            "dataFinal": end.strftime("%d/%m/%Y"),
        }
        try:
            response = httpx.get(url, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            raise FetchError(f"Erro HTTP ao buscar série {series_id}: {e}") from e
        except ValueError as e:
            raise ParseError(f"Resposta não-JSON para série {series_id}: {e}") from e

        return [self._parse_point(item) for item in data]

    def _parse_point(self, item):
        try:
            reference_date = self._parse_date(item["data"])
            raw = item["valor"]
            value = float(raw.replace(",", "."))  # BCB usa ponto, mas seguro
        except (KeyError, ValueError) as e:
            raise ParseError(f"Item inválido: {item} ({e})") from e
        return RawDataPoint(
            reference_date=reference_date,
            value=value,
            raw_value=str(raw),
        )

    def _parse_date(self, s: str) -> date:
        # Formato BCB: DD/MM/YYYY
        d, m, y = s.split("/")
        ref = date(int(y), int(m), int(d))
        # Para séries mensais o BCB devolve dia 1; já vem normalizado
        return ref

    def _earliest_default(self) -> date:
        # Séries do BCB começam, no mais antigo, em 1986
        return date(1986, 1, 1)
```

### Comportamento esperado

| Cenário | Comportamento |
|---|---|
| Série vazia para a janela | Retorna lista vazia (não erro) |
| HTTP 5xx | `FetchError` com mensagem |
| HTTP 200 mas JSON malformado | `ParseError` |
| Dado com vírgula em vez de ponto | Trata transparentemente (`replace(",", ".")`) |
| Backfill 1986→hoje | ~4 chamadas (40 anos / 10 anos) com pausa de 1s = ~4s total |

### Configurações para os indicadores Fase 1

Ver `08-indicators-catalog.md` — cada um tem `connector_config` próprio.

## Estratégia para futuros conectores

### IBGE SIDRA (Fase 2)

API REST mais complexa. Precisa receber `tabela`, `variavel`, `localidade`. URL:

```
https://servicodados.ibge.gov.br/api/v3/agregados/{tabela}/periodos/{periodos}/variaveis/{variaveis}?localidades={localidades}
```

### FGV (Fase 2)

Não tem API pública estável. Provavelmente CSV/HTML scraping a partir de portalibre.fgv.br ou ftp.

### Custom HTTP (Fase 2)

Conector genérico configurável: URL, JSONPath para valor e data, formato de data. Resolve casos pontuais sem criar classe nova.

## Testes

Cada conector tem testes em `pipeline/connectors/tests/test_<connector>.py`:

- Teste com fixture de resposta JSON real (snapshot capturado uma vez)
- Teste de janela única
- Teste de paginação (múltiplas janelas)
- Teste de erro de rede (mock httpx)
- Teste de parse error (JSON malformado)

Os testes não fazem chamadas HTTP reais (use `respx` para mockar httpx).
