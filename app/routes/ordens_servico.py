from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from datetime import datetime

from app.templating import templates
from app.database import conectar


router = APIRouter()

STATUS_OS = [
    "Aguardando início",
    "Em instalação",
    "Homologação",
    "Concluído",
    "Cancelado",
]


# ==========================================
# LISTAR ORDENS DE SERVIÇO
# ==========================================

@router.get("/ordens-servico")
async def listar_ordens(request: Request, view: str = "lista"):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            os.*,
            c.nome AS cliente_nome,
            c.telefone AS cliente_telefone,
            c.cidade AS cliente_cidade
        FROM ordens_servico os
        INNER JOIN clientes c ON c.id = os.cliente_id
        ORDER BY os.id DESC
    """)

    ordens = cursor.fetchall()
    conn.close()

    ordens_por_status = {s: [] for s in STATUS_OS}
    for o in ordens:
        st = o["status"] or "Aguardando início"
        if st not in ordens_por_status:
            ordens_por_status[st] = []
        ordens_por_status[st].append(o)

    return templates.TemplateResponse(
        request=request,
        name="ordens_servico.html",
        context={
            "ordens": ordens,
            "status_lista": STATUS_OS,
            "ordens_por_status": ordens_por_status,
            "view": view if view in ("lista", "kanban") else "lista",
        }
    )


# ==========================================
# VISUALIZAR ORDEM
# ==========================================

@router.get("/ordens-servico/{ordem_id}")
async def visualizar_ordem(request: Request, ordem_id: int):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            os.*,
            c.nome AS cliente_nome,
            c.telefone AS cliente_telefone,
            c.email AS cliente_email,
            c.cidade AS cliente_cidade,
            c.uf AS cliente_uf,
            c.rua AS cliente_rua,
            c.bairro AS cliente_bairro
        FROM ordens_servico os
        INNER JOIN clientes c ON c.id = os.cliente_id
        WHERE os.id = ?
    """, (ordem_id,))

    ordem = cursor.fetchone()

    if not ordem:
        conn.close()
        return RedirectResponse("/ordens-servico", status_code=303)

    cursor.execute("""
        SELECT *
        FROM itens_proposta
        WHERE proposta_id = ?
    """, (ordem["proposta_id"],))

    itens = cursor.fetchall()

    cursor.execute("""
        SELECT *
        FROM sistemas_solares
        WHERE proposta_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (ordem["proposta_id"],))

    sistema = cursor.fetchone()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="visualizar_ordem.html",
        context={
            "ordem": ordem,
            "itens": itens,
            "sistema": sistema,
            "status_lista": STATUS_OS,
        }
    )


# ==========================================
# ATUALIZAR STATUS
# ==========================================

@router.post("/ordens-servico/{ordem_id}/status")
async def atualizar_status_ordem(
    ordem_id: int,
    status: str = Form(...),
    data_inicio: str = Form(""),
    data_prevista: str = Form(""),
    data_conclusao: str = Form(""),
    responsavel: str = Form(""),
    observacoes: str = Form(""),
):

    conn = conectar()
    cursor = conn.cursor()

    # Se mudou para Em instalação e ainda não tem data_inicio, preenche hoje
    cursor.execute("SELECT * FROM ordens_servico WHERE id = ?", (ordem_id,))
    ordem = cursor.fetchone()

    if not ordem:
        conn.close()
        return RedirectResponse("/ordens-servico", status_code=303)

    hoje = datetime.now().strftime("%d/%m/%Y")

    inicio = data_inicio or ordem["data_inicio"]
    prevista = data_prevista or ordem["data_prevista"]
    conclusao = data_conclusao or ordem["data_conclusao"]

    if status == "Em instalação" and not inicio:
        inicio = hoje

    if status == "Concluído" and not conclusao:
        conclusao = hoje

    cursor.execute("""
        UPDATE ordens_servico
        SET status = ?,
            data_inicio = ?,
            data_prevista = ?,
            data_conclusao = ?,
            responsavel = ?,
            observacoes = ?
        WHERE id = ?
    """, (
        status,
        inicio,
        prevista,
        conclusao,
        responsavel or ordem["responsavel"],
        observacoes if observacoes != "" else ordem["observacoes"],
        ordem_id,
    ))

    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/ordens-servico/{ordem_id}",
        status_code=303
    )


# ==========================================
# CRIAR OS A PARTIR DE PROPOSTA ACEITA
# ==========================================

@router.post("/propostas/{proposta_id}/criar-ordem")
async def criar_ordem_de_proposta(proposta_id: int):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM propostas
        WHERE id = ?
    """, (proposta_id,))

    proposta = cursor.fetchone()

    if not proposta:
        conn.close()
        return RedirectResponse("/propostas", status_code=303)

    # Já existe OS para esta proposta?
    cursor.execute("""
        SELECT id FROM ordens_servico
        WHERE proposta_id = ?
        LIMIT 1
    """, (proposta_id,))

    existente = cursor.fetchone()

    if existente:
        conn.close()
        return RedirectResponse(
            f"/ordens-servico/{existente['id']}",
            status_code=303
        )

    cursor.execute("""
        SELECT *
        FROM sistemas_solares
        WHERE proposta_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (proposta_id,))

    sistema = cursor.fetchone()

    cursor.execute("""
        SELECT descricao, quantidade, valor_unitario
        FROM itens_proposta
        WHERE proposta_id = ?
    """, (proposta_id,))

    itens = cursor.fetchall()

    linhas_desc = []
    for item in itens:
        total_item = (item["quantidade"] or 0) * (item["valor_unitario"] or 0)
        linhas_desc.append(
            f"- {item['descricao']} "
            f"(qtd {item['quantidade']}) — R$ {total_item:.2f}"
        )

    if sistema:
        linhas_desc.insert(
            0,
            f"Sistema fotovoltaico {sistema['potencia_kwp']} kWp — "
            f"{sistema['quantidade_modulos']} módulos"
        )

    descricao = "\n".join(linhas_desc) if linhas_desc else (
        proposta["observacoes"] or "Ordem gerada a partir da proposta aceita."
    )

    potencia = sistema["potencia_kwp"] if sistema else None
    qtd_modulos = sistema["quantidade_modulos"] if sistema else None

    cursor.execute("""
        INSERT INTO ordens_servico
        (
            proposta_id,
            cliente_id,
            status,
            data_criacao,
            valor_fechado,
            potencia_kwp,
            quantidade_modulos,
            descricao,
            observacoes
        )
        VALUES (?,?,?,?,?,?,?,?,?)
    """, (
        proposta_id,
        proposta["cliente_id"],
        "Aguardando início",
        datetime.now().strftime("%d/%m/%Y"),
        proposta["valor_total"] or 0,
        potencia,
        qtd_modulos,
        descricao,
        "Criada automaticamente a partir da proposta aceita.",
    ))

    ordem_id = cursor.lastrowid

    # Marca proposta como Aceita se ainda não estiver
    if proposta["status"] != "Aceita":
        cursor.execute("""
            UPDATE propostas SET status = 'Aceita' WHERE id = ?
        """, (proposta_id,))

    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/ordens-servico/{ordem_id}",
        status_code=303
    )


# ==========================================
# EXCLUIR ORDEM
# ==========================================

@router.get("/ordens-servico/{ordem_id}/excluir")
async def excluir_ordem(ordem_id: int):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM ordens_servico WHERE id = ?", (ordem_id,))
    conn.commit()
    conn.close()

    return RedirectResponse("/ordens-servico", status_code=303)
