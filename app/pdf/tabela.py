from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Spacer, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

from app.formatadores import moeda_rs
from app.pdf.estilos import AZUL, LARANJA


def formatar_moeda(valor):
    return moeda_rs(valor)


def desenhar_tabela(elementos, itens):
    """Lista itens um abaixo do outro + total."""
    estilo_desc = ParagraphStyle(
        "item_desc_v", fontName="Helvetica", fontSize=10, leading=14,
        textColor=colors.HexColor("#222222"), alignment=TA_LEFT,
    )
    estilo_valor = ParagraphStyle(
        "item_valor_v", fontName="Helvetica-Bold", fontSize=11, leading=14,
        textColor=AZUL, alignment=TA_RIGHT,
    )
    estilo_total = ParagraphStyle(
        "item_total_v", fontName="Helvetica-Bold", fontSize=12, leading=16,
        textColor=colors.white, alignment=TA_LEFT,
    )
    estilo_total_v = ParagraphStyle(
        "item_total_vv", fontName="Helvetica-Bold", fontSize=12, leading=16,
        textColor=colors.white, alignment=TA_RIGHT,
    )

    total = 0.0
    for i, item in enumerate(itens or []):
        qtd = item["quantidade"] or 0
        vu = item["valor_unitario"] or 0
        valor_total = qtd * vu
        total += valor_total
        desc = (item["descricao"] or "").replace("\n", "<br/>")
        linha = Table(
            [[
                Paragraph(f"{i + 1}. {desc}", estilo_desc),
                Paragraph(formatar_moeda(valor_total) if valor_total else "—", estilo_valor),
            ]],
            colWidths=[380, 100],
        )
        linha.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7F9FC")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elementos.append(linha)
        elementos.append(Spacer(1, 8))

    rodape = Table(
        [[
            Paragraph("TOTAL DO INVESTIMENTO", estilo_total),
            Paragraph(formatar_moeda(total), estilo_total_v),
        ]],
        colWidths=[380, 100],
    )
    rodape.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LARANJA),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    elementos.append(rodape)
    elementos.append(Spacer(1, 16))
    return total
