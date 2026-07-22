from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import conectar


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


# =========================
# CLIENTES
# =========================


@router.get("/clientes")
async def listar_clientes(request: Request):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM clientes
        ORDER BY id DESC
        """
    )

    clientes = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="clientes.html",
        context={
            "clientes": clientes
        }
    )



@router.get("/clientes/novo")
async def novo_cliente(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="novo_cliente.html"
    )



@router.post("/clientes/salvar")
async def salvar_cliente(

    nome: str = Form(...),
    cpf_cnpj: str = Form(""),
    telefone: str = Form(""),
    email: str = Form(""),
    rua: str = Form(""),
    numero: str = Form(""),
    bairro: str = Form(""),
    cidade: str = Form(""),
    uf: str = Form(""),
    tipo_cliente: str = Form(""),
    unidade_consumidora: str = Form(""),
    observacoes: str = Form("")

):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO clientes
        (
            nome,
            cpf_cnpj,
            telefone,
            email,
            rua,
            numero,
            bairro,
            cidade,
            uf,
            tipo_cliente,
            unidade_consumidora,
            observacoes
        )

        VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?)

        """,

        (
            nome,
            cpf_cnpj,
            telefone,
            email,
            rua,
            numero,
            bairro,
            cidade,
            uf,
            tipo_cliente,
            unidade_consumidora,
            observacoes
        )
    )


    conn.commit()

    conn.close()


    return RedirectResponse(
        url="/clientes",
        status_code=303
    )



@router.get("/clientes/excluir/{id}")
async def excluir_cliente(id: int):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM clientes
        WHERE id=?
        """,
        (id,)
    )


    conn.commit()

    conn.close()


    return RedirectResponse(
        url="/clientes",
        status_code=303
    )