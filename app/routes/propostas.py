from fastapi.responses import FileResponse
from app.pdf.gerador import gerar_pdf_proposta
import os
from datetime import datetime
from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from app.templating import templates
from app.database import conectar
from app.auth import empresa_id_sessao


router = APIRouter()

# =========================
# NOVA PROPOSTA
# =========================

@router.get("/propostas/nova")
async def nova_proposta(request: Request, cliente_id: int = None):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM clientes
        ORDER BY nome
    """)
    clientes = cursor.fetchall()

    dimensionamentos = []
    if cliente_id:
        cursor.execute("""
            SELECT *
            FROM dimensionamentos_solares
            WHERE cliente_id = ?
            ORDER BY id DESC
        """, (cliente_id,))
        dimensionamentos = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="nova_proposta.html",
        context={
            "clientes": clientes,
            "cliente_selecionado": cliente_id,
            "dimensionamentos": dimensionamentos,
        }
    )



# =========================
# SELECIONAR CLIENTE
# =========================

@router.post("/propostas/selecionar-cliente")
async def selecionar_cliente(
    request: Request,
    cliente_id: int = Form(...)
):

    request.session["cliente_id"] = cliente_id


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )



# =========================
# ADICIONAR ITEM
# =========================

@router.post("/propostas/adicionar-item")
async def adicionar_item(
    request: Request,
    servico_id: int = Form(...),
    quantidade: float = Form(...),
    valor: float = Form(...)
):

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
        SELECT descricao
        FROM servicos
        WHERE id = ?
    """, (servico_id,))


    servico = cursor.fetchone()


    conn.close()


    itens = request.session.get(
        "itens_proposta",
        []
    )


    itens.append({

        "servico_id": servico_id,

        "descricao": servico["descricao"],

        "quantidade": quantidade,

        "valor": valor

    })


    request.session["itens_proposta"] = itens


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )



# =========================
# REMOVER ITEM
# =========================

@router.get("/propostas/remover-item/{item_id}")
async def remover_item(
    request: Request,
    item_id: int
):

    itens = request.session.get(
        "itens_proposta",
        []
    )


    if 0 <= item_id < len(itens):

        itens.pop(item_id)


    request.session["itens_proposta"] = itens


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )



# =========================
# SALVAR PROPOSTA
# =========================

@router.post("/propostas/salvar")
async def salvar_proposta(
    request: Request
):

    cliente_id = request.session.get(
        "cliente_id"
    )


    itens = request.session.get(
        "itens_proposta",
        []
    )


    if not cliente_id or not itens:

        return RedirectResponse(
            "/propostas/nova",
            status_code=303
        )


    total = sum(
        item["quantidade"] * item["valor"]
        for item in itens
    )


    conn = conectar()
    cursor = conn.cursor()



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

        total,

        "Aberta",

        "15 dias",

        ""

    ))



    proposta_id = cursor.lastrowid



    for item in itens:


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

            item["servico_id"],

            item["descricao"],

            item["quantidade"],

            item["valor"]

        ))



    conn.commit()

    conn.close()



    request.session.pop(
        "itens_proposta",
        None
    )


    request.session.pop(
        "cliente_id",
        None
    )


    return RedirectResponse(
        "/propostas/nova",
        status_code=303
    )

@router.get("/propostas")
async def listar_propostas(request: Request):

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
    SELECT 
        propostas.id,
        propostas.data,
        propostas.status,
        clientes.nome AS cliente_nome,
        SUM(itens_proposta.quantidade * itens_proposta.valor_unitario) AS valor_total

    FROM propostas

    INNER JOIN clientes

    ON propostas.cliente_id = clientes.id


    LEFT JOIN itens_proposta

    ON propostas.id = itens_proposta.proposta_id


    GROUP BY propostas.id


    ORDER BY propostas.id DESC
