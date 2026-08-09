"""
Webhook Asaas + geração de cobrança a partir da proposta.

URL pública (configurar no painel Asaas):
  POST /webhooks/asaas

Header opcional de autenticação:
  asaas-access-token: <token configurado em empresa.asaas_webhook_token>
"""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Request, Form
from fastapi.responses import JSONResponse, RedirectResponse

from app.database import conectar
from app.services.asaas import (
    EVENTOS_ATENCAO,
    EVENTOS_PAGO,
    criar_cobranca,
    criar_ou_buscar_cliente,
    processar_evento_webhook,
)

router = APIRouter()


def _empresa_asaas(cursor):
    cursor.execute(
        """
        SELECT asaas_api_key, asaas_webhook_token, asaas_ambiente
        FROM empresa LIMIT 1
        """
    )
    row = cursor.fetchone()
    if not row:
        return None, None, "sandbox"
    return (
        row["asaas_api_key"] if "asaas_api_key" in row.keys() else None,
        row["asaas_webhook_token"] if "asaas_webhook_token" in row.keys() else None,
        (row["asaas_ambiente"] if "asaas_ambiente" in row.keys() else None) or "sandbox",
    )


def _criar_os_se_preciso(cursor, proposta_id: int) -> int | None:
    cursor.execute(
        "SELECT id FROM ordens_servico WHERE proposta_id = ? LIMIT 1",
        (proposta_id,),
    )
    if cursor.fetchone():
        return None

    cursor.execute("SELECT * FROM propostas WHERE id = ?", (proposta_id,))
    proposta = cursor.fetchone()
    if not proposta:
        return None

    cursor.execute(
        """
        SELECT * FROM sistemas_solares
        WHERE proposta_id = ?
        ORDER BY id DESC LIMIT 1
        """,
        (proposta_id,),
    )
    sistema = cursor.fetchone()

    cursor.execute(
        """
        SELECT descricao, quantidade, valor_unitario
        FROM itens_proposta WHERE proposta_id = ?
        """,
        (proposta_id,),
    )
    itens = cursor.fetchall()

    linhas = []
    for item in itens:
        total_item = (item["quantidade"] or 0) * (item["valor_unitario"] or 0)
        linhas.append(
            f"- {item['descricao']} (qtd {item['quantidade']}) — R$ {total_item:.2f}"
        )
    if sistema:
        linhas.insert(
            0,
            f"Sistema fotovoltaico {sistema['potencia_kwp']} kWp — "
            f"{sistema['quantidade_modulos']} módulos",
        )
    descricao = "\n".join(linhas) if linhas else (
        proposta["observacoes"] or "OS gerada após pagamento Asaas."
    )

    cursor.execute(
        """
        INSERT INTO ordens_servico
        (
            proposta_id, cliente_id, status, data_criacao,
            valor_fechado, potencia_kwp, quantidade_modulos,
            descricao, observacoes
        )
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            proposta_id,
            proposta["cliente_id"],
            "Aguardando início",
            datetime.now().strftime("%d/%m/%Y"),
            proposta["valor_total"] or 0,
            sistema["potencia_kwp"] if sistema else None,
            sistema["quantidade_modulos"] if sistema else None,
            descricao,
            "Criada automaticamente após confirmação de pagamento (Asaas).",
        ),
    )
    return cursor.lastrowid


@router.post("/webhooks/asaas")
async def webhook_asaas(request: Request):
    """
    Recebe eventos do Asaas. Sempre responde 200 quando o body é válido,
    para não pausar a fila. Idempotente via event_id.
    """
    # token opcional
    conn = conectar()
    cursor = conn.cursor()
    _, webhook_token, _ = _empresa_asaas(cursor)

    header_token = request.headers.get("asaas-access-token") or request.headers.get(
        "Asaas-Access-Token"
    )
    if webhook_token and header_token and header_token != webhook_token:
        conn.close()
        return JSONResponse({"error": "token inválido"}, status_code=401)

    try:
        payload = await request.json()
    except Exception:
        conn.close()
        return JSONResponse({"error": "JSON inválido"}, status_code=400)

    info = processar_evento_webhook(payload)
    event_id = info["event_id"] or f"no-id-{info['payment_id']}-{info['event']}"
    event = info["event"]

    # idempotência
    try:
        cursor.execute(
            "SELECT id FROM asaas_webhook_events WHERE event_id = ?",
            (event_id,),
        )
        if cursor.fetchone():
            conn.close()
            return JSONResponse({"received": True, "duplicate": True})
    except Exception:
        # tabela pode não existir em DB antigo — tenta criar
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS asaas_webhook_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE,
                    event_type TEXT,
                    payment_id TEXT,
                    payload TEXT,
                    processado_em TEXT,
                    resultado TEXT
                )
                """
            )
            conn.commit()
        except Exception:
            pass

    resultado = "ignorado"
    proposta_id = None

    # localiza proposta por payment_id ou externalReference
    payment_id = info["payment_id"]
    ext_ref = info["external_reference"]

    proposta = None
    if payment_id:
        cursor.execute(
            "SELECT * FROM propostas WHERE asaas_payment_id = ?",
            (payment_id,),
        )
        proposta = cursor.fetchone()
    if not proposta and ext_ref:
        # externalReference = "proposta:123"
        ref = str(ext_ref)
        if ref.startswith("proposta:"):
            try:
                pid = int(ref.split(":", 1)[1])
                cursor.execute("SELECT * FROM propostas WHERE id = ?", (pid,))
                proposta = cursor.fetchone()
            except ValueError:
                pass
        else:
            try:
                pid = int(ref)
                cursor.execute("SELECT * FROM propostas WHERE id = ?", (pid,))
                proposta = cursor.fetchone()
            except ValueError:
                pass

    if proposta:
        proposta_id = proposta["id"]
        novo_status_pag = None
        novo_status_prop = None

        if event in EVENTOS_PAGO:
            novo_status_pag = "Pago"
            novo_status_prop = "Aceita"
            resultado = "pago"
        elif event == "PAYMENT_OVERDUE":
            novo_status_pag = "Vencido"
            resultado = "vencido"
        elif event == "PAYMENT_DELETED":
            novo_status_pag = "Cancelado"
            resultado = "cancelado"
        elif event in EVENTOS_ATENCAO:
            novo_status_pag = event.replace("PAYMENT_", "")
            resultado = "atencao"
        elif event == "PAYMENT_CREATED":
            novo_status_pag = "Aguardando"
            resultado = "criado"
        else:
            novo_status_pag = info["status"] or event
            resultado = f"evento:{event}"

        sets = ["asaas_status = ?", "pagamento_status = ?"]
        vals = [info["status"] or event, novo_status_pag]

        if info["invoice_url"]:
            sets.append("asaas_invoice_url = ?")
            vals.append(info["invoice_url"])
        if payment_id:
            sets.append("asaas_payment_id = ?")
            vals.append(payment_id)

        if event in EVENTOS_PAGO:
            sets.append("status = ?")
            vals.append(novo_status_prop)
            sets.append("pago_em = ?")
            vals.append(datetime.now().strftime("%d/%m/%Y %H:%M"))

        vals.append(proposta_id)
        cursor.execute(
            f"UPDATE propostas SET {', '.join(sets)} WHERE id = ?",
            tuple(vals),
        )

        if event in EVENTOS_PAGO:
            os_id = _criar_os_se_preciso(cursor, proposta_id)
            if os_id:
                resultado = f"pago_os:{os_id}"

        conn.commit()

    # log do evento
    try:
        import json

        cursor.execute(
            """
            INSERT OR IGNORE INTO asaas_webhook_events
            (event_id, event_type, payment_id, payload, processado_em, resultado)
            VALUES (?,?,?,?,?,?)
            """,
            (
                event_id,
                event,
                payment_id,
                json.dumps(payload, ensure_ascii=False)[:8000],
                datetime.now().isoformat(timespec="seconds"),
                f"{resultado}|proposta={proposta_id}",
            ),
        )
        conn.commit()
    except Exception:
        pass

    conn.close()
    # Asaas exige HTTP 200
    return JSONResponse(
        {"received": True, "event": event, "resultado": resultado},
        status_code=200,
    )


