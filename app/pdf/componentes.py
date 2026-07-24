# Componentes reutilizáveis do PDF GMTECH
from reportlab.platypus import Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from app.pdf.estilos import AZUL

estilos = getSampleStyleSheet()


def cabecalho(elementos, proposta):

    titulo = estilos["Title"]
    titulo.alignment = TA_CENTER
    titulo.textColor = AZUL

    elementos.append(
        Paragraph(
            "GMTECH Soluções Elétricas",
            titulo
        )
    )

    elementos.append(
        Spacer(1, 20)
    )

    elementos.append(
        Paragraph(
            f"Proposta Comercial Nº {proposta['id']}",
            estilos["Heading2"]
        )
    )

    elementos.append(
        Spacer(1, 12)
    )


def dados_cliente(elementos, proposta):
    pass


def tabela_itens(elementos, itens):
    pass


def total_proposta(elementos, total):
    pass


def condicoes(elementos):
    pass


def rodape(elementos):
    pass