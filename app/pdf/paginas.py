from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether
)

from reportlab.lib import colors
from reportlab.lib.units import mm

from app.pdf.estilos import (
    AZUL,
    LARANJA,
    CINZA,
    CINZA_CLARO,
    BRANCO,
    corpo,
    corpo_centro,
    capa_titulo,
    capa_subtitulo,
    capa_linha,
    capa_info,
    secao_titulo,
    subtitulo_item,
    numero_destaque,
    rotulo_destaque,
    titulo_dois_tons
)

from app.pdf.utils import formatar_moeda, carregar_logo, logo_centralizada, gerar_qrcode
from app.formatadores import numero_br

from app.pdf.graficos import (
    grafico_retorno,
    grafico_geracao_consumo,
    grafico_rentabilidade,
    calcular_impacto_ambiental
)


# ==========================================
# PÁGINA 1 - CAPA
# ==========================================


def _path_capa_fundo():
    import os
    aqui = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.dirname(aqui)
    candidatos = [
        os.path.join(app_dir, "static", "img", "capa_fundo.png"),
        os.path.join("app", "static", "img", "capa_fundo.png"),
        os.path.join("static", "img", "capa_fundo.png"),
    ]
    for c in candidatos:
        if os.path.isfile(c):
            return c
    return None