""")


    propostas = cursor.fetchall()


    conn.close()


    return templates.TemplateResponse(

        request=request,

        name="propostas.html",

        context={

            "propostas": propostas

        }

    )

# =========================
# GERAR PDF DA PROPOSTA
# =========================

@router.get("/propostas/{proposta_id}/pdf")
async def gerar_pdf(request: Request, proposta_id: int):

    conn = conectar()
    cursor = conn.cursor()

    # numero_endereco pode não existir em bancos antigos — usa COALESCE com numero
    cursor.execute("PRAGMA table_info(clientes)")
    cols = {row[1] for row in cursor.fetchall()}
    col_numero = "numero_endereco" if "numero_endereco" in cols else "numero"

    cursor.execute(f"""
        SELECT
            propostas.*,
            clientes.nome AS cliente_nome,
            clientes.telefone AS cliente_telefone,
            clientes.email AS cliente_email,
            clientes.cidade AS cliente_cidade,
            clientes.uf AS cliente_uf,
            clientes.rua AS cliente_rua,
            clientes.{col_numero} AS cliente_numero_endereco,
            clientes.bairro AS cliente_bairro
        FROM propostas
        INNER JOIN clientes
            ON propostas.cliente_id = clientes.id
        WHERE propostas.id = ?
    """, (proposta_id,))

    proposta = cursor.fetchone()

    if not proposta:
        conn.close()
        return RedirectResponse("/propostas", status_code=303)

    # sqlite3.Row → dict para acesso seguro no PDF
    proposta = dict(proposta)

    cursor.execute("""
        SELECT *
        FROM empresa
        LIMIT 1
    """)
    empresa_row = cursor.fetchone()
    empresa = dict(empresa_row) if empresa_row else None

    cursor.execute("""
        SELECT *
        FROM itens_proposta
        WHERE proposta_id = ?
    """, (proposta_id,))
    itens = [dict(i) for i in cursor.fetchall()]

    cursor.execute("""
        SELECT *
        FROM sistemas_solares
        WHERE proposta_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (proposta_id,))
    sistema_row = cursor.fetchone()
    sistema_solar = dict(sistema_row) if sistema_row else None

    token = _garantir_token(cursor, proposta_id)
    conn.commit()

    conn.close()

    base = str(request.base_url).rstrip("/")
    link_assinatura = f"{base}/assinar/{token}"

    caminho = f"proposta_{proposta_id}.pdf"

    gerar_pdf_proposta(
        caminho,
        proposta,
        itens,
        empresa,
        sistema_solar,
        link_assinatura
    )

    return FileResponse(
        caminho,
        media_type="application/pdf",
        filename=caminho
    )

# =========================
# VISUALIZAR PROPOSTA
# =========================

