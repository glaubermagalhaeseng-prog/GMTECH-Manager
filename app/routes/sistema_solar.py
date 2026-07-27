from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from app.database import conectar


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)



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

    observacoes: str = Form("")

):


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

        observacoes

    )


    VALUES

    (?,?,?,?,?,?,?,?,?,?)

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