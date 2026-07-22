from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database import conectar


router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


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