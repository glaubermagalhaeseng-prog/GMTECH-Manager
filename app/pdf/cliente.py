from reportlab.platypus import (
    Paragraph,
    Spacer
)

from app.pdf.estilos import normal


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
            normal
        )
    )

    elementos.append(
        Spacer(1, 20)
    )