@router.get("/propostas/{proposta_id}")
async def visualizar_proposta(
    request: Request,
    proposta_id: int
):

    conn = conectar()
    cursor = conn.cursor()


    # =========================
    # DADOS DA PROPOSTA
    # =========================

    cursor.execute("""
    SELECT
        propostas.*,

        clientes.nome AS cliente_nome,
        clientes.telefone AS cliente_telefone,
        clientes.email AS cliente_email,
        clientes.cidade AS cliente_cidade,
        clientes.uf AS cliente_uf

    FROM propostas

    INNER JOIN clientes

    ON propostas.cliente_id = clientes.id

    WHERE propostas.id = ?

    """, (proposta_id,))


    proposta = cursor.fetchone()



    # =========================
    # ITENS DA PROPOSTA
    # =========================

    cursor.execute("""
        SELECT *

        FROM itens_proposta

        WHERE proposta_id = ?

    """, (proposta_id,))


    itens = cursor.fetchall()



    # =========================
    # SISTEMAS SOLARES
    # =========================

    cursor.execute("""
        SELECT *
        FROM sistemas_solares
        WHERE proposta_id = ?
    """, (proposta_id,))
    sistemas_solares = cursor.fetchall()

    cursor.execute("SELECT * FROM empresa LIMIT 1")
    empresa = cursor.fetchone()

    cursor.execute("""
        SELECT id FROM ordens_servico
        WHERE proposta_id = ?
        LIMIT 1
    """, (proposta_id,))
    ordem = cursor.fetchone()

    conn.close()

    # Links WhatsApp para o cliente
    from urllib.parse import quote as url_quote

    tel = (proposta["cliente_telefone"] or "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if tel and not tel.startswith("55"):
        tel = "55" + tel.lstrip("0")

    nome_emp = (
        empresa["nome_fantasia"]
        if empresa and empresa["nome_fantasia"]
        else "GMTECH"
    )
    valor_fmt = f"{(proposta['valor_total'] or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    mensagem = (
        f"Olá {proposta['cliente_nome']}! Segue a proposta comercial "
        f"PROP-{proposta_id:04d} da {nome_emp}. "
        f"Valor: R$ {valor_fmt}."
    )
    whatsapp_url = f"https://wa.me/{tel}?text={url_quote(mensagem)}" if tel else None

    # WhatsApp com link de pagamento Asaas
    whatsapp_pagamento_url = None
    invoice = None
    try:
        invoice = proposta["asaas_invoice_url"]
    except (KeyError, IndexError, TypeError):
        invoice = None
    if tel and invoice:
        msg_pag = (
            f"Olá {proposta['cliente_nome']}! Segue o link para pagamento "
            f"da proposta PROP-{proposta_id:04d} ({nome_emp}).\n"
            f"Valor: R$ {valor_fmt}.\n"
            f"Pague com PIX, boleto ou cartão:\n{invoice}"
        )
        whatsapp_pagamento_url = f"https://wa.me/{tel}?text={url_quote(msg_pag)}"

    return templates.TemplateResponse(
        request=request,
        name="visualizar_proposta.html",
        context={
            "proposta": proposta,
            "itens": itens,
            "sistemas_solares": sistemas_solares,
            "empresa": empresa,
            "ordem_existente": ordem,
            "whatsapp_url": whatsapp_url,
            "whatsapp_pagamento_url": whatsapp_pagamento_url,
        }
    )


# =========================
# ATUALIZAR ITEM DA PROPOSTA
# (quantidade e valor unitário)
# =========================

@router.post("/propostas/{proposta_id}/itens/{item_id}/atualizar")
async def atualizar_item_proposta(
    proposta_id: int,
    item_id: int,
    quantidade: float = Form(...),
    valor_unitario: float = Form(...)
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE itens_proposta
        SET quantidade = ?,
            valor_unitario = ?
        WHERE id = ?
          AND proposta_id = ?
    """, (quantidade, valor_unitario, item_id, proposta_id))

    cursor.execute("""
        SELECT SUM(quantidade * valor_unitario) AS total
        FROM itens_proposta
        WHERE proposta_id = ?
    """, (proposta_id,))

    total = cursor.fetchone()["total"] or 0

    cursor.execute("""
        UPDATE propostas
        SET valor_total = ?
        WHERE id = ?
    """, (total, proposta_id))

    conn.commit()
    conn.close()

    return RedirectResponse(
        f"/propostas/{proposta_id}",
        status_code=303
    )


# =========================
# ATUALIZAR STATUS DA PROPOSTA
# (Aceita → cria OS automaticamente)
# =========================

@router.post("/propostas/{proposta_id}/status")
async def atualizar_status_proposta(
    proposta_id: int,
    status: str = Form(...)
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE propostas
        SET status = ?
        WHERE id = ?
    """, (status, proposta_id))

    conn.commit()

    # Quando marcada como Aceita, cria a Ordem de Serviço automaticamente
    if status == "Aceita":
        cursor.execute("""
            SELECT id FROM ordens_servico
            WHERE proposta_id = ?
            LIMIT 1
        """, (proposta_id,))
        ja_existe = cursor.fetchone()

        if not ja_existe:
            cursor.execute("SELECT * FROM propostas WHERE id = ?", (proposta_id,))
            proposta = cursor.fetchone()

            if proposta:
                cursor.execute("""
                    SELECT * FROM sistemas_solares
                    WHERE proposta_id = ?
                    ORDER BY id DESC LIMIT 1
                """, (proposta_id,))
                sistema = cursor.fetchone()

                cursor.execute("""
                    SELECT descricao, quantidade, valor_unitario
                    FROM itens_proposta WHERE proposta_id = ?
                """, (proposta_id,))
                itens = cursor.fetchall()

                linhas_desc = []
                for item in itens:
                    total_item = (item["quantidade"] or 0) * (item["valor_unitario"] or 0)
                    linhas_desc.append(
                        f"- {item['descricao']} (qtd {item['quantidade']}) — R$ {total_item:.2f}"
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
                        proposta_id, cliente_id, status, data_criacao,
                        valor_fechado, potencia_kwp, quantidade_modulos,
                        descricao, observacoes
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
                    "Criada automaticamente quando a proposta foi marcada como Aceita.",
                ))
                conn.commit()
                ordem_id = cursor.lastrowid
                conn.close()
                return RedirectResponse(
                    f"/ordens-servico/{ordem_id}",
                    status_code=303
                )

    conn.close()
    return RedirectResponse(
        f"/propostas/{proposta_id}",
        status_code=303
    )



