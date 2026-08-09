import math

from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart, HorizontalBarChart
from reportlab.lib import colors

from app.pdf.estilos import AZUL, LARANJA, VERDE, VERMELHO, CINZA


# ==========================================
# GRÁFICO: RETORNO ACUMULADO (25 ANOS)
# ==========================================

def grafico_retorno(investimento, economia_mensal, anos=25):

    investimento = investimento or 0
    economia_mensal = economia_mensal or 0

    valores = []

    for ano in range(anos + 1):

        acumulado = (economia_mensal * 12 * ano) - investimento

        valores.append(round(acumulado, 2))


    desenho = Drawing(480, 220)

    grafico = VerticalBarChart()

    grafico.x = 45
    grafico.y = 35
    grafico.width = 420
    grafico.height = 160

    grafico.data = [valores]

    grafico.categoryAxis.categoryNames = [
        f"Ano {a}" if a % 2 == 0 else "" for a in range(anos + 1)
    ]

    grafico.categoryAxis.labels.fontSize = 6
    grafico.categoryAxis.labels.dy = -2
    grafico.categoryAxis.labels.angle = 0

    grafico.valueAxis.labelTextFormat = "R$ %0.f"
    grafico.valueAxis.labels.fontSize = 7

    grafico.barWidth = 6

    # cor por barra: vermelho enquanto o acumulado é negativo
    # (antes do payback), verde a partir do momento em que o
    # investimento já se pagou
    for indice, valor in enumerate(valores):
        cor = VERMELHO if valor < 0 else VERDE
        grafico.bars[(0, indice)].fillColor = cor

    desenho.add(grafico)

    return desenho


# ==========================================
# GRÁFICO: GERAÇÃO x CONSUMO MENSAL
# ==========================================

def grafico_geracao_consumo(geracao_mensal):

    geracao_mensal = geracao_mensal or 0

    meses = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]

    # variação sazonal simples (mais sol no verão, menos no inverno)
    fatores = [
        1.08, 1.05, 1.02, 0.96, 0.90, 0.86,
        0.88, 0.95, 1.00, 1.05, 1.10, 1.10
    ]

    geracao = [round(geracao_mensal * f, 1) for f in fatores]

    consumo = [round(geracao_mensal, 1) for _ in meses]


    desenho = Drawing(480, 220)

    grafico = VerticalBarChart()

    grafico.x = 45
    grafico.y = 35
    grafico.width = 420
    grafico.height = 160

    grafico.data = [geracao, consumo]

    grafico.categoryAxis.categoryNames = meses
    grafico.categoryAxis.labels.fontSize = 7

    grafico.valueAxis.labelTextFormat = "%0.f"
    grafico.valueAxis.labels.fontSize = 7

    grafico.bars[0].fillColor = VERDE
    grafico.bars[1].fillColor = VERMELHO

    grafico.barWidth = 6
    grafico.groupSpacing = 8

    desenho.add(grafico)

    return desenho


# ==========================================
# GRÁFICO: COMPARATIVO DE RENTABILIDADE
# (economia anual investida em poupança,
#  CDI e renda fixa, a título ilustrativo)
# ==========================================

def grafico_rentabilidade(economia_mensal):

    economia_anual = (economia_mensal or 0) * 12

    poupanca = economia_anual * 0.0617
    cdi = economia_anual * 0.1065
    renda_fixa = economia_anual * 0.12


    desenho = Drawing(480, 160)

    grafico = HorizontalBarChart()

    grafico.x = 140
    grafico.y = 25
    grafico.width = 300
    grafico.height = 100

    grafico.data = [[poupanca, cdi, renda_fixa]]

    grafico.categoryAxis.categoryNames = [
        "Poupança",
        "100% CDI",
        "Renda Fixa 12% a.a"
    ]

    grafico.categoryAxis.labels.fontSize = 8

    grafico.valueAxis.labelTextFormat = "R$ %0.f"
    grafico.valueAxis.labels.fontSize = 7

    grafico.bars[0].fillColor = CINZA

    grafico.barWidth = 12

    desenho.add(grafico)

    return desenho


# ==========================================
# IMPACTO AMBIENTAL (ESTIMATIVA)
# ==========================================

def calcular_impacto_ambiental(geracao_mensal, anos=25):

    geracao_mensal = geracao_mensal or 0

    geracao_total_kwh = geracao_mensal * 12 * anos

    # fator médio de emissão do grid brasileiro (estimativa, kg CO2/kWh)
    co2_evitado_kg = geracao_total_kwh * 0.084

    # 1 árvore absorve, em média, ~22kg de CO2 por ano
    arvores = co2_evitado_kg / (22 * anos)

    # emissão média de um carro a combustão (estimativa, kg CO2/km)
    km_carro_evitados = co2_evitado_kg / 0.12

    return {
        "co2_toneladas": round(co2_evitado_kg / 1000, 2),
        "arvores": round(arvores),
        "km_carro_evitados": round(km_carro_evitados)
    }
