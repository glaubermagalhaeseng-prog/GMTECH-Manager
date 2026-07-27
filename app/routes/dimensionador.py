from fastapi import APIRouter, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

from datetime import datetime

from app.database import conectar


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)


# ==========================================
# ABRIR DIMENSIONADOR
# ==========================================

@router.get("/dimensionador")
async def dimensionador(request: Request):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """)

    clientes = cursor.fetchall()

    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="dimensionador.html",
        context={
            "clientes": clientes
        }
    )



# ==========================================
# SALVAR DIMENSIONAMENTO
# ==========================================

@router.post("/dimensionador/salvar")
async def salvar_dimensionamento(

    request: Request,

    modalidade: str = Form("Autoconsumo local"),

    ano_conexao: int = Form(2026),

    quantidade_beneficiarias: int = Form(0),

    consumo_beneficiarias: float = Form(0),

    percentual_fio_b: float = Form(0),

    custo_fio_b: float = Form(0),

    economia_liquida: float = Form(0),

    consumo_corrigido: float = Form(0),

    cliente_id: int = Form(...),

    consumo: float = Form(...),

    produtividade: float = Form(...),

    margem: float = Form(10),

    modulo: int = Form(...),

    tarifa: float = Form(...),

    quantidade_modulos: int = Form(...),

    potencia_final: float = Form(...),

    geracao: float = Form(...),

    economia: float = Form(...),


    fabricante_modulo: str = Form(""),

    modelo_modulo: str = Form(""),

    fabricante_inversor: str = Form(""),

    modelo_inversor: str = Form(""),

    potencia_inversor: float = Form(0),

    dimensionamento_id: str = Form("")

):


    consumo_corrigido = (
        consumo * (1 + margem / 100)
    )


    potencia_calculada = (
        consumo_corrigido / produtividade
    )


            # ==========================================
    # CÁLCULO FIO B - LEI 14.300
    # ==========================================

    if ano_conexao <= 2022:

        percentual_fio_b = 0

    elif ano_conexao == 2023:

        percentual_fio_b = 15

    elif ano_conexao == 2024:

        percentual_fio_b = 30

    elif ano_conexao == 2025:

        percentual_fio_b = 45

    else:

        percentual_fio_b = 60



    custo_fio_b = economia * (percentual_fio_b / 100)

    economia_liquida = economia - custo_fio_b



    conn = conectar()
    
    cursor = conn.cursor()


    print("Economia bruta:", economia)
    print("Percentual Fio B:", percentual_fio_b)
    print("Custo Fio B:", custo_fio_b)
    print("Economia líquida:", economia_liquida)

    if dimensionamento_id:


        cursor.execute("""
            UPDATE dimensionamentos_solares
            SET

                cliente_id = ?,
                consumo_medio = ?,
                margem_tecnica = ?,
                produtividade = ?,
                modalidade = ?,
                ano_conexao = ?,
                quantidade_beneficiarias = ?,
                consumo_beneficiarias = ?,
                percentual_fio_b = ?,
                consumo_corrigido = ?,
                potencia_calculada_kwp = ?,
                quantidade_modulos = ?,
                potencia_modulo = ?,
                fabricante_modulo = ?,
                modelo_modulo = ?,
                fabricante_inversor = ?,
                modelo_inversor = ?,
                potencia_inversor = ?,
                potencia_final_kwp = ?,
                geracao_estimada = ?,
                tarifa_energia = ?,
                economia_estimada = ?,
                economia_bruta = ?,
                custo_fio_b = ?,
                economia_liquida = ?

            WHERE id = ?

        """,

        (

            cliente_id,
            consumo,
            margem,
            produtividade,
            modalidade,
            ano_conexao,
            quantidade_beneficiarias,
            consumo_beneficiarias,
            percentual_fio_b,
            consumo_corrigido,
            potencia_calculada,
            quantidade_modulos,
            modulo,
            fabricante_modulo,
            modelo_modulo,
            fabricante_inversor,
            modelo_inversor,
            potencia_inversor,
            potencia_final,
            geracao,
            tarifa,
            economia,
            economia,
            custo_fio_b,
            economia_liquida,
            dimensionamento_id

        ))


        conn.commit()

        conn.close()


        return RedirectResponse(
            "/dimensionamentos",
            status_code=303
        )

    cursor.execute("""
    INSERT INTO dimensionamentos_solares
    (

        cliente_id,

        data,

        consumo_medio,

        margem_tecnica,

        produtividade,

        modalidade,

        ano_conexao,

        quantidade_beneficiarias,

        consumo_beneficiarias,

        percentual_fio_b,

        consumo_corrigido,

        potencia_calculada_kwp,

        quantidade_modulos,

        potencia_modulo,

        fabricante_modulo,

        modelo_modulo,

        fabricante_inversor,

        modelo_inversor,

        potencia_inversor,

        potencia_final_kwp,

        geracao_estimada,

        tarifa_energia,

        economia_estimada,

        economia_bruta,

        custo_fio_b,

        economia_liquida,

        status

    )

    VALUES

    (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)

    """,

    (

        cliente_id,

        datetime.now().strftime("%d/%m/%Y"),

        consumo,

        margem,

        produtividade,

        modalidade,

        ano_conexao,

        quantidade_beneficiarias,

        consumo_beneficiarias,

        percentual_fio_b,

        consumo_corrigido,

        potencia_calculada,

        quantidade_modulos,

        modulo,

        fabricante_modulo,

        modelo_modulo,

        fabricante_inversor,

        modelo_inversor,

        potencia_inversor,

        potencia_final,

        geracao,

        tarifa,

        economia,          # economia_estimada

        economia,          # economia_bruta

        custo_fio_b,

        economia_liquida,

        "Calculado"

    ))



    conn.commit()


    print("SALVOU DIMENSIONAMENTO COM SUCESSO")


    conn.close()



    return RedirectResponse(
        "/dimensionador",
        status_code=303
    )


# ==========================================
# LISTAR DIMENSIONAMENTOS
# ==========================================

@router.get("/dimensionamentos")
async def listar_dimensionamentos(request: Request):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            d.*,
            c.nome AS cliente_nome
        FROM dimensionamentos_solares d
        LEFT JOIN clientes c
            ON c.id = d.cliente_id
        ORDER BY d.id DESC
    """)

    dimensionamentos = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="dimensionamentos.html",
        context={
            "dimensionamentos": dimensionamentos
        }
    )

