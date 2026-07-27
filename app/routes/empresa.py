from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.database import conectar


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


# =========================
# VISUALIZAR EMPRESA
# =========================

@router.get("/empresa")
async def empresa(request: Request):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM empresa
        LIMIT 1
    """)

    empresa = cursor.fetchone()

    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="empresa.html",
        context={
            "empresa": empresa
        }
    )



# =========================
# SALVAR EMPRESA
# =========================

@router.post("/empresa/salvar")
async def salvar_empresa(

    razao_social: str = Form(...),
    nome_fantasia: str = Form(...),
    cnpj: str = Form(...),
    responsavel: str = Form(...),
    telefone: str = Form(...),
    email: str = Form(...),
    endereco: str = Form(...),
    cidade: str = Form(...),
    uf: str = Form(...),
    cft: str = Form(...)

):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        DELETE FROM empresa
    """)


    cursor.execute("""
        INSERT INTO empresa
        (
            razao_social,
            nome_fantasia,
            cnpj,
            responsavel,
            telefone,
            email,
            endereco,
            cidade,
            uf,
            cft
        )

        VALUES
        (?,?,?,?,?,?,?,?,?,?)

    """,

    (
        razao_social,
        nome_fantasia,
        cnpj,
        responsavel,
        telefone,
        email,
        endereco,
        cidade,
        uf,
        cft
    ))


    conn.commit()
    conn.close()


    return RedirectResponse(
        "/empresa",
        status_code=303
    )