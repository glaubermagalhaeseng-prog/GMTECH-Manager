import sqlite3


DATABASE = "app/gmtech.db"


def conectar():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn



def criar_tabela_clientes():

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        nome TEXT NOT NULL,
        cpf_cnpj TEXT,
        telefone TEXT,
        email TEXT,

        rua TEXT,
        numero TEXT,
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



def criar_tabela_servicos():

    conn = conectar()

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servicos (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        descricao TEXT NOT NULL,

        categoria TEXT,

        valor REAL

    )
    """)


    conn.commit()

    conn.close()



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

def atualizar_banco():

    conn = conectar()

    cursor = conn.cursor()

    try:

        cursor.execute("""
            ALTER TABLE itens_proposta
            ADD COLUMN descricao TEXT
        """)

        conn.commit()

    except sqlite3.OperationalError:

        pass

    conn.close()

