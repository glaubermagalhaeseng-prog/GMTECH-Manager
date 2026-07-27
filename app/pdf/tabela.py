from reportlab.lib import colors

from reportlab.platypus import (
    Table,
    TableStyle,
    Spacer
)


def formatar_moeda(valor):

    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )



def desenhar_tabela(elementos, itens):


    dados = [

        [
            "Descrição",
            "Qtd",
            "Valor Unitário",
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

                formatar_moeda(
                    item["valor_unitario"]
                ),

                formatar_moeda(
                    valor_total
                )

            ]

        )



    # linha final de total

    dados.append(

        [

            "",

            "",

            "TOTAL",

            formatar_moeda(total)

        ]

    )



    tabela = Table(

        dados,

        colWidths=[220, 50, 85, 85],

        repeatRows=1

    )



    tabela.setStyle(

        TableStyle(

            [

                (
                    "GRID",
                    (0,0),
                    (-1,-2),
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
                ),


                (
                    "BACKGROUND",
                    (0,-1),
                    (-1,-1),
                    colors.HexColor("#F7941D")
                ),


                (
                    "TEXTCOLOR",
                    (0,-1),
                    (-1,-1),
                    colors.white
                ),


                (
                    "FONTNAME",
                    (0,-1),
                    (-1,-1),
                    "Helvetica-Bold"
                )


            ]

        )

    )


    elementos.append(tabela)


    elementos.append(

        Spacer(1,20)

    )


    return total