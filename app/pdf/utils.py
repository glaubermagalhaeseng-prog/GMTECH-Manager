import os

from app.formatadores import moeda_rs


def formatar_moeda(valor):
    return moeda_rs(valor)


def _pastas_img():
    aqui = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(aqui)
    raiz = os.path.dirname(app_dir)
    return [
        os.path.join(app_dir, "static", "img"),
        os.path.join(raiz, "app", "static", "img"),
        os.path.join("app", "static", "img"),
        os.path.join("static", "img"),
    ]


def carregar_logo(largura=140):
    """Prioriza logo_nova.png (arquivo oficial), depois SVG e demais."""
    from reportlab.platypus import Image

    pastas = _pastas_img()

    # 1) PNG oficial (logo final)
    for pasta in pastas:
        for nome in ("logo_nova.png", "logo.png", "logo.jpg", "logo.jpeg"):
            caminho = os.path.join(pasta, nome)
            if not os.path.isfile(caminho):
                continue
            try:
                from PIL import Image as PILImage
                with PILImage.open(caminho) as img:
                    w, h = img.size
                    proporcao = h / float(w) if w else 0.3
                return Image(caminho, width=largura, height=largura * proporcao)
            except Exception:
                try:
                    return Image(caminho, width=largura, height=largura * 0.3)
                except Exception:
                    continue

    # 2) SVG legado
    for pasta in pastas:
        for nome in ("logo.svg", "logo.pdf.svg"):
            caminho_svg = os.path.join(pasta, nome)
            if not os.path.isfile(caminho_svg):
                continue
            try:
                from svglib.svglib import svg2rlg
                desenho = svg2rlg(caminho_svg)
                if desenho and getattr(desenho, "width", None):
                    escala = largura / float(desenho.width)
                    desenho.width = float(desenho.width) * escala
                    desenho.height = float(desenho.height) * escala
                    desenho.scale(escala, escala)
                    return desenho
            except Exception:
                continue
    return None


def gerar_qrcode(url, tamanho=90):
    """Gera um QR Code (Drawing do reportlab) apontando para 'url'."""

    from reportlab.graphics.barcode.qr import QrCodeWidget
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF

    if not url:
        return None

    widget = QrCodeWidget(url)

    caixa = widget.getBounds()
    largura_nativa = caixa[2] - caixa[0]
    altura_nativa = caixa[3] - caixa[1]

    escala_x = tamanho / largura_nativa
    escala_y = tamanho / altura_nativa

    desenho = Drawing(tamanho, tamanho, transform=[escala_x, 0, 0, escala_y, 0, 0])
    desenho.add(widget)

    return desenho


def logo_centralizada(largura=240):
    from reportlab.platypus import Table, TableStyle
    logo = carregar_logo(largura=largura)
    if not logo:
        return None
    tabela = Table([[logo]], colWidths=[500])
    tabela.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return tabela
