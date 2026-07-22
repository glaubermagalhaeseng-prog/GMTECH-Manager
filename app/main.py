from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.routes import clientes
from app.routes import servicos
from starlette.middleware.sessions import SessionMiddleware

from app.database import (
    conectar,
    criar_tabela_clientes,
    criar_tabela_servicos,
    criar_tabela_propostas
)


app = FastAPI(title="GMTECH Manager")

app.include_router(clientes.router)
app.include_router(servicos.router)


app.add_middleware(
    SessionMiddleware,
    secret_key="gmtech-secret-key"
)


templates = Jinja2Templates(directory="app/templates")


criar_tabela_clientes()
criar_tabela_servicos()
criar_tabela_propostas()



# =========================
# INICIO
# =========================


@app.get("/")
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )






    # =========================
# PROPOSTAS
# =========================


@app.get("/propostas/nova")
async def nova_proposta(request: Request):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM clientes
        ORDER BY nome
        """
    )

    clientes = cursor.fetchall()


    cursor.execute(
        """
        SELECT *
        FROM servicos
        ORDER BY descricao
        """
    )

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





@app.post("/propostas/adicionar-item")
async def adicionar_item(
    request: Request,
    servico_id: int = Form(...),
    quantidade: int = Form(...),
    valor: float = Form(...)
):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT id, descricao
        FROM servicos
        WHERE id = ?
        """,
        (servico_id,)
    )


    servico = cursor.fetchone()


    conn.close()


    itens = request.session.get(
        "itens_proposta",
        []
    )


    itens.append(

        {

            "servico_id": servico[0],

            "servico": servico[1],

            "quantidade": quantidade,

            "valor": valor

        }

    )


    request.session["itens_proposta"] = itens


    return RedirectResponse(

        url="/propostas/nova",

        status_code=303

    )

@app.post("/propostas/selecionar-cliente")
async def selecionar_cliente(

    request: Request,

    cliente_id: int = Form(...)

):

    request.session["cliente_id"] = cliente_id


    return RedirectResponse(

        url="/propostas/nova",

        status_code=303

    )

@app.get("/propostas/remover-item/{item_id}")
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

        url="/propostas/nova",

        status_code=303

    )
    
@app.post("/propostas/salvar")
async def salvar_proposta(request: Request):

    cliente_id = request.session.get(
        "cliente_id"
    )


    itens = request.session.get(
        "itens_proposta",
        []
    )


    if not cliente_id or not itens:

        return RedirectResponse(

            url="/propostas/nova",

            status_code=303

        )



    conn = conectar()

    cursor = conn.cursor()



    cursor.execute(

        """

        INSERT INTO propostas

        (

            cliente_id,

            data,

            observacoes

        )

        VALUES

        (?,?,?)

        """,

        (

            cliente_id,

            "21/07/2026",

            ""

        )

    )


    proposta_id = cursor.lastrowid



    for item in itens:


        cursor.execute(

            """

            INSERT INTO itens_proposta

            (

                proposta_id,

                servico_id,

                quantidade,

                valor_unitario

            )

            VALUES

            (?,?,?,?)

            """,

            (

                proposta_id,

                item["servico_id"],

                item["quantidade"],

                item["valor"]

            )

        )



    conn.commit()

    conn.close()



    request.session.clear()



    return RedirectResponse(

        url="/",

        status_code=303

    )