def desenhar_capa_canva(canvas, doc):
    """
    Capa estilo Canva.
    Logo maior no topo; título e dados mais abaixo; payback moderado.
    """
    from reportlab.lib.pagesizes import A4
    from app.pdf.estilos import AZUL, LARANJA
    from app.formatadores import moeda_rs
    import os

    ctx = getattr(doc, "_capa_ctx", {}) or {}
    proposta = ctx.get("proposta") or {}
    sistema = ctx.get("sistema")

    w, h = A4
    canvas.saveState()

    # Fundo
    fundo = _path_capa_fundo()
    if fundo:
        try:
            canvas.drawImage(
                fundo, 0, 0, width=w, height=h,
                preserveAspectRatio=False, mask="auto",
            )
        except Exception:
            canvas.setFillColorRGB(0.97, 0.98, 1)
            canvas.rect(0, 0, w, h, fill=1, stroke=0)
    else:
        canvas.setFillColorRGB(0.97, 0.98, 1)
        canvas.rect(0, 0, w, h, fill=1, stroke=0)

    # Logo nova — maior
    app_img = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "static", "img",
    )
    logo_candidates = [
        os.path.join(app_img, "logo_nova.png"),
        os.path.join(app_img, "logo.png"),
        "app/static/img/logo_nova.png",
        "app/static/img/logo.png",
    ]
    logo_path = next((p for p in logo_candidates if os.path.isfile(p)), None)

    # Logo um pouco mais abaixo do topo
    logo_top = h - 55

    if logo_path:
        try:
            from PIL import Image as PILImage
            with PILImage.open(logo_path) as im:
                iw, ih = im.size
            max_w = 300
            lh = max_w * (ih / float(iw)) if iw else 90
            if lh > 115:
                lh = 115
                max_w = lh * (iw / float(ih)) if ih else 300
            x_logo = (w - max_w) / 2
            y_logo = logo_top - lh
            canvas.drawImage(
                logo_path,
                x_logo,
                y_logo,
                width=max_w,
                height=lh,
                mask="auto",
                preserveAspectRatio=True,
            )
        except Exception:
            pass

    def _get(obj, key, default=""):
        try:
            if obj is None:
                return default
            v = obj[key] if not isinstance(obj, dict) else obj.get(key)
            return v if v is not None else default
        except Exception:
            return default

    pid = _get(proposta, "id", 0)
    try:
        pid = int(pid)
    except Exception:
        pid = 0

    # Título centralizado no meio vertical da página
    y_titulo = h * 0.48
    canvas.setFillColor(AZUL)
    canvas.setFont("Helvetica-Bold", 30)
    canvas.drawCentredString(w / 2, y_titulo, "PROPOSTA")
    canvas.setFillColor(LARANJA)
    canvas.setFont("Helvetica-Bold", 26)
    canvas.drawCentredString(w / 2, y_titulo - 32, "COMERCIAL")
    canvas.setFillColor(LARANJA)
    canvas.setFont("Helvetica", 10)
    canvas.drawCentredString(w / 2, y_titulo - 52, f"PROP-{pid:04d}")

    # Bloco de dados (kWp → payback) perto da base da capa
    x = 50
    y = 210  # base do bloco; sobe conforme as linhas

    potencia = _get(sistema, "potencia_kwp", "-") if sistema else "-"
    cliente = _get(proposta, "cliente_nome", "")
    valor = _get(proposta, "valor_total", 0)

    try:
        potencia_txt = f"{float(potencia):.2f}".replace(".", ",")
    except (TypeError, ValueError):
        potencia_txt = str(potencia)

    endereco_partes = [
        p for p in [
            _get(proposta, "cliente_rua"),
            _get(proposta, "cliente_numero_endereco") or _get(proposta, "cliente_numero"),
            _get(proposta, "cliente_bairro"),
            _get(proposta, "cliente_cidade"),
            _get(proposta, "cliente_uf"),
        ] if p
    ]
    endereco = ", ".join(str(p) for p in endereco_partes)

    # altura aproximada do bloco (kWp → payback) para ancorar perto da base
    alt = 18 + 16  # kWp + cliente
    if valor:
        alt += 15
    if endereco:
        alt += 24 if len(endereco) > 70 else 12
    alt += 12 + 12 + 18  # data + validade + folga
    alt += 16 + 18  # payback (rótulo + valor)
    y = 48 + alt  # base do bloco ~48 pt acima da margem inferior

    canvas.setFillColor(AZUL)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawString(x, y, f"{potencia_txt} kWp")
    y -= 18
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(x, y, str(cliente))
    y -= 16

    if valor:
        try:
            canvas.setFont("Helvetica-Bold", 12)
            canvas.drawString(x, y, f"Investimento: {moeda_rs(valor)}")
            y -= 15
        except Exception:
            pass

    canvas.setFont("Helvetica", 10)
    if endereco:
        if len(endereco) > 70:
            canvas.drawString(x, y, endereco[:70])
            y -= 12
            canvas.drawString(x, y, endereco[70:140])
            y -= 12
        else:
            canvas.drawString(x, y, endereco)
            y -= 12

    data = _get(proposta, "data", "")
    validade = _get(proposta, "validade", "") or "15 dias"
    canvas.drawString(x, y, f"Data: {data}")
    y -= 12
    canvas.drawString(x, y, f"Validade: {validade}")
    y -= 18

    # Payback
    try:
        eco = float(_get(sistema, "economia_mensal", 0) or 0) if sistema else 0
        inv = float(valor or 0)
        if eco > 0 and inv > 0:
            anos = (inv / eco) / 12.0
            anos_txt = f"{anos:.1f}".replace(".", ",")
            canvas.setFillColor(LARANJA)
            canvas.setFont("Helvetica-Bold", 10)
            canvas.drawString(x, y, "PAYBACK ESTIMADO")
            y -= 16
            canvas.setFillColor(AZUL)
            canvas.setFont("Helvetica-Bold", 18)
            canvas.drawString(x, y, f"{anos_txt} anos")
    except Exception:
        pass

    canvas.restoreState()



def desenhar_tracos_capa(canvas, doc):
    """Compat: redireciona para capa Canva completa."""
    desenhar_capa_canva(canvas, doc)


