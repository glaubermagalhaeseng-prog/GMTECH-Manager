from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate

from app.pdf.cabecalho import desenhar_cabecalho
from app.pdf.cliente import desenhar_cliente
from app.pdf.tabela import desenhar_tabela
from app.pdf.rodape import desenhar_total


def gerar_pdf_proposta(caminho, proposta, itens, empresa):

    documento = SimpleDocTemplate(
        caminho,
        pagesize=A4
    )

    elementos = []

    desenhar_cabecalho(
        elementos,
        proposta,
        empresa
    )

    desenhar_cliente(
        elementos,
        proposta
    )

    total = desenhar_tabela(
        elementos,
        itens
    )

    desenhar_total(
        elementos,
        total
    )

    documento.build(elementos)