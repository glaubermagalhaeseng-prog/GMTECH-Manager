from urllib.parse import quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.database import conectar
from app.auth import empresa_id_sessao
from app.validacao import validar_cliente


router = APIRouter()

# =========================
# CLIENTES
# =========================


@router.get("/clientes")
async def listar_clientes(request: Request):

    conn = conectar()

    cursor = conn.cursor()

    emp = empresa_id_sessao(request)
    cursor.execute(
        """
        SELECT * FROM clientes
        WHERE COALESCE(empresa_id, 1) = ?
        ORDER BY id DESC
        """,
        (emp,)
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

    erros = validar_cliente(nome)
    if erros:
        return RedirectResponse(
            url="/clientes/novo?erro=" + quote(erros[0]),
            status_code=303
        )

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
    novo_id = cursor.lastrowid
    conn.close()

    return RedirectResponse(
        url=f"/dimensionador?cliente_id={novo_id}",
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

    # =========================
# EDITAR CLIENTE
# =========================


@router.get("/clientes/editar/{id}")
async def editar_cliente(
    request: Request,
    id: int
):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM clientes
        WHERE id=?
        """,
        (id,)
    )


    cliente = cursor.fetchone()


    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="editar_cliente.html",
        context={
            "cliente": cliente
        }
    )




@router.post("/clientes/editar/{id}")
async def salvar_edicao_cliente(

    id: int,

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

    erros = validar_cliente(nome)
    if erros:
        return RedirectResponse(
            url=f"/clientes/editar/{id}?erro=" + quote(erros[0]),
            status_code=303
        )

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE clientes SET

        nome=?,
        cpf_cnpj=?,
        telefone=?,
        email=?,
        rua=?,
        numero=?,
        bairro=?,
        cidade=?,
        uf=?,
        tipo_cliente=?,
        unidade_consumidora=?,
        observacoes=?

        WHERE id=?

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
            observacoes,
            id
        )

    )


    conn.commit()

    conn.close()


    return RedirectResponse(
        url="/clientes",
        status_code=303
    )