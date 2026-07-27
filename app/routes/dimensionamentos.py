from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from datetime import datetime

from app.database import conectar


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)



# ==========================================
# LISTAR DIMENSIONAMENTOS
# ==========================================

@router.get("/dimensionamentos")
async def listar_dimensionamentos(request: Request):


    conn = conectar()

    cursor = conn.cursor()



    cursor.execute("""
        SELECT

            dimensionamentos_solares.*,

            clientes.nome AS cliente_nome


        FROM dimensionamentos_solares


        INNER JOIN clientes

        ON dimensionamentos_solares.cliente_id = clientes.id


        ORDER BY dimensionamentos_solares.id DESC

    """)



    dimensionamentos = cursor.fetchall()



    conn.close()



    return templates.TemplateResponse(

        request=request,

        name="dimensionamentos.html",

        context={

            "dimensionamentos": dimensionamentos

        }

    )

# ==========================================
# VISUALIZAR DIMENSIONAMENTO
# ==========================================

@router.get("/dimensionamentos/{dimensionamento_id}")
async def visualizar_dimensionamento(
    request: Request,
    dimensionamento_id: int
):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            dimensionamentos_solares.*,

            clientes.nome AS cliente_nome,
            clientes.telefone AS cliente_telefone,
            clientes.email AS cliente_email


        FROM dimensionamentos_solares


        INNER JOIN clientes

        ON dimensionamentos_solares.cliente_id = clientes.id


        WHERE dimensionamentos_solares.id = ?

    """, (dimensionamento_id,))


    dimensionamento = cursor.fetchone()


    conn.close()


    return templates.TemplateResponse(

        request=request,

        name="visualizar_dimensionamento.html",

        context={

            "dimensionamento": dimensionamento

        }

    )

# ==========================================
# GERAR PROPOSTA A PARTIR DO DIMENSIONAMENTO
# ==========================================

@router.get("/dimensionamentos/{dimensionamento_id}/gerar-proposta")
async def gerar_proposta_dimensionamento(
    dimensionamento_id: int
):

    conn = conectar()

    cursor = conn.cursor()


    # Busca dimensionamento

    cursor.execute("""
        SELECT *
        FROM dimensionamentos_solares
        WHERE id = ?
    """, (dimensionamento_id,))


    dimensionamento = cursor.fetchone()



    if not dimensionamento:

        conn.close()

        return RedirectResponse(
            "/dimensionamentos",
            status_code=303
        )



    # Cria proposta

    cursor.execute("""
        INSERT INTO propostas

        (
            cliente_id,
            data,
            valor_total,
            status,
            validade,
            observacoes
        )

        VALUES (?,?,?,?,?,?)

    """,

    (

        dimensionamento["cliente_id"],

        datetime.now().strftime("%d/%m/%Y"),

        0,

        "Orçamento",

        "15 dias",

        "Proposta gerada pelo dimensionador solar"

    ))



    proposta_id = cursor.lastrowid



    # Item sistema solar

    cursor.execute("""
        INSERT INTO itens_proposta

        (
            proposta_id,
            descricao,
            quantidade,
            valor_unitario
        )

        VALUES (?,?,?,?)

    """,

    (

        proposta_id,

        f"Sistema Fotovoltaico {dimensionamento['potencia_final_kwp']} kWp",

        1,

        0

    ))



    # Item módulos

    cursor.execute("""
        INSERT INTO itens_proposta

        (
            proposta_id,
            descricao,
            quantidade,
            valor_unitario
        )

        VALUES (?,?,?,?)

    """,

    (

        proposta_id,

        f"Módulo {dimensionamento['fabricante_modulo']} {dimensionamento['modelo_modulo']}",

        dimensionamento["quantidade_modulos"],

        0

    ))



    # Item inversor

    cursor.execute("""
        INSERT INTO itens_proposta

        (
            proposta_id,
            descricao,
            quantidade,
            valor_unitario
        )

        VALUES (?,?,?,?)

    """,

    (

        proposta_id,

        f"Inversor {dimensionamento['fabricante_inversor']} {dimensionamento['modelo_inversor']}",

        1,

        0

    ))



    conn.commit()

    conn.close()



    return RedirectResponse(

        f"/propostas/{proposta_id}",

        status_code=303

    )