def rodape_e_marca_dagua(canvas, doc):
    """
    Callback para as páginas 2+ (onLaterPages):
    - rodapé com nome do cliente + número da página
    - marca d'água "RASCUNHO" quando a proposta está com esse status
    """
    from reportlab.lib.pagesizes import A4

    w, h = A4
    canvas.saveState()

    # ------- rodapé -------
    cliente_nome = getattr(doc, "_rodape_cliente", "") or ""
    numero_proposta = getattr(doc, "_rodape_numero", "") or ""

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CINZA)

    if cliente_nome:
        canvas.drawString(45, 25, f"{cliente_nome} — {numero_proposta}")

    canvas.drawRightString(w - 45, 25, f"Página {canvas.getPageNumber()}")

    canvas.setStrokeColor(CINZA_CLARO)
    canvas.setLineWidth(0.6)
    canvas.line(45, 34, w - 45, 34)

    # ------- marca d'água "RASCUNHO" -------
    if getattr(doc, "_rodape_rascunho", False):

        canvas.saveState()
        canvas.translate(w / 2, h / 2)
        canvas.rotate(38)
        canvas.setFont("Helvetica-Bold", 90)
        canvas.setFillColor(CINZA)
        try:
            canvas.setFillAlpha(0.14)
        except Exception:
            pass
        canvas.drawCentredString(0, 0, "RASCUNHO")
        canvas.restoreState()

    canvas.restoreState()


def pagina_capa(elementos, proposta, sistema, empresa):
    """
    A capa visual é desenhada no canvas (onFirstPage).
    Aqui só reserva a página e pula para o conteúdo.
    """
    # Espaço “vazio” ocupa a 1ª página; o desenho real está no canvas.
    elementos.append(Spacer(1, 700))
    elementos.append(PageBreak())


# ==========================================
# PÁGINA 2 - COMO FUNCIONA
# ==========================================

def pagina_como_funciona(elementos):

    elementos.append(
        Paragraph(
            titulo_dois_tons("COMO", "FUNCIONA?"),
            secao_titulo
        )
    )

    elementos.append(Spacer(1, 20))

    conceitos = [
        (
            "ENERGIA GERADA",
            "É o total de energia que o seu sistema fotovoltaico "
            "produziu no período da medição."
        ),
        (
            "AUTOCONSUMO",
            "É a energia consumida em tempo real, no momento em "
            "que ela é gerada pelo sistema."
        ),
        (
            "ENERGIA INJETADA",
            "É a energia que sobra da geração solar e é injetada "
            "na rede, virando crédito na concessionária."
        ),
        (
            "ENERGIA CONSUMIDA DA REDE",
            "É a energia puxada da rede elétrica durante a noite "
            "ou quando o consumo é maior que a geração solar."
        )
    ]

    linhas = []

    for titulo_conceito, texto in conceitos:

        linhas.append([
            Paragraph(
                f'<font color="#F7941D">●</font> '
                f'<b>{titulo_conceito}</b>',
                subtitulo_item
            ),
            Paragraph(texto, corpo)
        ])

    tabela = Table(
        linhas,
        colWidths=[150, 300]
    )

    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
            ("TOPPADDING", (0, 0), (-1, -1), 4)
        ])
    )

    elementos.append(tabela)

    elementos.append(Spacer(1, 20))

    elementos.append(
        Paragraph(
            "Resumindo: durante o dia, sua casa consome a energia que "
            "o sistema está gerando. O que sobra vira crédito. À "
            "noite, ou nos dias de pouco sol, você usa esse crédito "
            "acumulado em vez de pagar pela energia da rede.",
            corpo
        )
    )

    elementos.append(Spacer(1, 26))


# ==========================================
# PÁGINA 3 - SEU PROJETO
# ==========================================

