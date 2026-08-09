from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors


# ==========================================
# PALETA GMTECH
# ==========================================

AZUL = colors.HexColor("#073B4C")
LARANJA = colors.HexColor("#F7941D")
CINZA = colors.HexColor("#8A94A0")
CINZA_CLARO = colors.HexColor("#F4F6F9")
VERDE = colors.HexColor("#198754")
VERMELHO = colors.HexColor("#D64545")
BRANCO = colors.white


_base = getSampleStyleSheet()


# ==========================================
# ESTILOS DE TEXTO
# ==========================================

titulo = _base["Title"]
titulo.alignment = TA_CENTER

normal = _base["Normal"]

heading = _base["Heading2"]


capa_titulo = ParagraphStyle(
    "capa_titulo",
    parent=_base["Normal"],
    fontName="Helvetica-Bold",
    fontSize=34,
    leading=38,
    textColor=AZUL
)

capa_subtitulo = ParagraphStyle(
    "capa_subtitulo",
    parent=_base["Normal"],
    fontName="Helvetica-Bold",
    fontSize=30,
    leading=34,
    textColor=LARANJA
)

capa_linha = ParagraphStyle(
    "capa_linha",
    parent=_base["Normal"],
    fontName="Helvetica",
    fontSize=16,
    leading=20,
    textColor=AZUL
)

capa_info = ParagraphStyle(
    "capa_info",
    parent=_base["Normal"],
    fontName="Helvetica",
    fontSize=11,
    leading=16,
    textColor=colors.HexColor("#444444")
)

secao_titulo = ParagraphStyle(
    "secao_titulo",
    parent=_base["Normal"],
    fontName="Helvetica-Bold",
    fontSize=22,
    leading=26,
    textColor=AZUL
)

secao_titulo_leve = ParagraphStyle(
    "secao_titulo_leve",
    parent=_base["Normal"],
    fontName="Helvetica",
    fontSize=22,
    leading=26,
    textColor=CINZA
)

subtitulo_item = ParagraphStyle(
    "subtitulo_item",
    parent=_base["Normal"],
    fontName="Helvetica-Bold",
    fontSize=12,
    leading=15,
    textColor=AZUL
)

corpo = ParagraphStyle(
    "corpo",
    parent=_base["Normal"],
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    textColor=colors.HexColor("#333333")
)

corpo_centro = ParagraphStyle(
    "corpo_centro",
    parent=corpo,
    alignment=TA_CENTER
)

numero_destaque = ParagraphStyle(
    "numero_destaque",
    parent=_base["Normal"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    textColor=AZUL,
    alignment=TA_CENTER
)

rotulo_destaque = ParagraphStyle(
    "rotulo_destaque",
    parent=_base["Normal"],
    fontName="Helvetica",
    fontSize=9,
    leading=12,
    textColor=CINZA,
    alignment=TA_CENTER
)

rodape_pagina = ParagraphStyle(
    "rodape_pagina",
    parent=_base["Normal"],
    fontName="Helvetica",
    fontSize=8,
    leading=10,
    textColor=CINZA,
    alignment=TA_CENTER
)


def titulo_dois_tons(parte_leve, parte_forte, tamanho=22):
    """Ex.: 'SEU' (cinza) + 'PROJETO' (azul, negrito) na mesma linha."""

    return (
        f'<font color="#8A94A0" size="{tamanho}">{parte_leve} </font>'
        f'<font color="#073B4C" size="{tamanho}"><b>{parte_forte}</b></font>'
    )
