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

        observacoes TEXT,

        FOREIGN KEY(cliente_id)
        REFERENCES clientes(id)

    )
    """)



    cursor.execute("""
    CREATE TABLE IF NOT EXISTS itens_proposta (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        proposta_id INTEGER NOT NULL,

        servico_id INTEGER NOT NULL,

        quantidade REAL,

        valor_unitario REAL,

        FOREIGN KEY(proposta_id)
        REFERENCES propostas(id),

        FOREIGN KEY(servico_id)
        REFERENCES servicos(id)

    )
    """)



    conn.commit()

    conn.close()