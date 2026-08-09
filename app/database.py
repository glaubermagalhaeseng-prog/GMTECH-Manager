import sqlite3


DATABASE = "app/gmtech.db"


def conectar():

    conn = sqlite3.connect(
        DATABASE,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn



# ==========================================
# CLIENTES
# ==========================================

def criar_tabela_clientes():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        numero TEXT,

        nome TEXT NOT NULL,

        cpf_cnpj TEXT,

        telefone TEXT,

        email TEXT,

        rua TEXT,

        numero_endereco TEXT,

        bairro TEXT,

        cidade TEXT,

        uf TEXT,

        tipo_cliente TEXT,

        unidade_consumidora TEXT,

        observacoes TEXT

    )
    """)

    conn.commit()
    conn.close()



# ==========================================
# SERVIÇOS
# ==========================================

def criar_tabela_servicos():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicos (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        descricao TEXT,

        categoria TEXT,

        valor REAL

    )
    """)

    conn.commit()
    conn.close()



# ==========================================
# PROPOSTAS
# ==========================================

def criar_tabela_propostas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS propostas (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        cliente_id INTEGER NOT NULL,

        data TEXT,

        valor_total REAL,

        status TEXT,

        validade TEXT,

        observacoes TEXT,


        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id)

    )
    """)


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_proposta (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proposta_id INTEGER NOT NULL,

        servico_id INTEGER,

        descricao TEXT NOT NULL,

        quantidade REAL DEFAULT 1,

        valor_unitario REAL,


        FOREIGN KEY(proposta_id)
        REFERENCES propostas(id),


        FOREIGN KEY(servico_id)
        REFERENCES servicos(id)

    )
    """)


    conn.commit()
    conn.close()



# ==========================================
# EMPRESA
# ==========================================

def criar_tabela_empresa():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS empresa (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        razao_social TEXT,

        nome_fantasia TEXT,

        cnpj TEXT,

        responsavel TEXT,

        telefone TEXT,

        email TEXT,

        endereco TEXT,

        cidade TEXT,

        uf TEXT,

        cft TEXT,

        logo TEXT

    )
    """)


    cursor.execute("""
    INSERT OR IGNORE INTO empresa(id)
    VALUES (1)
    """)


    conn.commit()
    conn.close()



# ==========================================
# SISTEMA SOLAR
# ==========================================

def criar_tabela_sistemas_solares():

    conn = conectar()
    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sistemas_solares (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proposta_id INTEGER NOT NULL,

        potencia_kwp REAL,

        quantidade_modulos INTEGER,

        potencia_modulo INTEGER,

        fabricante_modulo TEXT,

        modelo_inversor TEXT,

        potencia_inversor REAL,

        geracao_mensal REAL,

        economia_mensal REAL,

        valor_conta_atual REAL,

        valor_conta_residual REAL,

        observacoes TEXT,


        FOREIGN KEY(proposta_id)
        REFERENCES propostas(id)

    )
    """)


    conn.commit()
    conn.close()

# ==========================================
# DIMENSIONADOR SOLAR
# ==========================================

def criar_tabela_dimensionamentos_solares():

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dimensionamentos_solares (

        id INTEGER PRIMARY KEY AUTOINCREMENT,


        cliente_id INTEGER NOT NULL,


        data TEXT,


        consumo_medio REAL,


        percentual_compensacao REAL,


        produtividade REAL,


        potencia_calculada_kwp REAL,


        quantidade_modulos INTEGER,


        potencia_modulo INTEGER,


        potencia_final_kwp REAL,


        geracao_estimada REAL,


        tarifa_energia REAL,


        economia_estimada REAL,


        status TEXT,


        observacoes TEXT,


        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id)

    )
    """)


    conn.commit()

    conn.close()



# ==========================================
# LEADS (SIMULADOR PÚBLICO)
# ==========================================

def criar_tabela_leads():

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leads (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT NOT NULL,

        telefone TEXT NOT NULL,

        email TEXT,

        cidade TEXT,

        uf TEXT,

        valor_conta REAL,

        consumo_estimado REAL,

        potencia_estimada_kwp REAL,

        quantidade_modulos INTEGER,

        potencia_modulo REAL,

        geracao_estimada REAL,

        economia_estimada REAL,

        status TEXT DEFAULT 'Novo',

        origem TEXT DEFAULT 'Simulador site',

        data TEXT,

        observacoes TEXT,

        cliente_id INTEGER,

        proposta_id INTEGER,


        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id),

        FOREIGN KEY(proposta_id)
        REFERENCES propostas(id)

    )
    """)


    conn.commit()

    conn.close()



# ==========================================
# COLUNAS DO DIMENSIONADOR (Fio B / Lei 14.300)
# ==========================================

