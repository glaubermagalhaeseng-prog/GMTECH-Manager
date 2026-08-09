from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware

from app.routes import dimensionador
from app.routes import clientes
from app.routes import servicos
from app.routes import propostas
from app.routes import sistema_solar
from app.routes import empresa
from app.routes import dimensionamentos
from app.routes import leads
from app.routes import ordens_servico
from app.routes import auth
from app.routes import asaas_webhooks
from app.routes import roi

from app.templating import templates
from app.database import (
    conectar,
    criar_tabela_clientes,
    criar_tabela_sistemas_solares,
    criar_tabela_servicos,
    criar_tabela_propostas,
    criar_tabela_empresa,
    criar_tabela_dimensionamentos_solares,
    criar_tabela_leads,
    criar_tabela_ordens_servico,
    criar_tabela_usuarios,
    garantir_empresa_id_nas_tabelas,
    atualizar_banco,
)


app = FastAPI(
    title="GMTECH Manager"
)


app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


app.add_middleware(
    SessionMiddleware,
    secret_key="gmtech-secret-key"
)


app.include_router(empresa.router)
app.include_router(clientes.router)
app.include_router(servicos.router)
app.include_router(propostas.router)
app.include_router(sistema_solar.router)
app.include_router(dimensionador.router)
app.include_router(dimensionamentos.router)
app.include_router(leads.router)
app.include_router(ordens_servico.router)
app.include_router(auth.router)
app.include_router(asaas_webhooks.router)
app.include_router(roi.router)


criar_tabela_clientes()
criar_tabela_servicos()
criar_tabela_propostas()
criar_tabela_empresa()
criar_tabela_sistemas_solares()
criar_tabela_dimensionamentos_solares()
criar_tabela_leads()
criar_tabela_ordens_servico()
criar_tabela_usuarios()
garantir_empresa_id_nas_tabelas()
atualizar_banco()


@app.get("/")
async def home(request: Request):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM servicos")
    total_servicos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM propostas")
    total_propostas = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(valor_total) FROM propostas")
    valor_total_propostas = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM leads")
    total_leads = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status = 'Novo'")
    leads_novos = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM propostas
        WHERE status IN ('Enviada', 'Aberta', 'Orçamento', 'Rascunho')
    """)
    propostas_abertas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM propostas WHERE status = 'Aceita'
    """)
    propostas_aceitas = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM ordens_servico")
    total_ordens = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM ordens_servico
        WHERE status NOT IN ('Concluído', 'Cancelado')
    """)
    ordens_ativas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM ordens_servico WHERE status = 'Concluído'
    """)
    ordens_concluidas = cursor.fetchone()[0]

    cursor.execute("""
        SELECT status, COUNT(*) AS qtd
        FROM ordens_servico
        GROUP BY status
    """)
    os_por_status = {row["status"]: row["qtd"] for row in cursor.fetchall()}

    conn.close()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_clientes": total_clientes,
            "total_servicos": total_servicos,
            "total_propostas": total_propostas,
            "valor_total_propostas": valor_total_propostas,
            "total_leads": total_leads,
            "leads_novos": leads_novos,
            "propostas_abertas": propostas_abertas,
            "propostas_aceitas": propostas_aceitas,
            "total_ordens": total_ordens,
            "ordens_ativas": ordens_ativas,
            "ordens_concluidas": ordens_concluidas,
            "os_por_status": os_por_status,
        }
    )
