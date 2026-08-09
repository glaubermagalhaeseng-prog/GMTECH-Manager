from reportlab.platypus import Paragraph

from app.pdf.estilos import heading
from app.formatadores import moeda_rs


def desenhar_total(elementos, total):

    elementos.append(
        Paragraph(
            f"<b>TOTAL DA PROPOSTA:</b> {moeda_rs(total)}",
            heading
        )
    )
