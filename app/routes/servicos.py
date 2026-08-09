from urllib.parse import quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.database import conectar
from app.validacao import validar_servico


router = APIRouter()

# =========================
# SERVIÇOS
# =========================


@router.get("/servicos")
async def listar_servicos(request: Request):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT * FROM servicos
        ORDER BY id DESC
        """
    )

    servicos = cursor.fetchall()

    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="servicos.html",
        context={
            "servicos": servicos
        }
    )



@router.get("/servicos/novo")
async def novo_servico(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="novo_servico.html"
    )



@router.post("/servicos/salvar")
async def salvar_servico(

    descricao: str = Form(...),
    categoria: str = Form(""),
    valor: float = Form(0)

):

    erros = validar_servico(descricao)
    if erros:
        return RedirectResponse(
            url="/servicos/novo?erro=" + quote(erros[0]),
            status_code=303
        )

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        INSERT INTO servicos
        (
            descricao,
            categoria,
            valor
        )

        VALUES
        (?,?,?)

        """,

        (
            descricao,
            categoria,
            valor
        )
    )


    conn.commit()

    conn.close()


    return RedirectResponse(
        url="/servicos",
        status_code=303
    )

    # =========================
# EDITAR SERVIÇO
# =========================


@router.get("/servicos/editar/{id}")
async def editar_servico(
    request: Request,
    id: int
):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT *
        FROM servicos
        WHERE id=?
        """,
        (id,)
    )


    servico = cursor.fetchone()


    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="editar_servico.html",
        context={
            "servico": servico
        }
    )




@router.post("/servicos/editar/{id}")
async def salvar_edicao_servico(

    id: int,

    descricao: str = Form(...),
    categoria: str = Form(""),
    valor: float = Form(0)

):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        UPDATE servicos SET

        descricao=?,
        categoria=?,
        valor=?

        WHERE id=?

        """,

        (
            descricao,
            categoria,
            valor,
            id
        )

    )


    conn.commit()

    conn.close()


    return RedirectResponse(
        url="/servicos",
        status_code=303
    )





# =========================
# EXCLUIR SERVIÇO
# =========================


@router.get("/servicos/excluir/{id}")
async def excluir_servico(id: int):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute(
        """
        DELETE FROM servicos
        WHERE id=?
        """,
        (id,)
    )


    conn.commit()

    conn.close()


    return RedirectResponse(
        url="/servicos",
        status_code=303
    )