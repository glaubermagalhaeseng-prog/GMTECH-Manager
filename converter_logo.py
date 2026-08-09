"""
Script de uso único: converte app/static/img/logo.svg em
app/static/img/logo.png, para que o gerador de PDF (reportlab,
que não lê SVG) consiga usar a logo nova.

Como usar (uma vez só, no seu PC, com o ambiente virtual ativado):

    pip install svglib --break-system-packages
    python tools/converter_logo.py

Isso vai sobrescrever app/static/img/logo.png com uma versão
em alta resolução da logo nova. Pode rodar de novo sempre que
trocar a logo.
"""

import os

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM


CAMINHO_SVG = os.path.join(
    "app", "static", "img", "logo.svg"
)

CAMINHO_PNG = os.path.join(
    "app", "static", "img", "logo.png"
)


def converter():

    if not os.path.exists(CAMINHO_SVG):
        print(f"Não encontrei {CAMINHO_SVG}. Rode este script "
              "a partir da pasta raiz do projeto (GMTECH-Sistema).")
        return

    desenho = svg2rlg(CAMINHO_SVG)

    # escala para ficar em alta resolução (fica nítido no PDF)
    desenho.width *= 3
    desenho.height *= 3
    desenho.scale(3, 3)

    renderPM.drawToFile(
        desenho,
        CAMINHO_PNG,
        fmt="PNG"
    )

    print(f"Pronto! Logo convertida para {CAMINHO_PNG}")


if __name__ == "__main__":
    converter()
