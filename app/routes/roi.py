"""Rotas da Calculadora de ROI Solar."""

from fastapi import APIRouter, Request, Form, Query
from fastapi.responses import JSONResponse

from app.templating import templates
from app.database import conectar
from app.services.roi import calcular_roi


router = APIRouter()


def _fmt_br(valor) -> str:
    try:
        v = float(valor)
    except (TypeError, ValueError):
        return "—"
    s = f"{v:,.2f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")


@router.get("/roi")
async def pagina_roi(
    request: Request,
    proposta_id: int = Query(None),
):
    prefill = {
        "investimento": "",
        "economia_mensal": "",
        "anos": 25,
        "reajuste_tarifa_aa": 8.0,
        "degradacao_aa": 0.5,
        "taxa_desconto_aa": 10.0,
        "om_anual": 0,
        "cliente_nome": "",
        "proposta_id": proposta_id or "",
    }
    resultado = None

    if proposta_id:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT p.id, p.valor_total, p.status,
                   c.nome AS cliente_nome,
                   s.economia_mensal, s.valor_conta_atual, s.valor_conta_residual,
                   s.potencia_kwp
            FROM propostas p
            LEFT JOIN clientes c ON c.id = p.cliente_id
            LEFT JOIN sistemas_solares s ON s.proposta_id = p.id
            WHERE p.id = ?
            """,
            (proposta_id,),
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            prefill["proposta_id"] = row["id"]
            prefill["cliente_nome"] = row["cliente_nome"] or ""
            if row["valor_total"]:
                prefill["investimento"] = float(row["valor_total"])

            eco = row["economia_mensal"]
            atual = row["valor_conta_atual"] or 0
            residual = row["valor_conta_residual"]
            if atual and residual is not None:
                eco = max(0, float(atual) - float(residual))
            if eco:
                prefill["economia_mensal"] = float(eco)

            # já calcula na abertura se tiver dados
            if prefill["investimento"] and prefill["economia_mensal"]:
                resultado = calcular_roi(
                    prefill["investimento"],
                    prefill["economia_mensal"],
                    anos=25,
                )

    # lista curta de propostas para carregar
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, c.nome AS cliente_nome, p.valor_total, p.status
        FROM propostas p
        LEFT JOIN clientes c ON c.id = p.cliente_id
        ORDER BY p.id DESC
        LIMIT 40
        """
    )
    propostas = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="roi.html",
        context={
            "prefill": prefill,
            "resultado": resultado,
            "propostas": propostas,
            "fmt": _fmt_br,
        },
    )


@router.post("/roi/calcular")
async def calcular_roi_form(
    request: Request,
    investimento: float = Form(...),
    economia_mensal: float = Form(...),
    anos: int = Form(25),
    reajuste_tarifa_aa: float = Form(8.0),
    degradacao_aa: float = Form(0.5),
    taxa_desconto_aa: float = Form(10.0),
    om_anual: float = Form(0),
    proposta_id: str = Form(""),
):
    resultado = calcular_roi(
        investimento,
        economia_mensal,
        anos=anos,
        reajuste_tarifa_aa=reajuste_tarifa_aa,
        degradacao_aa=degradacao_aa,
        taxa_desconto_aa=taxa_desconto_aa,
        om_anual=om_anual,
    )

    # se veio de fetch JSON (Accept), devolve JSON
    accept = (request.headers.get("accept") or "").lower()
    if "application/json" in accept:
        return JSONResponse(resultado)

    prefill = {
        "investimento": investimento,
        "economia_mensal": economia_mensal,
        "anos": anos,
        "reajuste_tarifa_aa": reajuste_tarifa_aa,
        "degradacao_aa": degradacao_aa,
        "taxa_desconto_aa": taxa_desconto_aa,
        "om_anual": om_anual,
        "cliente_nome": "",
        "proposta_id": proposta_id,
    }

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT p.id, c.nome AS cliente_nome, p.valor_total, p.status
        FROM propostas p
        LEFT JOIN clientes c ON c.id = p.cliente_id
        ORDER BY p.id DESC
        LIMIT 40
        """
    )
    propostas = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="roi.html",
        context={
            "prefill": prefill,
            "resultado": resultado,
            "propostas": propostas,
            "fmt": _fmt_br,
        },
    )


@router.post("/roi/api")
async def calcular_roi_api(request: Request):
    """API JSON para recálculo em tempo real na tela."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"erro": "JSON inválido"}, status_code=400)

    resultado = calcular_roi(
        body.get("investimento", 0),
        body.get("economia_mensal", 0),
        anos=int(body.get("anos") or 25),
        reajuste_tarifa_aa=float(body.get("reajuste_tarifa_aa") or 8),
        degradacao_aa=float(body.get("degradacao_aa") or 0.5),
        taxa_desconto_aa=float(body.get("taxa_desconto_aa") or 10),
        om_anual=float(body.get("om_anual") or 0),
    )
    return JSONResponse(resultado)
