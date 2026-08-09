from urllib.parse import quote
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from datetime import datetime

from app.templating import templates
from app.database import conectar
from app.validacao import validar_orcamento_publico


router = APIRouter()

# ==========================================
# CÁLCULO DO ORÇAMENTO
# (mesma lógica do dimensionador, mas
#  partindo do valor da conta em R$)
# ==========================================

def calcular_orcamento(valor_conta, config):

    tarifa = config["tarifa_padrao"] or 0.85

    produtividade = config["produtividade_padrao"] or 125

    potencia_modulo = config["potencia_modulo_padrao"] or 620

    margem = config["margem_padrao"] or 10


    consumo_estimado = valor_conta / tarifa

    consumo_corrigido = consumo_estimado * (1 + margem / 100)

    potencia_kwp = consumo_corrigido / produtividade

    quantidade_modulos = max(
        1,
        round((potencia_kwp * 1000) / potencia_modulo)
    )

    potencia_final = (quantidade_modulos * potencia_modulo) / 1000

    geracao_estimada = potencia_final * produtividade

    economia_estimada = geracao_estimada * tarifa


    return {
        "consumo_estimado": round(consumo_estimado, 0),
        "potencia_estimada_kwp": round(potencia_final, 2),
        "quantidade_modulos": quantidade_modulos,
        "geracao_estimada": round(geracao_estimada, 0),
        "economia_estimada": round(economia_estimada, 2)
    }



# ==========================================
# PÁGINA PÚBLICA DO SIMULADOR
# ==========================================

@router.get("/orcamento")
async def orcamento(request: Request):

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
        name="orcamento.html",
        context={
            "empresa": empresa
        }
    )



# ==========================================
# ENVIAR SIMULAÇÃO (VIRA LEAD)
# ==========================================

@router.post("/orcamento/enviar")
async def enviar_orcamento(
    request: Request,
    nome: str = Form(...),
    telefone: str = Form(...),
    cidade: str = Form(""),
    uf: str = Form(""),
    valor_conta: float = Form(...)
):

    erros = validar_orcamento_publico(nome, telefone, valor_conta)
    if erros:
        return RedirectResponse(
            url="/orcamento?erro=" + quote(erros[0]),
            status_code=303
        )

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM empresa
        LIMIT 1
    """)

    empresa = cursor.fetchone()


    resultado = calcular_orcamento(valor_conta, empresa)


    cursor.execute("""
        INSERT INTO leads
        (
            nome,
            telefone,
            cidade,
            uf,
            valor_conta,
            consumo_estimado,
            potencia_estimada_kwp,
            quantidade_modulos,
            potencia_modulo,
            geracao_estimada,
            economia_estimada,
            status,
            origem,
            data
        )
        VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """,
    (
        nome,
        telefone,
        cidade,
        uf,
        valor_conta,
        resultado["consumo_estimado"],
        resultado["potencia_estimada_kwp"],
        resultado["quantidade_modulos"],
        empresa["potencia_modulo_padrao"] if empresa and empresa["potencia_modulo_padrao"] else 620,
        resultado["geracao_estimada"],
        resultado["economia_estimada"],
        "Novo",
        "Simulador site",
        datetime.now().strftime("%d/%m/%Y %H:%M")
    ))

    conn.commit()

    conn.close()


    whatsapp_empresa = (empresa["telefone"] if empresa else "") or ""


    return templates.TemplateResponse(
        request=request,
        name="orcamento_resultado.html",
        context={
            "empresa": empresa,
            "nome": nome,
            "resultado": resultado,
            "whatsapp_empresa": whatsapp_empresa
        }
    )



# ==========================================
# LISTAR LEADS (CRM)
# ==========================================

@router.get("/leads")
async def listar_leads(request: Request):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM leads
        ORDER BY id DESC
    """)

    leads = cursor.fetchall()

    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="leads.html",
        context={
            "leads": leads
        }
    )



# ==========================================
# VISUALIZAR LEAD
# ==========================================

@router.get("/leads/{lead_id}")
async def visualizar_lead(request: Request, lead_id: int):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM leads
        WHERE id = ?
    """, (lead_id,))

    lead = cursor.fetchone()

    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="visualizar_lead.html",
        context={
            "lead": lead
        }
    )



# ==========================================
# ATUALIZAR STATUS DO LEAD
# ==========================================

@router.post("/leads/{lead_id}/status")
async def atualizar_status_lead(
    lead_id: int,
    status: str = Form(...)
):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        UPDATE leads
        SET status = ?
        WHERE id = ?
    """, (status, lead_id))

    conn.commit()

    conn.close()


    return RedirectResponse(
        f"/leads/{lead_id}",
        status_code=303
    )