def pagina_projeto(elementos, sistema, proposta):

    elementos.append(
        Paragraph(titulo_dois_tons("SEU", "PROJETO"), secao_titulo)
    )

    elementos.append(Spacer(1, 20))

    if not sistema:

        elementos.append(
            Paragraph(
                "Nenhum sistema fotovoltaico foi cadastrado nesta "
                "proposta ainda.",
                corpo
            )
        )

        elementos.append(PageBreak())

        return


    # área mínima estimada (aprox. 2,6 m² por módulo)
    area_minima = round((sistema["quantidade_modulos"] or 0) * 2.6, 2)

    itens_specs = [
        (
            "Potência",
            f"Potência do sistema: {numero_br(sistema['potencia_kwp'])} kWp"
        ),
        (
            "Inversor",
            f"Inversor {sistema['modelo_inversor'] or ''} "
            f"({numero_br(sistema['potencia_inversor'] or 0)} kW)"
        ),
        (
            "Módulos",
            f"{sistema['quantidade_modulos']} Módulos Solares "
            f"{sistema['potencia_modulo']}W "
            f"{sistema['fabricante_modulo'] or ''}"
        ),
        (
            "Geração",
            f"Geração estimada mensal de "
            f"{numero_br(sistema['geracao_mensal'] or 0)} kWh/mês"
        ),
        (
            "Economia",
            f"Economia de {formatar_moeda(sistema['economia_mensal'])} "
            "por mês"
        ),
        (
            "Área",
            f"Área mínima estimada: {numero_br(area_minima)} m<super>2</super>"
        )
    ]

    linhas = []

    for icone, texto in itens_specs:

        linhas.append([
            Paragraph(
                f'<font color="#F7941D">●</font>',
                corpo
            ),
            Paragraph(texto, corpo)
        ])

    tabela = Table(linhas, colWidths=[20, 420])

    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10)
        ])
    )

    elementos.append(tabela)

    elementos.append(Spacer(1, 14))

    if sistema["observacoes"]:

        elementos.append(
            Paragraph(f"<i>{sistema['observacoes']}</i>", corpo)
        )

        elementos.append(Spacer(1, 12))


    bloco_garantias = []

    bloco_garantias.append(
        Paragraph(titulo_dois_tons("", "GARANTIAS", tamanho=16), secao_titulo)
    )

    bloco_garantias.append(Spacer(1, 8))

    dados_garantia = [
        ["EQUIPAMENTO", "GARANTIA"],
        ["Módulos solares", "12 anos*"],
        ["Inversores", "10 anos"],
        ["Estrutura", "10 anos"],
        ["Instalação", "1 ano"],
    ]

    tabela_garantia = Table(dados_garantia, colWidths=[220, 220])
    # não permite quebrar linhas da tabela entre páginas
    tabela_garantia.splitByRow = 0

    tabela_garantia.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), CINZA_CLARO),
            ("TEXTCOLOR", (0, 0), (-1, 0), CINZA),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("GRID", (0, 0), (-1, -1), 0.4, CINZA_CLARO),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    bloco_garantias.append(tabela_garantia)

    bloco_garantias.append(Spacer(1, 6))

    bloco_garantias.append(
        Paragraph(
            "*25 anos com eficiência mínima de 80%.",
            rotulo_destaque
        )
    )

    elementos.append(KeepTogether(bloco_garantias))

    elementos.append(Spacer(1, 18))


# ==========================================
# PÁGINA 4 - INVESTIMENTO E ECONOMIA
# ==========================================

