from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.database import conectar
from app.auth import hash_senha, usuario_logado


router = APIRouter()


@router.get("/login")
async def login_page(request: Request):
    if usuario_logado(request):
        return RedirectResponse("/", status_code=303)

    erro = request.query_params.get("erro")

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_fantasia, razao_social FROM empresa ORDER BY id")
    empresas = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "erro": erro,
            "empresas": empresas,
        }
    )


@router.post("/login")
async def login_submit(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    empresa_id: int = Form(1),
):
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM usuarios WHERE email = ? AND ativo = 1",
        (email.strip().lower(),)
    )
    user = cursor.fetchone()
    conn.close()

    if not user or user["senha"] != hash_senha(senha):
        return RedirectResponse(
            "/login?erro=E-mail ou senha inválidos",
            status_code=303
        )

    # empresa do usuário ou a selecionada
    emp = user["empresa_id"] or empresa_id or 1

    request.session["usuario"] = {
        "id": user["id"],
        "nome": user["nome"],
        "email": user["email"],
        "perfil": user["perfil"],
    }
    request.session["empresa_id"] = emp

    return RedirectResponse("/", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)


@router.post("/selecionar-empresa")
async def selecionar_empresa(
    request: Request,
    empresa_id: int = Form(...),
):
    if not usuario_logado(request):
        return RedirectResponse("/login", status_code=303)

    request.session["empresa_id"] = empresa_id
    return RedirectResponse("/", status_code=303)
