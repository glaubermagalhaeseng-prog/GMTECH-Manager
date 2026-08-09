from urllib.parse import quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.database import conectar
from app.auth import empresa_id_sessao
from app.validacao import validar_empresa


router = APIRouter()

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

    request: Request,

    razao_social: str = Form(...),
    nome_fantasia: str = Form(...),
    cnpj: str = Form(...),
    responsavel: str = Form(...),
    telefone: str = Form(...),
    email: str = Form(...),
    endereco: str = Form(...),
    cidade: str = Form(...),
    uf: str = Form(...),
    cft: str = Form(...),
    tarifa_padrao: float = Form(0.85),
    produtividade_padrao: float = Form(125),
    potencia_modulo_padrao: float = Form(620),
    margem_padrao: float = Form(10),
    preco_por_kwp: float = Form(4500),
    asaas_api_key: str = Form(""),
    asaas_webhook_token: str = Form(""),
    asaas_ambiente: str = Form("sandbox"),

):

    erros = validar_empresa(razao_social, nome_fantasia, telefone)
    if erros:
        return RedirectResponse(
            url="/empresa?erro=" + quote(erros[0]),
            status_code=303
        )

    conn = conectar()
    cursor = conn.cursor()


    emp_id = empresa_id_sessao(request)

    cursor.execute("SELECT id FROM empresa WHERE id = ?", (emp_id,))
    existe = cursor.fetchone()

    if existe:
        cursor.execute("""
            UPDATE empresa SET
                razao_social=?, nome_fantasia=?, cnpj=?, responsavel=?,
                telefone=?, email=?, endereco=?, cidade=?, uf=?, cft=?,
                tarifa_padrao=?, produtividade_padrao=?,
                potencia_modulo_padrao=?, margem_padrao=?,
                preco_por_kwp=?,
                asaas_api_key=?, asaas_webhook_token=?, asaas_ambiente=?
            WHERE id=?
        """, (
            razao_social, nome_fantasia, cnpj, responsavel,
            telefone, email, endereco, cidade, uf, cft,
            tarifa_padrao, produtividade_padrao,
            potencia_modulo_padrao, margem_padrao,
            preco_por_kwp,
            asaas_api_key, asaas_webhook_token, asaas_ambiente,
            emp_id
        ))
    else:
        cursor.execute("""
            INSERT INTO empresa
            (id, razao_social, nome_fantasia, cnpj, responsavel,
             telefone, email, endereco, cidade, uf, cft,
             tarifa_padrao, produtividade_padrao,
             potencia_modulo_padrao, margem_padrao, preco_por_kwp)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            emp_id, razao_social, nome_fantasia, cnpj, responsavel,
            telefone, email, endereco, cidade, uf, cft,
            tarifa_padrao, produtividade_padrao,
            potencia_modulo_padrao, margem_padrao, preco_por_kwp
        ))


    conn.commit()
    conn.close()


    return RedirectResponse(
        "/empresa",
        status_code=303
    )