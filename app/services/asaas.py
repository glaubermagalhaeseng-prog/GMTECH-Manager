"""
Cliente Asaas (sandbox e produção).

Documentação:
- Criar cobrança: POST /v3/payments
- Webhooks: PAYMENT_CONFIRMED, PAYMENT_RECEIVED, etc.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import date, timedelta
from typing import Any, Dict, Optional


def base_url(ambiente: str = "sandbox") -> str:
    if (ambiente or "").lower() in ("prod", "production", "producao", "produção"):
        return "https://api.asaas.com/v3"
    return "https://api-sandbox.asaas.com/v3"


def _request(
    method: str,
    path: str,
    api_key: str,
    ambiente: str = "sandbox",
    body: Optional[dict] = None,
) -> Dict[str, Any]:
    url = base_url(ambiente).rstrip("/") + "/" + path.lstrip("/")
    data = None
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "GMTECH-Manager/1.0",
        "access_token": api_key,
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(err_body)
        except Exception:
            err_json = {"raw": err_body}
        raise RuntimeError(
            f"Asaas HTTP {e.code}: {err_json.get('errors') or err_json}"
        ) from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Asaas conexão falhou: {e.reason}") from e


def _validar_cpf(cpf: str) -> bool:
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    nums = [int(d) for d in cpf]
    s = sum(nums[i] * (10 - i) for i in range(9))
    d1 = (s * 10 % 11) % 10
    if d1 != nums[9]:
        return False
    s = sum(nums[i] * (11 - i) for i in range(10))
    d2 = (s * 10 % 11) % 10
    return d2 == nums[10]


def _validar_cnpj(cnpj: str) -> bool:
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    nums = [int(d) for d in cnpj]
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s = sum(nums[i] * pesos1[i] for i in range(12))
    d1 = 11 - (s % 11)
    d1 = 0 if d1 >= 10 else d1
    if d1 != nums[12]:
        return False
    s = sum(nums[i] * pesos2[i] for i in range(13))
    d2 = 11 - (s % 11)
    d2 = 0 if d2 >= 10 else d2
    return d2 == nums[13]


def criar_ou_buscar_cliente(
    api_key: str,
    *,
    nome: str,
    cpf_cnpj: str = "",
    email: str = "",
    telefone: str = "",
    ambiente: str = "sandbox",
) -> str:
    """
    Cria cliente no Asaas e retorna o id (cus_...).
    Se já existir pelo CPF/CNPJ, a API pode retornar erro — neste caso tentamos listar.
    """
    payload: Dict[str, Any] = {"name": nome or "Cliente"}
    cpf = "".join(c for c in (cpf_cnpj or "") if c.isdigit())

    if not cpf:
        raise RuntimeError(
            "Cliente sem CPF/CNPJ. Edite o cadastro do cliente e informe um documento válido."
        )
    if len(cpf) == 11:
        if not _validar_cpf(cpf):
            raise RuntimeError(
                f"CPF inválido ({cpf}). Corrija no cadastro do cliente e tente de novo."
            )
    elif len(cpf) == 14:
        if not _validar_cnpj(cpf):
            raise RuntimeError(
                f"CNPJ inválido ({cpf}). Corrija no cadastro do cliente e tente de novo."
            )
    else:
        raise RuntimeError(
            f"CPF/CNPJ deve ter 11 ou 14 dígitos (recebido: {len(cpf)} dígitos). "
            "Corrija no cadastro do cliente."
        )

    payload["cpfCnpj"] = cpf
    if email:
        payload["email"] = email
    if telefone:
        tel = "".join(c for c in telefone if c.isdigit())
        if len(tel) >= 10:
            payload["mobilePhone"] = tel

    try:
        resp = _request("POST", "/customers", api_key, ambiente, payload)
        if resp.get("id"):
            return resp["id"]
    except RuntimeError as e:
        msg = str(e)
        # já existe — busca por CPF
        if cpf:
            try:
                lista = _request(
                    "GET",
                    f"/customers?cpfCnpj={cpf}&limit=1",
                    api_key,
                    ambiente,
                )
                data = lista.get("data") or []
                if data and data[0].get("id"):
                    return data[0]["id"]
            except Exception:
                pass
        if "inválido" in msg.lower() or "invalid" in msg.lower():
            raise RuntimeError(
                "CPF/CNPJ rejeitado pelo Asaas. Abra o cliente, confira o documento "
                "(só números válidos) e gere a cobrança de novo."
            ) from e
        raise e

    raise RuntimeError("Asaas não retornou id do cliente.")


def criar_cobranca(
    api_key: str,
    *,
    customer_id: str,
    valor: float,
    descricao: str,
    external_reference: str,
    billing_type: str = "UNDEFINED",
    dias_vencimento: int = 7,
    ambiente: str = "sandbox",
) -> Dict[str, Any]:
    """
    Cria cobrança. billing_type: UNDEFINED | PIX | BOLETO | CREDIT_CARD
    UNDEFINED deixa o cliente escolher na fatura Asaas.
    """
    due = (date.today() + timedelta(days=max(1, dias_vencimento))).isoformat()
    payload = {
        "customer": customer_id,
        "billingType": billing_type or "UNDEFINED",
        "value": round(float(valor), 2),
        "dueDate": due,
        "description": (descricao or "Proposta solar")[:500],
        "externalReference": str(external_reference),
    }
    return _request("POST", "/payments", api_key, ambiente, payload)


def processar_evento_webhook(payload: dict) -> Dict[str, Any]:
    """
    Normaliza o body do webhook Asaas.
    Retorna: event_id, event, payment_id, status, value, external_reference, payment
    """
    event = payload.get("event") or ""
    event_id = payload.get("id") or ""
    payment = payload.get("payment") or {}
    return {
        "event_id": event_id,
        "event": event,
        "payment_id": payment.get("id"),
        "status": payment.get("status"),
        "value": payment.get("value"),
        "net_value": payment.get("netValue"),
        "billing_type": payment.get("billingType"),
        "external_reference": payment.get("externalReference"),
        "invoice_url": payment.get("invoiceUrl"),
        "payment_date": payment.get("paymentDate") or payment.get("confirmedDate"),
        "payment": payment,
    }


EVENTOS_PAGO = {
    "PAYMENT_CONFIRMED",
    "PAYMENT_RECEIVED",
    "PAYMENT_ANTICIPATED",
}

EVENTOS_ATENCAO = {
    "PAYMENT_OVERDUE",
    "PAYMENT_DELETED",
    "PAYMENT_REFUNDED",
    "PAYMENT_CHARGEBACK_REQUESTED",
}
