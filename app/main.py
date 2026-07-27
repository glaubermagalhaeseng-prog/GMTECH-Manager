   
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from starlette.middleware.sessions import SessionMiddleware


from app.routes import dimensionador
from app.routes import clientes
from app.routes import servicos
from app.routes import propostas
from app.routes import sistema_solar
from app.routes import empresa
from app.routes import dimensionamentos

from app.database import (
    conectar,
    criar_tabela_clientes,
    criar_tabela_sistemas_solares,
    criar_tabela_servicos,
    criar_tabela_propostas,
    criar_tabela_empresa,
    atualizar_banco
)

from app.database import (
    conectar,
    criar_tabela_clientes,
    criar_tabela_sistemas_solares,
    criar_tabela_servicos,
    criar_tabela_propostas,
    criar_tabela_empresa,
    criar_tabela_dimensionamentos_solares,
    atualizar_banco
)


# =========================
# CONFIGURAÇÃO APP
# =========================

app = FastAPI(
    title="GMTECH Manager"
)


# =========================
# ARQUIVOS ESTÁTICOS
# =========================

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)


# =========================
# SESSÃO
# =========================

app.add_middleware(
    SessionMiddleware,
    secret_key="gmtech-secret-key"
)


# =========================
# TEMPLATES
# =========================

templates = Jinja2Templates(
    directory="app/templates"
)


# =========================
# ROTAS
# =========================

app.include_router(
    empresa.router
)

app.include_router(
    clientes.router
)

app.include_router(
    servicos.router
)

app.include_router(
    propostas.router
)

app.include_router(
    sistema_solar.router
)

app.include_router(
    dimensionador.router
)

app.include_router(
    sistema_solar.router
)

app.include_router(
    dimensionamentos.router
)

# =========================
# BANCO DE DADOS
# =========================

criar_tabela_clientes()

criar_tabela_servicos()

criar_tabela_propostas()

criar_tabela_empresa()

criar_tabela_sistemas_solares()

criar_tabela_dimensionamentos_solares()

atualizar_banco()



# =========================
# DASHBOARD
# =========================


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


    cursor.execute("""
        SELECT SUM(valor_total)
        FROM propostas
    """)

    valor_total_propostas = cursor.fetchone()[0] or 0


    conn.close()


    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "total_clientes": total_clientes,
            "total_servicos": total_servicos,
            "total_propostas": total_propostas,
            "valor_total_propostas": valor_total_propostas
        }
    )