# ==========================================
# VISUALIZAR DIMENSIONAMENTO
# ==========================================

@router.get("/dimensionamentos/{id}")
async def visualizar_dimensionamento(
    id: int,
    request: Request
):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT
            d.*,
            c.nome AS cliente_nome
        FROM dimensionamentos_solares d
        LEFT JOIN clientes c
            ON c.id = d.cliente_id
        WHERE d.id = ?
    """, (id,))


    dimensionamento = cursor.fetchone()


    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="dimensionamento.html",
        context={
            "dimensionamento": dimensionamento
        }
    )

# ==========================================
# EXCLUIR DIMENSIONAMENTO
# ==========================================

@router.get("/dimensionamentos/{id}/excluir")
async def excluir_dimensionamento(id: int):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
        DELETE FROM dimensionamentos_solares
        WHERE id = ?
    """, (id,))


    conn.commit()

    conn.close()


    return RedirectResponse(
        "/dimensionamentos",
        status_code=303
    )

# ==========================================
# EDITAR DIMENSIONAMENTO
# ==========================================

@router.get("/dimensionamentos/{id}/editar")
async def editar_dimensionamento(id: int, request: Request):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT *
        FROM dimensionamentos_solares
        WHERE id = ?
    """, (id,))


    dimensionamento = cursor.fetchone()



    cursor.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """)


    clientes = cursor.fetchall()


    conn.close()



    return templates.TemplateResponse(
        request=request,
        name="dimensionador.html",
        context={
            "dimensionamento": dimensionamento,
            "clientes": clientes
        }
    )
    