def pagina_investimento_economia(elementos, proposta, sistema):

    elementos.append(
        Paragraph(titulo_dois_tons("SEU", "INVESTIMENTO"), secao_titulo)
    )

    elementos.append(Spacer(1, 10))

    elementos.append(
        Paragraph(
            f"<b>{formatar_moeda(proposta['valor_total'])}</b>",
            capa_linha
        )
    )

    if sistema and sistema.get("economia_mensal") and proposta.get("valor_total"):
        try:
            eco = float(sistema["economia_mensal"] or 0)
            inv = float(proposta["valor_total"] or 0)
            if eco > 0 and inv > 0:
                anos = (inv / eco) / 12.0
                anos_txt = f"{anos:.1f}".replace(".", ",")
                elementos.append(Spacer(1, 8))
                elementos.append(
                    Paragraph(
                        f"Payback estimado: <b>{anos_txt} anos</b> · "
                        f"Economia mensal estimada: <b>{formatar_moeda(eco)}</b>",
                        corpo,
                    )
                )
        except Exception:
            pass

    elementos.append(Spacer(1, 12))

    elementos.append(
        Paragraph(
            "Consulte-nos sobre opções de financiamento junto às "
            "principais instituições financeiras. Simulação sujeita "
            "à análise de crédito. Valores sujeitos à alteração.",
            corpo
        )
    )

    elementos.append(Spacer(1, 12))

    elementos.append(
        Paragraph(
            "<i>Para o correto dimensionamento e precificação do seu "
            "projeto é fundamental a nossa visita técnica, já que a "
            "face e a inclinação do telhado podem alterar a geração "
            "de energia do sistema. Também avaliamos as condições da "
            "estrutura física e elétrica, podendo ser necessárias "
            "adequações para a segurança e a correta homologação "
            "junto à concessionária.</i>",
            corpo
        )
    )

    elementos.append(Spacer(1, 30))

    elementos.append(
        Paragraph(titulo_dois_tons("SUA", "ECONOMIA"), secao_titulo)
    )

    elementos.append(Spacer(1, 15))

    if sistema:

        valor_atual = sistema["valor_conta_atual"] or 0

        valor_residual = sistema["valor_conta_residual"]

        if not valor_residual:

            valor_residual = max(
                0,
                valor_atual - (sistema["economia_mensal"] or 0)
            )

        economia_mensal = valor_atual - valor_residual

        dados = [
            [
                "Sua conta de energia\nsem Energia Solar",
                "Sua conta de energia\ncom Energia Solar",
                "Sua economia será de:"
            ],
            [
                formatar_moeda(valor_atual * 12) + " / ano",
                formatar_moeda(valor_residual * 12) + " / ano",
                formatar_moeda(economia_mensal * 12) + " / ano"
            ],
            [
                formatar_moeda(valor_atual) + " / mês",
                formatar_moeda(valor_residual) + " / mês",
                formatar_moeda(economia_mensal) + " / mês"
            ]
        ]

        tabela = Table(dados, colWidths=[150, 150, 150])

        tabela.setStyle(
            TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TEXTCOLOR", (0, 0), (-1, 0), CINZA),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("TEXTCOLOR", (0, 1), (-1, 1), AZUL),
                ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 1), (-1, 1), 11),
                ("TEXTCOLOR", (0, 2), (-1, 2), colors.HexColor("#555555")),
                ("FONTSIZE", (0, 2), (-1, 2), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6)
            ])
        )

        elementos.append(tabela)

    else:

        elementos.append(
            Paragraph(
                "Cadastre um sistema fotovoltaico nesta proposta para "
                "calcular a economia estimada.",
                corpo
            )
        )

    elementos.append(Spacer(1, 26))


# ==========================================
# PÁGINA 5 - RETORNO, RENTABILIDADE,
# GERAÇÃO E IMPACTO AMBIENTAL
# ==========================================

