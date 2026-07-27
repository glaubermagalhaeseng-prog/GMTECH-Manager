import os

from reportlab.platypus import (
    Image,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from reportlab.lib import colors

from app.pdf.estilos import (
    titulo,
    normal,
    heading
)


def desenhar_cabecalho(elementos, proposta, empresa):

    caminho_logo = os.path.join(
        "app",
        "static",
        "img",
        "logo.png"
    )


    # ==========================
    # CABEÇALHO SUPERIOR
    # ==========================

    logo = ""

    if os.path.exists(caminho_logo):

        logo = Image(
            caminho_logo,
            width=130,
            height=55
        )


    bloco_proposta = Paragraph(
        """
        <b>PROPOSTA COMERCIAL</b><br/>
        <font size="12">
        Nº {}</font>
        """.format(proposta["id"]),
        titulo
    )


    tabela_topo = Table(
        [
            [
                logo,
                bloco_proposta
            ]
        ],
        colWidths=[220, 220]
    )


    tabela_topo.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "MIDDLE"
            ),

            (
                "ALIGN",
                (1,0),
                (1,0),
                "RIGHT"
            )
        ])
    )


    elementos.append(
        tabela_topo
    )


    elementos.append(
        Spacer(1,20)
    )


    # ==========================
    # DADOS DA EMPRESA
    # ==========================

    if empresa:

        dados_empresa = f"""
        <b>{empresa['nome_fantasia'] or ''}</b><br/>
        {empresa['razao_social'] or ''}<br/>
        CNPJ: {empresa['cnpj'] or ''}<br/>
        Responsável: {empresa['responsavel'] or ''}<br/>
        CFT: {empresa['cft'] or ''}<br/>
        Telefone: {empresa['telefone'] or ''}<br/>
        E-mail: {empresa['email'] or ''}
        """


        tabela_empresa = Table(
            [
                [
                    Paragraph(
                        dados_empresa,
                        normal
                    )
                ]
            ],
            colWidths=[440]
        )


        tabela_empresa.setStyle(
            TableStyle([
                (
                    "BOX",
                    (0,0),
                    (-1,-1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0,0),
                    (-1,-1),
                    colors.whitesmoke
                ),

                (
                    "LEFTPADDING",
                    (0,0),
                    (-1,-1),
                    10
                ),

                (
                    "RIGHTPADDING",
                    (0,0),
                    (-1,-1),
                    10
                ),

                (
                    "TOPPADDING",
                    (0,0),
                    (-1,-1),
                    8
                ),

                (
                    "BOTTOMPADDING",
                    (0,0),
                    (-1,-1),
                    8
                )
            ])
        )


        elementos.append(
            tabela_empresa
        )


    elementos.append(
        Spacer(1,20)
    )