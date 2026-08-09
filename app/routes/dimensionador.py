from urllib.parse import quote
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Request, Form, File, UploadFile
from fastapi.responses import RedirectResponse, JSONResponse

from app.templating import templates
from app.database import conectar
from app.validacao import validar_dimensionamento
from app.services.fatura_reader import ler_fatura


router = APIRouter()

UPLOAD_DIR = os.path.join("app", "static", "uploads", "faturas")
os.makedirs(UPLOAD_DIR, exist_ok=True)

EXTENSOES_OK = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}


# ==========================================
# ABRIR DIMENSIONADOR
# ==========================================

@router.get("/dimensionador")
async def dimensionador(request: Request, cliente_id: int = None):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """)

    clientes = cursor.fetchall()

    conn.close()

    fatura_resultado = request.session.pop("fatura_resultado", None)

    return templates.TemplateResponse(
        request=request,
        name="dimensionador.html",
        context={
            "clientes": clientes,
            "cliente_preselecionado": cliente_id,
            "fatura_resultado": fatura_resultado,
        }
    )


# ==========================================
# UPLOAD + LEITURA DE FATURA
# ==========================================

@router.post("/dimensionador/ler-fatura")
async def ler_fatura_upload(
    request: Request,
    fatura: UploadFile = File(...),
    cliente_id: int = Form(None),
):
    """
    Salva a fatura e tenta extrair consumo (kWh), valor e tarifa.
    Redireciona de volta ao dimensionador com os campos preenchidos.
    """
    nome = fatura.filename or "fatura.bin"
    ext = os.path.splitext(nome)[1].lower()
    if ext not in EXTENSOES_OK:
        return RedirectResponse(
            "/dimensionador?erro=" + quote(
                "Formato não suportado. Use PDF, PNG ou JPG."
            ),
            status_code=303,
        )

    nome_seguro = f"{uuid.uuid4().hex}{ext}"
    caminho = os.path.join(UPLOAD_DIR, nome_seguro)

    conteudo = await fatura.read()
    if not conteudo or len(conteudo) > 15 * 1024 * 1024:
        return RedirectResponse(
            "/dimensionador?erro=" + quote("Arquivo vazio ou maior que 15 MB."),
            status_code=303,
        )

    with open(caminho, "wb") as f:
        f.write(conteudo)

    resultado = ler_fatura(caminho)
    resultado["arquivo_url"] = f"/static/uploads/faturas/{nome_seguro}"
    resultado["arquivo_nome"] = nome
    # não guarda texto completo na sessão (limite de cookie)
    resultado.pop("texto_amostra", None)

    # grava caminho no cliente, se informado
    if cliente_id:
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE clientes SET fatura_arquivo = ? WHERE id = ?",
                (resultado["arquivo_url"], cliente_id),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    request.session["fatura_resultado"] = resultado

    q = f"/dimensionador?cliente_id={cliente_id}" if cliente_id else "/dimensionador"
    return RedirectResponse(q, status_code=303)


@router.post("/dimensionador/ler-fatura-ajax")
async def ler_fatura_ajax(
    fatura: UploadFile = File(...),
):
    """Mesma leitura, resposta JSON (para preencher campos sem reload)."""
    nome = fatura.filename or "fatura.bin"
    ext = os.path.splitext(nome)[1].lower()
    if ext not in EXTENSOES_OK:
        return JSONResponse(
            {"ok": False, "erro": "Formato não suportado. Use PDF, PNG ou JPG."},
            status_code=400,
        )

    nome_seguro = f"{uuid.uuid4().hex}{ext}"
    caminho = os.path.join(UPLOAD_DIR, nome_seguro)
    conteudo = await fatura.read()
    if not conteudo:
        return JSONResponse({"ok": False, "erro": "Arquivo vazio."}, status_code=400)

    with open(caminho, "wb") as f:
        f.write(conteudo)

    resultado = ler_fatura(caminho)
    resultado["ok"] = True
    resultado["arquivo_url"] = f"/static/uploads/faturas/{nome_seguro}"
    resultado["arquivo_nome"] = nome
    return JSONResponse(resultado)



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

    quantidade_modulos: int = Form(0),

    potencia_final: float = Form(0),

    geracao: float = Form(0),

    economia: float = Form(0),

    aplicar_fio_b: str = Form(""),
    eusd_b: float = Form(0.083),

    fabricante_modulo: str = Form(""),

    modelo_modulo: str = Form(""),

    fabricante_inversor: str = Form(""),

    modelo_inversor: str = Form(""),

    potencia_inversor: float = Form(0),

    dimensionamento_id: str = Form("")

):


    erros = validar_dimensionamento(
        cliente_id, consumo, produtividade, modulo, tarifa
    )
    if erros:
        return RedirectResponse(
            url="/dimensionador?erro=" + quote(erros[0]),
            status_code=303
        )

    # Recalcula no servidor (não depende só do JS)
    consumo_total = consumo + (consumo_beneficiarias or 0)
    consumo_corrigido = consumo_total * (1 + margem / 100)

    potencia_calculada = (
        consumo_corrigido / produtividade if produtividade else 0
    )

    if not quantidade_modulos and modulo:
        quantidade_modulos = max(1, round((potencia_calculada * 1000) / modulo))

    if not potencia_final and quantidade_modulos and modulo:
        potencia_final = (quantidade_modulos * modulo) / 1000

    if not geracao and potencia_final and produtividade:
        geracao = potencia_final * produtividade

    if not economia and geracao and tarifa:
        economia = geracao * tarifa


            # ==========================================
    # CÁLCULO FIO B - LEI 14.300 (opcional)
    # custo = geração × EUSD-B (R$/kWh) × (% transição do ano)
    # NÃO aplica o % sobre a economia bruta inteira.
    # ==========================================
    aplicar = str(aplicar_fio_b or "").lower() in ("1", "on", "true", "sim")

    if not aplicar:
        percentual_fio_b = 0
    elif ano_conexao <= 2022:
        percentual_fio_b = 0
    elif ano_conexao == 2023:
        percentual_fio_b = 15
    elif ano_conexao == 2024:
        percentual_fio_b = 30
    elif ano_conexao == 2025:
        percentual_fio_b = 45
    elif ano_conexao == 2026:
        percentual_fio_b = 60
    elif ano_conexao == 2027:
        percentual_fio_b = 75
    elif ano_conexao == 2028:
        percentual_fio_b = 90
    else:
        percentual_fio_b = 100  # 2029+

    # Garante geração/economia no servidor
    if not geracao and potencia_final and produtividade:
        geracao = potencia_final * produtividade
    if potencia_final and quantidade_modulos == 0 and modulo:
        quantidade_modulos = max(1, round((potencia_final * 1000) / modulo))
    if geracao and tarifa:
        economia = geracao * tarifa
    elif not economia and geracao and tarifa:
        economia = geracao * tarifa

    eusd = float(eusd_b or 0)
    if eusd < 0:
        eusd = 0
    # Se o usuário digitou valor tipo 83.31 (R$/MWh), converte para R$/kWh
    if eusd > 2:
        eusd = eusd / 1000.0

    if aplicar and geracao and percentual_fio_b:
        custo_fio_b = geracao * eusd * (percentual_fio_b / 100.0)
    else:
        custo_fio_b = 0.0

    economia_liquida = max(0.0, (economia or 0) - custo_fio_b)

    # Cria colunas Fio B se o banco for antigo
    from app.database import garantir_colunas_dimensionamentos
    try:
        garantir_colunas_dimensionamentos()
    except Exception:
        pass

    conn = conectar()
    cursor = conn.cursor()

    try:
        if dimensionamento_id:
            cursor.execute(
                """
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
                    dimensionamento_id,
                ),
            )
            conn.commit()
            conn.close()
            return RedirectResponse(
                f"/dimensionamentos/{dimensionamento_id}",
                status_code=303,
            )

        cursor.execute(
            """
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
                economia,
                economia,
                custo_fio_b,
                economia_liquida,
                "Calculado",
            ),
        )

        novo_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return RedirectResponse(
            f"/dimensionamentos/{novo_id}",
            status_code=303,
        )

    except Exception as e:
        try:
            conn.close()
        except Exception:
            pass
        return RedirectResponse(
            url="/dimensionador?erro=" + quote(f"Erro ao salvar: {e}"),
            status_code=303,
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
        name="visualizar_dimensionamento.html",
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
    
