from fastapi.responses import FileResponse
from app.pdf.gerador import gerar_pdf_proposta
import os
from datetime import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import conectar


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =========================
# NOVA PROPOSTA
# =========================

@router.get("/propostas/nova")
async def nova_proposta(request: Request):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """)

    clientes = cursor.fetchall()


    cursor.execute("""
        SELECT *
        FROM servicos
        ORDER BY descricao
    """)

    servicos = cursor.fetchall()


    itens = request.session.get(
        "itens_proposta",
        []
    )


    total = sum(
        item["quantidade"] * item["valor"]
        for item in itens
    )


    cliente_selecionado = request.session.get(
        "cliente_id"
    )


    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="nova_proposta.html",
        context={
            "clientes": clientes,
            "servicos": servicos,
            "itens": itens,
            "total": total,
            "cliente_selecionado": cliente_selecionado
        }
    )



# =========================
# SELECIONAR CLIENTE
# =========================

@router.post("/propostas/selecionar-cliente")
async def selecionar_cliente(
    request: Request,
    cliente_id: int = Form(...)
):

    request.session["cliente_id"] = cliente_id


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )



# =========================
# ADICIONAR ITEM
# =========================

@router.post("/propostas/adicionar-item")
async def adicionar_item(
    request: Request,
    servico_id: int = Form(...),
    quantidade: float = Form(...),
    valor: float = Form(...)
):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT descricao
        FROM servicos
        WHERE id = ?
    """, (servico_id,))


    servico = cursor.fetchone()


    conn.close()


    itens = request.session.get(
        "itens_proposta",
        []
    )


    itens.append({

        "servico_id": servico_id,

        "descricao": servico["descricao"],

        "quantidade": quantidade,

        "valor": valor

    })


    request.session["itens_proposta"] = itens


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )



# =========================
# REMOVER ITEM
# =========================

@router.get("/propostas/remover-item/{item_id}")
async def remover_item(
    request: Request,
    item_id: int
):

    itens = request.session.get(
        "itens_proposta",
        []
    )


    if 0 <= item_id < len(itens):

        itens.pop(item_id)


    request.session["itens_proposta"] = itens


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )



# =========================
# SALVAR PROPOSTA
# =========================

@router.post("/propostas/salvar")
async def salvar_proposta(
    request: Request
):

    cliente_id = request.session.get(
        "cliente_id"
    )


    itens = request.session.get(
        "itens_proposta",
        []
    )


    if not cliente_id or not itens:

        return RedirectResponse(
            "/propostas/nova",
            status_code=303
        )


    total = sum(
        item["quantidade"] * item["valor"]
        for item in itens
    )


    conn = conectar()
    cursor = conn.cursor()



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

        VALUES

        (?,?,?,?,?,?)

    """,

    (

        cliente_id,

        datetime.now().strftime("%d/%m/%Y"),

        total,

        "Aberta",

        "15 dias",

        ""

    ))



    proposta_id = cursor.lastrowid



    for item in itens:


        cursor.execute("""

            INSERT INTO itens_proposta

            (

                proposta_id,

                servico_id,

                descricao,

                quantidade,

                valor_unitario

            )

            VALUES

            (?,?,?,?,?)

        """,

        (

            proposta_id,

            item["servico_id"],

            item["descricao"],

            item["quantidade"],

            item["valor"]

        ))



    conn.commit()

    conn.close()



    request.session.pop(
        "itens_proposta",
        None
    )


    request.session.pop(
        "cliente_id",
        None
    )


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )

@router.get("/propostas")
async def listar_propostas(request: Request):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT 
        propostas.id,
        propostas.data,
        propostas.status,
        clientes.nome AS cliente_nome,
        SUM(itens_proposta.quantidade * itens_proposta.valor_unitario) AS valor_total

    FROM propostas

    INNER JOIN clientes

    ON propostas.cliente_id = clientes.id


    LEFT JOIN itens_proposta

    ON propostas.id = itens_proposta.proposta_id


    GROUP BY propostas.id


    ORDER BY propostas.id DESC
""")


    propostas = cursor.fetchall()


    conn.close()


    return templates.TemplateResponse(

        request=request,

        name="propostas.html",

        context={

            "propostas": propostas

        }

    )

# =========================
# GERAR PDF DA PROPOSTA
# =========================

@router.get("/propostas/{proposta_id}/pdf")
async def gerar_pdf(
    proposta_id: int
):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT 
            propostas.*,

            clientes.nome AS cliente_nome,
            clientes.telefone AS cliente_telefone,
            clientes.email AS cliente_email,
            clientes.cidade AS cliente_cidade,
            clientes.uf AS cliente_uf

        FROM propostas

        INNER JOIN clientes

        ON propostas.cliente_id = clientes.id

        WHERE propostas.id = ?
    """, (proposta_id,))

    proposta = cursor.fetchone()

    print(dict(proposta))



    cursor.execute("""
        SELECT *

        FROM itens_proposta

        WHERE proposta_id = ?

    """, (proposta_id,))


    itens = cursor.fetchall()


    conn.close()



    caminho = f"proposta_{proposta_id}.pdf"



    gerar_pdf_proposta(

        caminho,

        proposta,

        itens

    )



    return FileResponse(

        caminho,

        media_type="application/pdf",

        filename=caminho

    )

# =========================
# VISUALIZAR PROPOSTA
# =========================

@router.get("/propostas/{proposta_id}")
async def visualizar_proposta(
    request: Request,
    proposta_id: int
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        propostas.*,

        clientes.nome AS cliente_nome,
        clientes.telefone AS cliente_telefone,
        clientes.email AS cliente_email,
        clientes.cidade AS cliente_cidade,
        clientes.uf AS cliente_uf

FROM propostas

INNER JOIN clientes

ON propostas.cliente_id = clientes.id

WHERE propostas.id = ?
    """, (proposta_id,))

    proposta = cursor.fetchone()

    

    cursor.execute("""
        SELECT *

        FROM itens_proposta

        WHERE proposta_id = ?
    """, (proposta_id,))

    itens = cursor.fetchall()

    conn.close()


    return templates.TemplateResponse(

        request=request,

        name="visualizar_proposta.html",

        context={

            "proposta": proposta,

            "itens": itens

        }

    )