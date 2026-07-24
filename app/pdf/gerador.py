import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)


estilos = getSampleStyleSheet()


# ==========================================
# CABEÇALHO
# ==========================================

def desenhar_cabecalho(elementos, proposta):

    caminho_logo = os.path.join(
        "app",
        "static",
        "img",
        "logo.png"
    )

    if os.path.exists(caminho_logo):

        logo = Image(
            caminho_logo,
            width=170,
            height=70
        )

        logo.hAlign = "CENTER"

        elementos.append(logo)
        elementos.append(Spacer(1, 15))


    titulo = estilos["Title"]
    titulo.alignment = TA_CENTER


    elementos.append(
        Paragraph(
            "PROPOSTA COMERCIAL",
            titulo
        )
    )


    elementos.append(
        Spacer(1, 10)
    )


    elementos.append(
        Paragraph(
            f"Proposta Nº {proposta['id']}",
            estilos["Heading2"]
        )
    )


    elementos.append(
        Spacer(1, 20)
    )



# ==========================================
# CLIENTE
# ==========================================

def desenhar_cliente(elementos, proposta):

    dados_cliente = f"""
    <b>Cliente:</b> {proposta['cliente_nome']}<br/>
    <b>Telefone:</b> {proposta['cliente_telefone'] or ''}<br/>
    <b>Email:</b> {proposta['cliente_email'] or ''}<br/>
    <b>Cidade:</b> {proposta['cliente_cidade'] or ''} - {proposta['cliente_uf'] or ''}
    """


    elementos.append(
        Paragraph(
            dados_cliente,
            estilos["Normal"]
        )
    )


    elementos.append(
        Spacer(1,20)
    )



# ==========================================
# TABELA DE ITENS
# ==========================================

def desenhar_tabela(elementos, itens):


    dados = [
        [
            "Descrição",
            "Qtd",
            "Valor Unit.",
            "Total"
        ]
    ]


    total = 0


    for item in itens:


        valor_total = (
            item["quantidade"] *
            item["valor_unitario"]
        )


        total += valor_total


        dados.append(
            [
                item["descricao"],
                str(item["quantidade"]),
                f"R$ {item['valor_unitario']:.2f}",
                f"R$ {valor_total:.2f}"
            ]
        )


    tabela = Table(
        dados,
        repeatRows=1
    )


    tabela.setStyle(
        TableStyle([

            (
                "GRID",
                (0,0),
                (-1,-1),
                0.5,
                colors.grey
            ),

            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.HexColor("#073B4C")
            ),

            (
                "TEXTCOLOR",
                (0,0),
                (-1,0),
                colors.white
            ),

            (
                "ALIGN",
                (1,1),
                (-1,-1),
                "RIGHT"
            ),

            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "MIDDLE"
            )

        ])
    )


    elementos.append(tabela)

    elementos.append(
        Spacer(1,20)
    )


    return total



# ==========================================
# TOTAL
# ==========================================

def desenhar_total(elementos,total):

    elementos.append(
        Paragraph(
            f"<b>TOTAL DA PROPOSTA:</b> R$ {total:.2f}",
            estilos["Heading2"]
        )
    )



# ==========================================
# GERAR PDF
# ==========================================

def gerar_pdf_proposta(caminho, proposta, itens):


    documento = SimpleDocTemplate(
        caminho,
        pagesize=A4
    )


    elementos = []


    desenhar_cabecalho(
        elementos,
        proposta
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