# ==========================================
# CONVERTER LEAD EM CLIENTE
# ==========================================

@router.get("/leads/{lead_id}/converter")
async def converter_lead(lead_id: int):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM leads
        WHERE id = ?
    """, (lead_id,))

    lead = cursor.fetchone()


    if not lead:

        conn.close()

        return RedirectResponse(
            "/leads",
            status_code=303
        )


    if lead["cliente_id"]:

        conn.close()

        if lead["proposta_id"]:

            return RedirectResponse(
                f"/propostas/{lead['proposta_id']}",
                status_code=303
            )

        return RedirectResponse(
            f"/clientes/editar/{lead['cliente_id']}",
            status_code=303
        )


    cursor.execute("""
        INSERT INTO clientes
        (
            nome,
            telefone,
            cidade,
            uf,
            tipo_cliente,
            observacoes
        )
        VALUES
        (?,?,?,?,?,?)
    """,
    (
        lead["nome"],
        lead["telefone"],
        lead["cidade"],
        lead["uf"],
        "Pessoa Física",
        f"Lead do simulador. Conta média: R$ {lead['valor_conta']:.2f} | "
        f"Estimativa: {lead['potencia_estimada_kwp']} kWp, "
        f"economia de R$ {lead['economia_estimada']:.2f}/mês."
    ))

    cliente_id = cursor.lastrowid


    # --------------------------------------
    # Cria a proposta em rascunho, já com
    # o sistema estimado pelo simulador.
    # O valor fica em aberto para o
    # instalador preencher.
    # --------------------------------------

    cursor.execute("""
        INSERT INTO propostas
        (
            cliente_id,
            data,
            valor_total,
            status,
            validade,
            observacoes
        )
        VALUES
        (?,?,?,?,?,?)
    """,
    (
        cliente_id,
        datetime.now().strftime("%d/%m/%Y"),
        0,
        "Rascunho",
        "15 dias",
        "Gerada automaticamente a partir de um lead do simulador. "
        "Revise o sistema e preencha o valor antes de enviar ao cliente."
    ))

    proposta_id = cursor.lastrowid


    quantidade_modulos = lead["quantidade_modulos"] or 0

    potencia_modulo = lead["potencia_modulo"] or 620


    cursor.execute("""
        INSERT INTO itens_proposta
        (
            proposta_id,
            servico_id,
            descricao,
            quantidade,
            valor_unitario
        )
        VALUES
        (?,?,?,?,?)
    """,
    (
        proposta_id,
        None,
        f"Sistema fotovoltaico {lead['potencia_estimada_kwp']} kWp "
        f"({quantidade_modulos} módulos de {potencia_modulo:.0f} Wp) "
        "- valor a definir",
        1,
        0
    ))


    cursor.execute("""
        INSERT INTO sistemas_solares
        (
            proposta_id,
            potencia_kwp,
            quantidade_modulos,
            potencia_modulo,
            geracao_mensal,
            economia_mensal,
            valor_conta_atual,
            valor_conta_residual,
            observacoes
        )
        VALUES
        (?,?,?,?,?,?,?,?,?)
    """,
    (
        proposta_id,
        lead["potencia_estimada_kwp"],
        quantidade_modulos,
        potencia_modulo,
        lead["geracao_estimada"],
        lead["economia_estimada"],
        lead["valor_conta"],
        max(0, (lead["valor_conta"] or 0) - (lead["economia_estimada"] or 0)),
        "Estimativa gerada pelo simulador público a partir do valor "
        f"da conta informado (R$ {lead['valor_conta']:.2f}). "
        "Confirme consumo real e condições do local antes de fechar."
    ))


    cursor.execute("""
        UPDATE leads
        SET status = 'Convertido',
            cliente_id = ?,
            proposta_id = ?
        WHERE id = ?
    """, (cliente_id, proposta_id, lead_id))

    conn.commit()

    conn.close()


    return RedirectResponse(
        f"/propostas/{proposta_id}",
        status_code=303
    )



# ==========================================
# EXCLUIR LEAD
# ==========================================

@router.get("/leads/{lead_id}/excluir")
async def excluir_lead(lead_id: int):

    conn = conectar()

    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM leads
        WHERE id = ?
    """, (lead_id,))

    conn.commit()

    conn.close()


    return RedirectResponse(
        "/leads",
        status_code=303
    )
