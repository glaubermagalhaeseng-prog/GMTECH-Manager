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
# ATUALIZAÇÕES DO BANCO
# ==========================================

def atualizar_banco():

    conn = conectar()

    cursor = conn.cursor()

    

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
# INICIALIZAÇÃO DO BANCO
# ==========================================

def iniciar_banco():

    criar_tabela_clientes()

    criar_tabela_servicos()

    criar_tabela_propostas()

    criar_tabela_empresa()

    criar_tabela_sistemas_solares()

    criar_tabela_dimensionamentos_solares()

    atualizar_banco()    