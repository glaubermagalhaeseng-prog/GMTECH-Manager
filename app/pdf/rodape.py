from reportlab.platypus import Paragraph

from app.pdf.estilos import heading


def desenhar_total(elementos, total):

    elementos.append(
        Paragraph(
            f"<b>TOTAL DA PROPOSTA:</b> R$ {total:.2f}",
            heading
        )
    )