# =========================
# EXCLUIR PROPOSTA
# =========================

@router.get("/propostas/{proposta_id}/excluir")
async def excluir_proposta(proposta_id: int):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM itens_proposta WHERE proposta_id = ?", (proposta_id,))
    cursor.execute("DELETE FROM sistemas_solares WHERE proposta_id = ?", (proposta_id,))
    cursor.execute("DELETE FROM ordens_servico WHERE proposta_id = ?", (proposta_id,))
    cursor.execute("DELETE FROM propostas WHERE id = ?", (proposta_id,))

    conn.commit()
    conn.close()

    return RedirectResponse("/propostas", status_code=303)


# =========================
# ASSINATURA DIGITAL
# =========================

def _garantir_token(cursor, proposta_id: int) -> str:
    """Garante que a proposta tenha token de assinatura."""
    import secrets
    cursor.execute(
        "SELECT token_assinatura FROM propostas WHERE id = ?",
        (proposta_id,)
    )
    row = cursor.fetchone()
    if row and row["token_assinatura"]:
        return row["token_assinatura"]
    token = secrets.token_urlsafe(24)
    cursor.execute(
        "UPDATE propostas SET token_assinatura = ? WHERE id = ?",
        (token, proposta_id)
    )
    return token


@router.get("/propostas/{proposta_id}/gerar-link-assinatura")
async def gerar_link_assinatura(request: Request, proposta_id: int):
    """Gera (ou reutiliza) o token e mostra o link para enviar ao cliente."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM propostas WHERE id = ?", (proposta_id,))
    proposta = cursor.fetchone()
    if not proposta:
        conn.close()
        return RedirectResponse("/propostas", status_code=303)

    token = _garantir_token(cursor, proposta_id)
    conn.commit()
    conn.close()

    base = str(request.base_url).rstrip("/")
    link = f"{base}/assinar/{token}"

    return templates.TemplateResponse(
        request=request,
        name="link_assinatura.html",
        context={
            "proposta_id": proposta_id,
            "link": link,
            "token": token,
        }
    )


@router.get("/assinar/{token}")
async def pagina_assinatura(request: Request, token: str):
    """Página pública para o cliente assinar a proposta."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*,
               c.nome AS cliente_nome,
               c.telefone AS cliente_telefone,
               c.email AS cliente_email,
               c.cidade AS cliente_cidade,
               c.uf AS cliente_uf
        FROM propostas p
        INNER JOIN clientes c ON c.id = p.cliente_id
        WHERE p.token_assinatura = ?
    """, (token,))
    proposta = cursor.fetchone()

    if not proposta:
        conn.close()
        return templates.TemplateResponse(
            request=request,
            name="assinatura_erro.html",
            context={"mensagem": "Link de assinatura inválido ou expirado."}
        )

    cursor.execute("""
        SELECT * FROM sistemas_solares
        WHERE proposta_id = ?
        ORDER BY id DESC LIMIT 1
    """, (proposta["id"],))
    sistema = cursor.fetchone()

    cursor.execute("SELECT * FROM empresa LIMIT 1")
    empresa = cursor.fetchone()
    conn.close()

    ja_assinada = bool(proposta["assinatura_data"])

    return templates.TemplateResponse(
        request=request,
        name="assinar_proposta.html",
        context={
            "proposta": proposta,
            "sistema": sistema,
            "empresa": empresa,
            "token": token,
            "ja_assinada": ja_assinada,
        }
    )


@router.post("/assinar/{token}")
async def confirmar_assinatura(
    request: Request,
    token: str,
    nome: str = Form(...),
    cpf: str = Form(...),
    aceite: str = Form(...),
):
    """Cliente confirma a assinatura digital."""
    if aceite != "sim":
        return RedirectResponse(
            f"/assinar/{token}?erro=Você precisa aceitar os termos.",
            status_code=303
        )

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM propostas WHERE token_assinatura = ?",
        (token,)
    )
    proposta = cursor.fetchone()

    if not proposta:
        conn.close()
        return RedirectResponse("/assinar/invalido", status_code=303)

    if proposta["assinatura_data"]:
        conn.close()
        return RedirectResponse(f"/assinar/{token}", status_code=303)

    # IP do cliente
    ip = request.client.host if request.client else ""
    if "x-forwarded-for" in request.headers:
        ip = request.headers["x-forwarded-for"].split(",")[0].strip()

    agora = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    cursor.execute("""
        UPDATE propostas SET
            status = 'Aceita',
            assinatura_nome = ?,
            assinatura_cpf = ?,
            assinatura_data = ?,
            assinatura_ip = ?
        WHERE id = ?
    """, (nome.strip(), cpf.strip(), agora, ip, proposta["id"]))

    # Cria OS automaticamente
    cursor.execute("""
        SELECT id FROM ordens_servico WHERE proposta_id = ? LIMIT 1
    """, (proposta["id"],))
    if not cursor.fetchone():
        cursor.execute("""
            SELECT * FROM sistemas_solares
            WHERE proposta_id = ? ORDER BY id DESC LIMIT 1
        """, (proposta["id"],))
        sistema = cursor.fetchone()

        cursor.execute("""
            SELECT descricao, quantidade, valor_unitario
            FROM itens_proposta WHERE proposta_id = ?
        """, (proposta["id"],))
        itens = cursor.fetchall()

        linhas = []
        for item in itens:
            tot = (item["quantidade"] or 0) * (item["valor_unitario"] or 0)
            linhas.append(f"- {item['descricao']} (qtd {item['quantidade']}) — R$ {tot:.2f}")
        if sistema:
            linhas.insert(
                0,
                f"Sistema fotovoltaico {sistema['potencia_kwp']} kWp — "
                f"{sistema['quantidade_modulos']} módulos"
            )
        descricao = "\n".join(linhas) if linhas else "Ordem gerada após assinatura digital."

        cursor.execute("""
            INSERT INTO ordens_servico
            (
                proposta_id, cliente_id, status, data_criacao,
                valor_fechado, potencia_kwp, quantidade_modulos,
                descricao, observacoes
            )
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (
            proposta["id"],
            proposta["cliente_id"],
            "Aguardando início",
            datetime.now().strftime("%d/%m/%Y"),
            proposta["valor_total"] or 0,
            sistema["potencia_kwp"] if sistema else None,
            sistema["quantidade_modulos"] if sistema else None,
            descricao,
            f"Criada automaticamente após assinatura digital de {nome} em {agora}.",
        ))

    conn.commit()
    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="assinatura_sucesso.html",
        context={
            "nome": nome,
            "data": agora,
        }
    )
