"""
Calculadora de ROI solar — payback, VPL, TIR, fluxo ano a ano.

Premissas padrão alinhadas ao mercado BR de GD:
- reajuste de tarifa ~8% a.a. (histórico aproximado)
- degradação de módulos ~0,5% a.a.
- horizonte 25 anos
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _safe_float(v, default=0.0) -> float:
    try:
        if v is None or v == "":
            return float(default)
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _npv(taxa: float, fluxos: List[float]) -> float:
    """VPL de uma série de fluxos (índice 0 = ano 0)."""
    total = 0.0
    for t, f in enumerate(fluxos):
        total += f / ((1.0 + taxa) ** t)
    return total


def _irr(fluxos: List[float], guess: float = 0.12, tol: float = 1e-6, max_iter: int = 100) -> Optional[float]:
    """
    TIR (taxa interna de retorno) pelo método de Newton-Raphson.
    Retorna None se não convergir ou se não houver mudança de sinal.
    """
    if not fluxos or all(f >= 0 for f in fluxos) or all(f <= 0 for f in fluxos):
        return None

    r = guess
    for _ in range(max_iter):
        npv = 0.0
        dnpv = 0.0
        for t, f in enumerate(fluxos):
            denom = (1.0 + r) ** t
            npv += f / denom
            if t > 0:
                dnpv -= t * f / ((1.0 + r) ** (t + 1))
        if abs(dnpv) < 1e-12:
            break
        r_new = r - npv / dnpv
        if abs(r_new - r) < tol:
            # limites razoáveis
            if r_new < -0.99 or r_new > 5:
                return None
            return r_new
        r = r_new
    return None


def calcular_roi(
    investimento: float,
    economia_mensal: float,
    *,
    anos: int = 25,
    reajuste_tarifa_aa: float = 8.0,
    degradacao_aa: float = 0.5,
    taxa_desconto_aa: float = 10.0,
    om_anual: float = 0.0,
    om_reajuste_aa: float = 5.0,
) -> Dict[str, Any]:
    """
    Calcula indicadores de retorno do sistema fotovoltaico.

    Parameters
    ----------
    investimento : custo total do sistema (R$)
    economia_mensal : economia no ano 1, média mensal (R$/mês)
    anos : horizonte de análise
    reajuste_tarifa_aa : % a.a. de aumento da tarifa (e da economia)
    degradacao_aa : % a.a. de perda de geração
    taxa_desconto_aa : % a.a. para VPL (custo de oportunidade)
    om_anual : custo anual de O&M no ano 1 (R$)
    om_reajuste_aa : reajuste do O&M (% a.a.)
    """
    investimento = max(0.0, _safe_float(investimento))
    economia_mensal = max(0.0, _safe_float(economia_mensal))
    anos = max(1, min(40, int(_safe_float(anos, 25))))
    reajuste = _safe_float(reajuste_tarifa_aa, 8.0) / 100.0
    degrad = _safe_float(degradacao_aa, 0.5) / 100.0
    desconto = _safe_float(taxa_desconto_aa, 10.0) / 100.0
    om0 = max(0.0, _safe_float(om_anual))
    om_reaj = _safe_float(om_reajuste_aa, 5.0) / 100.0

    economia_ano1 = economia_mensal * 12.0

    # Payback simples (sem reajuste/degradação) — referência rápida
    payback_simples_anos = (
        (investimento / economia_ano1) if economia_ano1 > 0 else None
    )

    # Fluxo de caixa ano a ano
    # Ano 0: -investimento
    fluxos: List[float] = [-investimento]
    tabela: List[Dict[str, Any]] = []

    acumulado = -investimento
    payback_anos: Optional[float] = None
    economia_total = 0.0
    om_total = 0.0

    for ano in range(1, anos + 1):
        # economia cresce com tarifa e cai com degradação
        fator_tarifa = (1.0 + reajuste) ** (ano - 1)
        fator_degrad = (1.0 - degrad) ** (ano - 1)
        eco = economia_ano1 * fator_tarifa * fator_degrad

        om = om0 * ((1.0 + om_reaj) ** (ano - 1)) if om0 else 0.0
        liquido = eco - om

        economia_total += eco
        om_total += om
        acumulado_anterior = acumulado
        acumulado += liquido
        fluxos.append(liquido)

        # payback interpolado no ano em que cruza zero
        if payback_anos is None and acumulado_anterior < 0 <= acumulado:
            if liquido != 0:
                frac = (-acumulado_anterior) / liquido
                payback_anos = (ano - 1) + frac
            else:
                payback_anos = float(ano)

        tabela.append({
            "ano": ano,
            "economia": round(eco, 2),
            "om": round(om, 2),
            "liquido": round(liquido, 2),
            "acumulado": round(acumulado, 2),
        })

    if payback_anos is None and acumulado >= 0 and economia_ano1 > 0:
        payback_anos = float(anos)

    lucro_liquido = acumulado  # já descontado investimento no acumulado
    roi_percent = (
        (lucro_liquido / investimento) * 100.0 if investimento > 0 else None
    )

    vpl = _npv(desconto, fluxos)
    tir = _irr(fluxos)

    # Payback descontado: quando VPL parcial zera
    payback_descontado: Optional[float] = None
    acum_desc = fluxos[0]
    for ano in range(1, len(fluxos)):
        prev = acum_desc
        parcela = fluxos[ano] / ((1.0 + desconto) ** ano)
        acum_desc += parcela
        if payback_descontado is None and prev < 0 <= acum_desc:
            if parcela != 0:
                frac = (-prev) / parcela
                payback_descontado = (ano - 1) + frac
            else:
                payback_descontado = float(ano)

    return {
        "investimento": round(investimento, 2),
        "economia_mensal": round(economia_mensal, 2),
        "economia_ano1": round(economia_ano1, 2),
        "anos": anos,
        "reajuste_tarifa_aa": round(reajuste * 100, 2),
        "degradacao_aa": round(degrad * 100, 2),
        "taxa_desconto_aa": round(desconto * 100, 2),
        "om_anual": round(om0, 2),
        "payback_simples_anos": (
            round(payback_simples_anos, 2) if payback_simples_anos is not None else None
        ),
        "payback_anos": round(payback_anos, 2) if payback_anos is not None else None,
        "payback_descontado_anos": (
            round(payback_descontado, 2) if payback_descontado is not None else None
        ),
        "economia_total": round(economia_total, 2),
        "om_total": round(om_total, 2),
        "lucro_liquido": round(lucro_liquido, 2),
        "roi_percent": round(roi_percent, 1) if roi_percent is not None else None,
        "vpl": round(vpl, 2),
        "tir_percent": round(tir * 100, 2) if tir is not None else None,
        "tabela": tabela,
        "fluxos": [round(f, 2) for f in fluxos],
        "labels_anos": [f"Ano {a}" for a in range(0, anos + 1)],
        "acumulados": [round(-investimento, 2)] + [r["acumulado"] for r in tabela],
    }