def pagina_retorno(elementos, proposta, sistema):

    if not sistema:
        return

    elementos.append(
        Paragraph(titulo_dois_tons("SEU", "RETORNO"), secao_titulo)
    )

    elementos.append(
        Paragraph(
            "Retorno acumulado ao longo de 25 anos (economia gerada "
            "menos o investimento). Em vermelho, o período antes do "
            "payback; em verde, a partir do momento em que o sistema "
            "já se pagou.",
            corpo
        )
    )

    elementos.append(Spacer(1, 10))

    elementos.append(
        grafico_retorno(
            proposta["valor_total"],
            sistema["economia_mensal"]
        )
    )

    elementos.append(Spacer(1, 24))

    # Capacidade de geração começa em página nova
    elementos.append(PageBreak())

    elementos.append(
        Paragraph(
            titulo_dois_tons("CAPACIDADE DE", "GERAÇÃO"),
            secao_titulo
        )
    )

    elementos.append(
        Paragraph(
            "Energia gerada x consumida (kWh/mês) — estimativa com "
            "base na média informada, aplicando variação sazonal "
            "típica da região.",
            corpo
        )
    )

    elementos.append(Spacer(1, 4))

    elementos.append(
        Paragraph(
            '<font color="#198754">■</font> Geração estimada &nbsp;&nbsp;&nbsp; '
            '<font color="#D64545">■</font> Consumo médio informado',
            rotulo_destaque
        )
    )

    elementos.append(Spacer(1, 6))

    elementos.append(grafico_geracao_consumo(sistema["geracao_mensal"]))

    elementos.append(Spacer(1, 14))

    impacto = calcular_impacto_ambiental(sistema["geracao_mensal"])

    dados_impacto = [
        [
            Paragraph(f"{impacto['arvores']}", numero_destaque),
            Paragraph(numero_br(impacto['co2_toneladas']), numero_destaque),
            Paragraph(f"{impacto['km_carro_evitados']:,}".replace(",", "."), numero_destaque)
        ],
        [
            Paragraph("Árvores equivalentes\npreservadas", rotulo_destaque),
            Paragraph("toneladas de CO2\nnão emitidas", rotulo_destaque),
            Paragraph("km não rodados\npor um carro a combustão", rotulo_destaque)
        ]
    ]

    tabela_impacto = Table(dados_impacto, colWidths=[150, 150, 150])

    tabela_impacto.setStyle(
        TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4)
        ])
    )

    elementos.append(tabela_impacto)

    elementos.append(Spacer(1, 10))

    elementos.append(
        Paragraph(
            "Estimativas calculadas ao longo de 25 anos de geração, "
            "com base em fatores médios de emissão. Valores "
            "aproximados, apenas para fins ilustrativos.",
            rotulo_destaque
        )
    )

    elementos.append(Spacer(1, 12))


# ==========================================
# PÁGINA 6 - NÓS CUIDAMOS DE TUDO
# ==========================================

