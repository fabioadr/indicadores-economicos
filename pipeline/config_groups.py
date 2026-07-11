"""Configuração dos grupos de comparação curados (Fase 2 / M14).

Cada grupo gera um PNG `compare-{slug}.png` e uma entrada em `groups.json`,
consumidos pelas páginas `/comparar/`.

Formato de `indicators` em cada grupo:

- string simples (`"IPCA"`): assume `metric` default do grupo e style `line`.
- dicionário (`{"code": "...", "metric": "...", "style": "line"|"step"}`):
  permite override por indicador (ex.: SELIC plotada como `step` por mudar
  apenas em reuniões do Copom).

A lista é versionada em código — adicionar/remover grupos é alteração simples
seguida de redeploy.
"""

from __future__ import annotations

INDICATOR_GROUPS: list[dict] = [
    {
        "slug": "inflacao-oficial",
        "title": "Inflação no Brasil: IPCA, IGP-M e INPC",
        "description": (
            "Os três principais índices de inflação brasileira lado a lado, "
            "no acumulado de 12 meses."
        ),
        "indicators": ["IPCA", "IGPM", "INPC"],
        "metric": "last_12m",
    },
    {
        "slug": "indices-fgv",
        "title": "Índices da FGV: IGP-M e IGP-DI",
        "description": (
            "Comparação entre os dois índices gerais de preços da FGV, "
            "no acumulado de 12 meses."
        ),
        "indicators": ["IGPM", "IGPDI"],
        "metric": "last_12m",
    },
    {
        "slug": "juros-vs-inflacao",
        "title": "Juros vs Inflação: SELIC e IPCA",
        "description": (
            "Como a SELIC se move em relação à inflação oficial. "
            "A SELIC é a taxa em vigor (% a.a.), definida pelo Copom em "
            "reuniões a cada 45 dias — pode haver mais de um valor no "
            "mesmo mês quando há mudança. A SELIC Acumulada e o IPCA são "
            "expressos como acumulado em 12 meses."
        ),
        "indicators": [
            {"code": "SELICAC", "metric": "last_12m"},
            {"code": "IPCA", "metric": "last_12m"},
            {"code": "SELIC", "metric": "value", "style": "step"},
        ],
        "metric": "last_12m",
    },
    {
        "slug": "construcao-civil",
        "title": "Construção Civil: INCC-M e IGP-M",
        "description": (
            "Custos da construção civil comparados ao índice geral de "
            "preços, no acumulado de 12 meses."
        ),
        "indicators": ["INCCM", "IGPM"],
        "metric": "last_12m",
    },
    {
        "slug": "poupanca-e-credito-imobiliario",
        "title": "Poupança e crédito imobiliário",
        "description": (
            "Do funding ao crédito: saldo da poupança (SBPE e rural) "
            "lado a lado com concessões e saldo de financiamento "
            "imobiliário a pessoas físicas."
        ),
        "indicators": ["POUPSAL", "FINIMOB", "FINISAL"],
        "metric": "value",
        "normalize": True,
    },
    {
        "slug": "precos-e-custo-imobiliario",
        "title": "Preços e custo imobiliário: IVG-R e INCC-M",
        "description": (
            "Valorização das garantias residenciais (IVG-R) comparada "
            "ao custo da construção civil (INCC-M), na variação "
            "acumulada em 12 meses."
        ),
        "indicators": ["IVGR", "INCCM"],
        "metric": "last_12m",
    },
]


def metric_label(metric: str) -> str:
    """Rótulo PT-BR do eixo Y para uma métrica de IndicatorValue."""
    return {
        "last_12m": "Acumulado 12 meses (%)",
        "last_24m": "Acumulado 24 meses (%)",
        "value": "Valor",
        "ytd": "Acumulado no ano (%)",
        "since_inception": "Acumulado desde o início (%)",
    }.get(metric, metric)


def metric_legend_suffix(metric: str) -> str:
    """Sufixo curto da legenda por indicador (mostra a métrica plotada)."""
    return {
        "last_12m": "12m",
        "last_24m": "24m",
        "value": "valor",
        "ytd": "YTD",
        "since_inception": "desde início",
    }.get(metric, metric)


def normalize_group(group: dict) -> dict:
    """Expande `indicators` para o formato uniforme `[{code, metric, style}, ...]`.

    Não muta `group`. Aceita strings simples ou dicts; preenche `metric`/`style`
    com defaults derivados do grupo.
    """
    default_metric = group.get("metric", "last_12m")
    items: list[dict] = []
    for raw in group["indicators"]:
        if isinstance(raw, str):
            items.append({"code": raw, "metric": default_metric, "style": "line"})
        else:
            items.append(
                {
                    "code": raw["code"],
                    "metric": raw.get("metric", default_metric),
                    "style": raw.get("style", "line"),
                }
            )
    out = dict(group)
    out["indicators"] = items
    return out


def group_codes(group: dict) -> list[str]:
    """Lista de codes do grupo, aceitando o formato cru ou normalizado."""
    out: list[str] = []
    for raw in group["indicators"]:
        if isinstance(raw, str):
            out.append(raw)
        else:
            out.append(raw["code"])
    return out
