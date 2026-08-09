from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from datetime import datetime

from app.templating import templates
from app.database import conectar


router = APIRouter()


# ==========================================
# LISTAR DIMENSIONAMENTOS
# ==========================================

@router.get("/dimensionamentos")
async def listar_dimensionamentos(request: Request):


    conn = conectar()

    cursor = conn.cursor()



    cursor.execute("""
        SELECT

            dimensionamentos_solares.*,

            clientes.nome AS cliente_nome


        FROM dimensionamentos_solares


        INNER JOIN clientes

        ON dimensionamentos_solares.cliente_id = clientes.id


        ORDER BY dimensionamentos_solares.id DESC

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

@router.get("/dimensionamentos/{dimensionamento_id}")
async def visualizar_dimensionamento(
    request: Request,
    dimensionamento_id: int
):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
        SELECT

            dimensionamentos_solares.*,

            clientes.nome AS cliente_nome,
            clientes.telefone AS cliente_telefone,
            clientes.email AS cliente_email


        FROM dimensionamentos_solares


        INNER JOIN clientes

        ON dimensionamentos_solares.cliente_id = clientes.id


        WHERE dimensionamentos_solares.id = ?

    """, (dimensionamento_id,))


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
# GERAR PROPOSTA A PARTIR DO DIMENSIONAMENTO
# ==========================================

@router.get("/dimensionamentos/{dimensionamento_id}/gerar-proposta")
async def gerar_proposta_dimensionamento(
    dimensionamento_id: int
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM dimensionamentos_solares
        WHERE id = ?
    """, (dimensionamento_id,))

    dimensionamento = cursor.fetchone()

    if not dimensionamento:
        conn.close()
        return RedirectResponse(
            "/dimensionamentos",
            status_code=303
        )

    # Conta estimada a partir de consumo x tarifa (quando houver)
    tarifa = dimensionamento["tarifa_energia"] or 0
    consumo = dimensionamento["consumo_medio"] or 0
    economia = dimensionamento["economia_liquida"] or dimensionamento["economia_estimada"] or 0
    valor_conta_atual = round(consumo * tarifa, 2) if tarifa and consumo else 0
    valor_conta_residual = max(0, round(valor_conta_atual - economia, 2))

    potencia = dimensionamento["potencia_final_kwp"] or 0
    qtd_modulos = dimensionamento["quantidade_modulos"] or 0
    pot_modulo = dimensionamento["potencia_modulo"] or 0
    fab_mod = dimensionamento["fabricante_modulo"] or ""
    mod_mod = dimensionamento["modelo_modulo"] or ""
    fab_inv = dimensionamento["fabricante_inversor"] or ""
    mod_inv = dimensionamento["modelo_inversor"] or ""
    pot_inv = dimensionamento["potencia_inversor"] or 0
    geracao = dimensionamento["geracao_estimada"] or 0

    # Preço por kWp da empresa (precificação automática)
    cursor.execute("SELECT preco_por_kwp FROM empresa LIMIT 1")
    emp_row = cursor.fetchone()
    preco_kwp = (emp_row["preco_por_kwp"] if emp_row and emp_row["preco_por_kwp"] else 4500) or 4500
    valor_sistema = round(float(potencia) * float(preco_kwp), 2)

    import secrets
    token = secrets.token_urlsafe(24)

    # Cria proposta já precificada
    cursor.execute("""
        INSERT INTO propostas
        (
            cliente_id,
            data,
            valor_total,
            status,
            validade,
            observacoes,
            token_assinatura
        )
        VALUES (?,?,?,?,?,?,?)
    """, (
        dimensionamento["cliente_id"],
        datetime.now().strftime("%d/%m/%Y"),
        valor_sistema,
        "Rascunho",
        "15 dias",
        f"Proposta gerada pelo dimensionador solar #{dimensionamento_id}. "
        f"Sistema {potencia} kWp × R$ {preco_kwp:,.2f}/kWp = R$ {valor_sistema:,.2f}.",
        token,
    ))

    proposta_id = cursor.lastrowid

    # Um único item descritivo (sem fatiar preço por produto)
    inv_txt = f"{fab_inv} {mod_inv}".strip() or "padrão do projeto"
    if pot_inv:
        inv_txt = f"{inv_txt} {pot_inv} kW".strip()
    mod_txt = f"{fab_mod} {mod_mod}".strip()
    if pot_modulo:
        mod_txt = f"{mod_txt} {int(pot_modulo)}W".strip() if pot_modulo else mod_txt
    mod_txt = mod_txt.strip() or f"{int(pot_modulo)}W" if pot_modulo else "padrão do projeto"

    descricao_sistema = (
        f"Sistema fotovoltaico de {potencia} kWp composto por: "
        f"{int(qtd_modulos or 0)} módulos solares {mod_txt}; "
        f"1 inversor {inv_txt}; "
        f"estrutura para fixação dos módulos; "
        f"cabos e string box; "
        f"projeto elétrico; "
        f"ART; "
        f"homologação junto à concessionária; "
        f"fornecimento e instalação completa."
    )

    cursor.execute("""
        INSERT INTO itens_proposta
        (proposta_id, descricao, quantidade, valor_unitario)
        VALUES (?,?,?,?)
    """, (
        proposta_id,
        descricao_sistema,
        1,
        valor_sistema,
    ))

    # Sistema solar completo (tudo do dimensionador)
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
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        proposta_id,
        potencia,
        qtd_modulos,
        pot_modulo,
        fab_mod,
        mod_inv if mod_inv else f"{fab_inv} {mod_inv}".strip(),
        pot_inv,
        geracao,
        economia,
        valor_conta_atual,
        valor_conta_residual,
        "Dados importados automaticamente do dimensionador solar. "
        f"Modalidade: {dimensionamento['modalidade'] or '—'}. "
        f"Ano conexão: {dimensionamento['ano_conexao'] or '—'}."
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/propostas/{proposta_id}",
        status_code=303
    )