def pagina_processo(elementos):

    bloco = []

    bloco.append(
        Paragraph(
            titulo_dois_tons("NÓS CUIDAMOS DE TUDO", "PRA VOCÊ", tamanho=18),
            secao_titulo
        )
    )

    bloco.append(Spacer(1, 12))

    etapas = [
        ("1", "Projeto", "Desenvolvido pelo nosso time de engenheiros, atendendo todas as exigências normativas."),
        ("2", "Logística", "Cuidamos para que o equipamento chegue com segurança até o local da instalação."),
        ("3", "Instalação", "Agendamos a instalação para um momento conveniente à sua rotina."),
        ("4", "Homologação", "Cuidamos de toda a papelada junto à concessionária de energia."),
        ("5", "Monitoramento", "Acompanhamos a geração do seu sistema para identificar possíveis falhas."),
        ("6", "Manutenção", "Conheça nossos planos de manutenção e operação continuada."),
    ]

    linhas = []

    for numero, nome_etapa, texto in etapas:

        linhas.append([
            Paragraph(f'<font color="#F7941D" size="14"><b>{numero}</b></font>', corpo),
            Paragraph(
                f"<b>{nome_etapa}</b><br/>{texto}",
                corpo
            )
        ])

    tabela = Table(linhas, colWidths=[28, 402])
    # impede que a última etapa (Manutenção) fique sozinha na próxima página
    tabela.splitByRow = 0

    tabela.setStyle(
        TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    bloco.append(tabela)

    elementos.append(KeepTogether(bloco))

    elementos.append(Spacer(1, 14))


# ==========================================
# PÁGINA 7 - NOSSAS SOLUÇÕES (GALERIA)
# ==========================================

def pagina_solucoes():
    """
    Retorna os elementos da seção "Nossas Soluções".
    Por enquanto fica como um espaço reservado, pronto
    para receber fotos reais de projetos futuramente
    (ver app/pdf/paginas.py -> adicionar_fotos_solucoes).
    """

    elementos = []

    elementos.append(
        Paragraph(titulo_dois_tons("NOSSAS", "SOLUÇÕES"), secao_titulo)
    )

    elementos.append(
        Paragraph(
            "Economize até 95% com nossas soluções",
            corpo
        )
    )

    elementos.append(Spacer(1, 20))

    caixa = Table(
        [[
            Paragraph(
                "📷<br/><br/>"
                "Em breve: fotos dos projetos já realizados "
                "pela GMTECH aparecerão aqui.",
                corpo_centro
            )
        ]],
        colWidths=[440],
        rowHeights=[140]
    )

    caixa.setStyle(
        TableStyle([
            ("BOX", (0, 0), (-1, -1), 1, CINZA),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER")
        ])
    )

    elementos.append(caixa)

    elementos.append(PageBreak())

    return elementos


# ==========================================
# PÁGINA 8 - POR QUE ESCOLHER + CONTATO
# ==========================================

def pagina_sobre_contato(elementos, empresa, link_assinatura=None):
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from app.pdf.estilos import AZUL, LARANJA, CINZA, corpo, corpo_centro, secao_titulo

    nome_empresa = (
        empresa["nome_fantasia"] if empresa and empresa["nome_fantasia"]
        else "GMTECH Soluções Elétricas"
    )

    elementos.append(
        Paragraph(
            titulo_dois_tons("POR QUE ESCOLHER", f"A {nome_empresa.upper()}?", tamanho=18),
            secao_titulo,
        )
    )
    elementos.append(Spacer(1, 16))

    # Texto sem repetir o nome da empresa (só no título)
    texto_marca = ParagraphStyle(
        "texto_marca",
        parent=corpo,
        textColor=AZUL,
        fontSize=11,
        leading=16,
    )
    elementos.append(
        Paragraph(
            "Somos uma empresa de soluções em energia solar "
            "comprometida com a qualidade técnica, a transparência "
            "e o atendimento próximo ao cliente. Cuidamos de todo o "
            "processo — do dimensionamento à homologação — para que "
            "você só precise se preocupar em economizar.",
            texto_marca,
        )
    )
    elementos.append(Spacer(1, 28))

    estilo_pilar_t = ParagraphStyle(
        "pilar_t", parent=corpo_centro, textColor=LARANJA,
        fontName="Helvetica-Bold", fontSize=12, leading=15,
    )
    estilo_pilar_d = ParagraphStyle(
        "pilar_d", parent=corpo_centro, textColor=AZUL,
        fontSize=9, leading=13,
    )

    pilares = [
        ("INOVAÇÃO", "Projetos com as melhores soluções técnicas disponíveis."),
        ("EFICIÊNCIA", "Equipe de profissionais altamente qualificados."),
        ("RESPEITO", "Compromisso com você e com o meio ambiente."),
    ]
    celulas = []
    for nome, texto in pilares:
        celulas.append([
            Paragraph(nome, estilo_pilar_t),
            Paragraph(texto, estilo_pilar_d),
        ])
    # 3 colunas lado a lado
    linha = [[celulas[0][0], celulas[1][0], celulas[2][0]],
             [celulas[0][1], celulas[1][1], celulas[2][1]]]
    # simpler: one row of stacked paragraphs
    linha = [[
        Paragraph(f"<b>{n}</b><br/>{t}", ParagraphStyle(
            f"px{i}", parent=corpo_centro, textColor=AZUL, fontSize=10, leading=13,
        ))
        for i, (n, t) in enumerate(pilares)
    ]]
    # color titles orange via separate approach
    linha = [[
        Paragraph(
            f'<font color="#F7941D"><b>{n}</b></font><br/><font color="#073B4C">{t}</font>',
            corpo_centro,
        )
        for n, t in pilares
    ]]

    tabela_pilares = Table(linha, colWidths=[155, 155, 155])
    tabela_pilares.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    elementos.append(tabela_pilares)

    # ------- CONTA RESIDUAL + ACEITE (página final, antes do contato) -------
    elementos.append(PageBreak())
    elementos.append(
        Paragraph(titulo_dois_tons("CONTA", "RESIDUAL", tamanho=20), secao_titulo)
    )
    elementos.append(Spacer(1, 12))
    elementos.append(
        Paragraph(
            "Após a instalação do sistema, a conta de energia normalmente "
            "<b>não zera por completo</b>. Permanecem valores como:",
            corpo,
        )
    )
    elementos.append(Spacer(1, 8))
    residual_itens = [
        "• Contribuição de Iluminação Pública (CIP) — taxa municipal",
        "• Custo de disponibilidade (30, 50 ou 100 kWh, conforme o tipo de ligação)",
        "• Parcela do Fio B (Lei 14.300), quando aplicável à data de conexão",
        "• Impostos incidentes sobre os valores ainda faturados",
    ]
    for linha in residual_itens:
        elementos.append(Paragraph(linha, corpo))
        elementos.append(Spacer(1, 3))

    elementos.append(Spacer(1, 24))
    elementos.append(
        Paragraph(titulo_dois_tons("ACEITE DA", "PROPOSTA", tamanho=20), secao_titulo)
    )
    elementos.append(Spacer(1, 10))
    elementos.append(
        Paragraph(
            "Declaro que li e concordo com as condições comerciais e técnicas "
            "desta proposta de sistema fotovoltaico.",
            corpo,
        )
    )

    qrcode = gerar_qrcode(link_assinatura, tamanho=85) if link_assinatura else None

    if qrcode:

        elementos.append(Spacer(1, 16))

        bloco_qr = Table(
            [[
                qrcode,
                Paragraph(
                    "<b>Prefere assinar pelo celular?</b><br/>"
                    "Aponte a câmera para o QR Code ao lado, ou acesse o "
                    f"link abaixo, para assinar digitalmente sem precisar "
                    "imprimir:<br/>"
                    f'<font color="#073B4C">{link_assinatura}</font>',
                    corpo
                )
            ]],
            colWidths=[95, 345]
        )

        bloco_qr.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), CINZA_CLARO),
                ("LEFTPADDING", (0, 0), (0, 0), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ])
        )

        elementos.append(bloco_qr)

        elementos.append(Spacer(1, 14))

        elementos.append(
            Paragraph(
                "Ou, se preferir, preencha e assine à mão:",
                corpo
            )
        )

    elementos.append(Spacer(1, 16))
    elementos.append(Paragraph("Nome: _______________________________________________", corpo))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("CPF/CNPJ: ___________________________________________", corpo))
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph("Data: ____/____/________", corpo))
    elementos.append(Spacer(1, 20))
    elementos.append(Paragraph("Assinatura: _________________________________________", corpo))

    # ------- CONTATO (centralizado: só WhatsApp + e-mail) -------
    elementos.append(Spacer(1, 28))
    elementos.append(
        Paragraph(titulo_dois_tons("ENTRE EM", "CONTATO", tamanho=22), secao_titulo)
    )
    elementos.append(Spacer(1, 14))

    estilo_dado = ParagraphStyle(
        "contato_dado", parent=corpo_centro, textColor=AZUL,
        fontSize=12, leading=18, alignment=TA_CENTER,
    )

    telefone = (empresa or {}).get("telefone") if empresa else None
    # e-mail oficial da GMTECH (fallback se cadastro da empresa estiver vazio/errado)
    email = ((empresa or {}).get("email") if empresa else None) or "glaubermagalhaeseng@gmail.com"
    if email and str(email).strip().lower() in ("", "none", "null"):
        email = "glaubermagalhaeseng@gmail.com"

    if telefone:
        elementos.append(Paragraph(f"WhatsApp / Tel: {telefone}", estilo_dado))
        elementos.append(Spacer(1, 6))
    elementos.append(Paragraph(str(email), estilo_dado))