_COLUNAS_DIMENSIONAMENTO = [
    ("ano_conexao", "INTEGER"),
    ("economia_bruta", "REAL"),
    ("custo_fio_b", "REAL"),
    ("economia_liquida", "REAL"),
    ("margem_tecnica", "REAL"),
    ("modalidade", "TEXT"),
    ("quantidade_beneficiarias", "INTEGER"),
    ("consumo_beneficiarias", "REAL"),
    ("percentual_fio_b", "REAL"),
    ("consumo_corrigido", "REAL"),
    ("fabricante_modulo", "TEXT"),
    ("modelo_modulo", "TEXT"),
    ("fabricante_inversor", "TEXT"),
    ("modelo_inversor", "TEXT"),
    ("potencia_inversor", "REAL"),
    ("fatura_arquivo", "TEXT"),
    ("valor_conta_fatura", "REAL"),
    ("consumo_total_projeto", "REAL"),
]


def garantir_colunas_dimensionamentos(conn=None, cursor=None):
    """Cria colunas faltantes usadas em /dimensionador/salvar (seguro repetir)."""
    fechar = False
    if conn is None or cursor is None:
        conn = conectar()
        cursor = conn.cursor()
        fechar = True
    for col, tipo in _COLUNAS_DIMENSIONAMENTO:
        try:
            cursor.execute(
                f"ALTER TABLE dimensionamentos_solares ADD COLUMN {col} {tipo}"
            )
            conn.commit()
        except Exception:
            pass
    if fechar:
        try:
            conn.close()
        except Exception:
            pass


# ==========================================
# ATUALIZAÇÕES DO BANCO
# ==========================================

def atualizar_banco():

    conn = conectar()

    cursor = conn.cursor()

    try:
        garantir_colunas_dimensionamentos(conn=conn, cursor=cursor)
    except Exception:
        pass

    

    # --------------------------------------
    # Campo responsavel na empresa
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE empresa
            ADD COLUMN responsavel TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    # --------------------------------------
    # Campo descricao nos itens da proposta
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE itens_proposta
            ADD COLUMN descricao TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    # --------------------------------------
    # Campos adicionais dimensionamento solar
    # --------------------------------------


    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN fabricante_modulo TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


            # --------------------------------------
    # Consumo total do projeto solar
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN consumo_total_projeto REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass

    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN modelo_modulo TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN fabricante_inversor TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN modelo_inversor TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN potencia_inversor REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass

    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN margem_tecnica REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass

        # --------------------------------------
    # Campos Lei 14.300 / Beneficiárias
    # --------------------------------------


    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN modalidade TEXT
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass

    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN quantidade_beneficiarias INTEGER
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN consumo_beneficiarias REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN percentual_fio_b REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass



    try:

        cursor.execute("""
            ALTER TABLE dimensionamentos_solares
            ADD COLUMN consumo_corrigido REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass

    # --------------------------------------
    # Configurações padrão do simulador
    # público de orçamento (/orcamento)
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE empresa
            ADD COLUMN tarifa_padrao REAL DEFAULT 0.85
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE empresa
            ADD COLUMN produtividade_padrao REAL DEFAULT 125
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE empresa
            ADD COLUMN potencia_modulo_padrao REAL DEFAULT 620
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE empresa
            ADD COLUMN margem_padrao REAL DEFAULT 10
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    # --------------------------------------
    # Novas colunas em leads (numero de
    # modulos, modulo padrao usado e
    # vinculo com a proposta gerada)
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE leads
            ADD COLUMN quantidade_modulos INTEGER
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE leads
            ADD COLUMN potencia_modulo REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE leads
            ADD COLUMN proposta_id INTEGER
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    # --------------------------------------
    # Novas colunas em sistemas_solares
    # (comparativo de conta antes/depois
    # usado na proposta em PDF)
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE sistemas_solares
            ADD COLUMN valor_conta_atual REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass


    try:

        cursor.execute("""
            ALTER TABLE sistemas_solares
            ADD COLUMN valor_conta_residual REAL
        """)

        conn.commit()


    except sqlite3.OperationalError:

        pass

    # --------------------------------------
    
    # numero_endereco (bancos antigos só tinham "numero")
    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN numero_endereco TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("""
            UPDATE clientes
            SET numero_endereco = numero
            WHERE (numero_endereco IS NULL OR numero_endereco = '')
              AND numero IS NOT NULL AND numero != ''
        """)
        conn.commit()
    except sqlite3.OperationalError:
        pass

    
    # Fatura anexada ao dimensionamento
    for col, tipo in [
        ("fatura_arquivo", "TEXT"),
        ("valor_conta_fatura", "REAL"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE dimensionamentos_solares ADD COLUMN {col} {tipo}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("ALTER TABLE clientes ADD COLUMN fatura_arquivo TEXT")
        conn.commit()
    except sqlite3.OperationalError:
        pass


    
    # Asaas (pagamento)
    for col, tipo in [
        ("asaas_api_key", "TEXT"),
        ("asaas_webhook_token", "TEXT"),
        ("asaas_ambiente", "TEXT DEFAULT 'sandbox'"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE empresa ADD COLUMN {col} {tipo}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    for col, tipo in [
        ("asaas_payment_id", "TEXT"),
        ("asaas_invoice_url", "TEXT"),
        ("asaas_status", "TEXT"),
        ("pagamento_status", "TEXT"),
        ("pago_em", "TEXT"),
    ]:
        try:
            cursor.execute(f"ALTER TABLE propostas ADD COLUMN {col} {tipo}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS asaas_webhook_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT UNIQUE,
                event_type TEXT,
                payment_id TEXT,
                payload TEXT,
                processado_em TEXT,
                resultado TEXT
            )
        """)
        conn.commit()
    except sqlite3.OperationalError:
        pass


    # Preço por kWp (precificação automática)
    # --------------------------------------

    try:
        cursor.execute("""
            ALTER TABLE empresa
            ADD COLUMN preco_por_kwp REAL DEFAULT 4500
        """)
        conn.commit()
    except sqlite3.OperationalError:
        pass

    # --------------------------------------
    # Assinatura digital da proposta
    # --------------------------------------

    for col in (
        "token_assinatura TEXT",
        "assinatura_nome TEXT",
        "assinatura_cpf TEXT",
        "assinatura_data TEXT",
        "assinatura_ip TEXT",
    ):
        try:
            cursor.execute(f"ALTER TABLE propostas ADD COLUMN {col}")
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # --------------------------------------
    # Ajusta itens_proposta para permitir
    # itens sem serviço vinculado
    # --------------------------------------

    try:

        cursor.execute("""
            ALTER TABLE itens_proposta
            RENAME TO itens_proposta_old
        """)


        cursor.execute("""
            CREATE TABLE itens_proposta (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                proposta_id INTEGER NOT NULL,

                servico_id INTEGER,

                descricao TEXT NOT NULL,

                quantidade REAL DEFAULT 1,

                valor_unitario REAL,

                FOREIGN KEY(proposta_id)
                REFERENCES propostas(id),

                FOREIGN KEY(servico_id)
                REFERENCES servicos(id)

            )
        """)


        cursor.execute("""
            INSERT INTO itens_proposta (
                id,
                proposta_id,
                servico_id,
                descricao,
                quantidade,
                valor_unitario
            )

            SELECT

                id,
                proposta_id,
                servico_id,
                COALESCE(descricao, 'Item sem descrição'),
                quantidade,
                valor_unitario

            FROM itens_proposta_old
        """)

        cursor.execute("""
            DROP TABLE itens_proposta_old
        """)


        conn.commit()


    except sqlite3.OperationalError:

        pass

    conn.close()