@router.post("/propostas/{proposta_id}/gerar-pagamento")
async def gerar_pagamento_asaas(
    request: Request,
    proposta_id: int,
    billing_type: str = Form("UNDEFINED"),
    dias_vencimento: int = Form(7),
):
    """
    Cria cobrança no Asaas vinculada à proposta.
    Salva payment_id e invoiceUrl na proposta.
    """
    conn = conectar()
    cursor = conn.cursor()

    api_key, _, ambiente = _empresa_asaas(cursor)
    if not api_key:
        conn.close()
        return RedirectResponse(
            f"/propostas/{proposta_id}?erro="
            + quote("Configure a API Key do Asaas em Empresa."),
            status_code=303,
        )

    cursor.execute("SELECT * FROM propostas WHERE id = ?", (proposta_id,))
    proposta = cursor.fetchone()
    if not proposta:
        conn.close()
        return RedirectResponse("/propostas", status_code=303)

    valor = float(proposta["valor_total"] or 0)
    if valor <= 0:
        conn.close()
        return RedirectResponse(
            f"/propostas/{proposta_id}?erro="
            + quote("Proposta sem valor total."),
            status_code=303,
        )

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (proposta["cliente_id"],))
    cliente = cursor.fetchone()
    if not cliente:
        conn.close()
        return RedirectResponse(
            f"/propostas/{proposta_id}?erro=" + quote("Cliente não encontrado."),
            status_code=303,
        )

    try:
        customer_id = criar_ou_buscar_cliente(
            api_key,
            nome=cliente["nome"] or "Cliente",
            cpf_cnpj=cliente["cpf_cnpj"] or "",
            email=cliente["email"] or "",
            telefone=cliente["telefone"] or "",
            ambiente=ambiente,
        )
        cob = criar_cobranca(
            api_key,
            customer_id=customer_id,
            valor=valor,
            descricao=f"Proposta #{proposta_id} — sistema fotovoltaico",
            external_reference=f"proposta:{proposta_id}",
            billing_type=billing_type or "UNDEFINED",
            dias_vencimento=int(dias_vencimento or 7),
            ambiente=ambiente,
        )
    except Exception as e:
        conn.close()
        return RedirectResponse(
            f"/propostas/{proposta_id}?erro=" + quote(str(e)[:180]),
            status_code=303,
        )

    payment_id = cob.get("id")
    invoice_url = cob.get("invoiceUrl") or cob.get("bankSlipUrl") or ""
    status = cob.get("status") or "PENDING"

    cursor.execute(
        """
        UPDATE propostas SET
            asaas_payment_id = ?,
            asaas_invoice_url = ?,
            asaas_status = ?,
            pagamento_status = ?
        WHERE id = ?
        """,
        (payment_id, invoice_url, status, "Aguardando", proposta_id),
    )
    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/propostas/{proposta_id}?ok="
        + quote("Cobrança Asaas gerada. Envie o link ao cliente."),
        status_code=303,
    )
