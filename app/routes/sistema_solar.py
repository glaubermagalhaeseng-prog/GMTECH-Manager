from urllib.parse import quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.database import conectar
from app.validacao import validar_sistema_solar


router = APIRouter()


# =====================================
# CADASTRAR SISTEMA SOLAR
# =====================================

@router.get("/propostas/{proposta_id}/sistema-solar")
async def cadastro_sistema_solar(
    request: Request,
    proposta_id: int
):

    return templates.TemplateResponse(

        request=request,

        name="sistema_solar.html",

        context={

            "proposta_id": proposta_id

        }

    )



# =====================================
# SALVAR SISTEMA SOLAR
# =====================================

@router.post("/propostas/{proposta_id}/sistema-solar/salvar")
async def salvar_sistema_solar(

    proposta_id: int,

    potencia_kwp: float = Form(...),

    quantidade_modulos: int = Form(...),

    potencia_modulo: int = Form(...),

    fabricante_modulo: str = Form(...),

    modelo_inversor: str = Form(...),

    potencia_inversor: float = Form(...),

    geracao_mensal: float = Form(...),

    economia_mensal: float = Form(...),

    valor_conta_atual: float = Form(0),

    valor_conta_residual: float = Form(0),

    observacoes: str = Form("")

):

    erros = validar_sistema_solar(potencia_kwp, quantidade_modulos, geracao_mensal)
    if erros:
        return RedirectResponse(
            url=f"/propostas/{proposta_id}/sistema-solar?erro=" + quote(erros[0]),
            status_code=303
        )

    conn = conectar()

    cursor = conn.cursor()



    cursor.execute("""

    INSERT INTO sistemas_solares

    (

        proposta_id,

        potencia_kwp,

        quantidade_modulos,

        potencia_modulo,

        fabricante_modulo,

        modelo_inversor,

        potencia_inversor,

        geracao_mensal,

        economia_mensal,

        valor_conta_atual,

        valor_conta_residual,

        observacoes

    )


    VALUES

    (?,?,?,?,?,?,?,?,?,?,?,?)

    """,

    (

        proposta_id,

        potencia_kwp,

        quantidade_modulos,

        potencia_modulo,

        fabricante_modulo,

        modelo_inversor,

        potencia_inversor,

        geracao_mensal,

        economia_mensal,

        valor_conta_atual,

        valor_conta_residual,

        observacoes

    ))



    conn.commit()

    conn.close()



    return RedirectResponse(

        f"/propostas/{proposta_id}",

        status_code=303

    )



# =====================================
# LISTAR SISTEMAS DA PROPOSTA
# =====================================

@router.get("/propostas/{proposta_id}/sistemas-solares")
async def listar_sistemas_solares(

    proposta_id: int

):


    conn = conectar()

    cursor = conn.cursor()



    cursor.execute("""

        SELECT *

        FROM sistemas_solares

        WHERE proposta_id = ?

    """,

    (proposta_id,))



    sistemas = cursor.fetchall()



    conn.close()



    return sistemas