# ==========================================
# ORDENS DE SERVIÇO (obras / projetos)
# ==========================================

def criar_tabela_ordens_servico():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ordens_servico (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proposta_id INTEGER NOT NULL,

        cliente_id INTEGER NOT NULL,

        status TEXT DEFAULT 'Aguardando início',

        data_criacao TEXT,

        data_inicio TEXT,

        data_prevista TEXT,

        data_conclusao TEXT,

        valor_fechado REAL,

        potencia_kwp REAL,

        quantidade_modulos INTEGER,

        descricao TEXT,

        observacoes TEXT,

        responsavel TEXT,

        FOREIGN KEY(proposta_id) REFERENCES propostas(id),

        FOREIGN KEY(cliente_id) REFERENCES clientes(id)

    )
    """)

    conn.commit()
    conn.close()


# ==========================================
# INICIALIZAÇÃO DO BANCO
# ==========================================



# ==========================================
# USUÁRIOS (multi-empresa / login)
# ==========================================

def criar_tabela_usuarios():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        empresa_id INTEGER DEFAULT 1,
        perfil TEXT DEFAULT 'admin',
        ativo INTEGER DEFAULT 1,
        FOREIGN KEY(empresa_id) REFERENCES empresa(id)
    )
    """)

    # usuário padrão: admin@gmtech / admin123
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        import hashlib
        senha = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, empresa_id, perfil)
            VALUES (?, ?, ?, 1, 'admin')
        """, ("Administrador", "admin@gmtech.local", senha))

    conn.commit()
    conn.close()


def garantir_empresa_id_nas_tabelas():
    """Adiciona empresa_id nas tabelas principais (multi-tenant leve)."""
    conn = conectar()
    cursor = conn.cursor()
    tabelas = [
        "clientes",
        "propostas",
        "servicos",
        "leads",
        "dimensionamentos_solares",
        "ordens_servico",
    ]
    for tabela in tabelas:
        try:
            cursor.execute(f"ALTER TABLE {tabela} ADD COLUMN empresa_id INTEGER DEFAULT 1")
            conn.commit()
        except Exception:
            pass
    conn.close()

def iniciar_banco():

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
    