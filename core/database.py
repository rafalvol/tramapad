import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "tramapad.db"


def conectar():
    """Retorna uma conexão com o banco, criando a pasta 'data' se necessário."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")  # necessário para ON DELETE CASCADE funcionar
    conn.row_factory = sqlite3.Row  # permite acessar colunas por nome, ex: linha["titulo"]
    return conn


def criar_tabelas():
    """Cria as tabelas do zero, caso ainda não existam. Chamado uma vez na inicialização do app."""
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projetos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            criado_em TEXT NOT NULL,
            atualizado_em TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS capitulos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projeto_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            conteudo TEXT DEFAULT '',
            ordem INTEGER NOT NULL,
            atualizado_em TEXT NOT NULL,
            FOREIGN KEY (projeto_id) REFERENCES projetos(id) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT
        )
    """)

    # Tabela virtual FTS5 para busca full-text (Etapa 4 usará isso; criada já agora
    # para não precisar migrar dados depois)
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS capitulos_fts USING fts5(
            titulo, conteudo, content='capitulos', content_rowid='id'
        )
    """)

    conn.commit()
    conn.close()


def agora():
    """Timestamp padrão usado em criado_em / atualizado_em."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------- Helpers básicos de projeto (CRUD mínimo, expandido na Etapa 3) ----------

def criar_projeto(nome: str) -> int:
    conn = conectar()
    ts = agora()
    cursor = conn.execute(
        "INSERT INTO projetos (nome, criado_em, atualizado_em) VALUES (?, ?, ?)",
        (nome, ts, ts)
    )
    conn.commit()
    projeto_id = cursor.lastrowid
    conn.close()
    return projeto_id


def listar_projetos():
    conn = conectar()
    linhas = conn.execute("SELECT * FROM projetos ORDER BY atualizado_em DESC").fetchall()
    conn.close()
    return linhas


# ---------- Helpers básicos de config ----------

def get_config(chave: str, padrao=None):
    conn = conectar()
    linha = conn.execute("SELECT valor FROM config WHERE chave = ?", (chave,)).fetchone()
    conn.close()
    return linha["valor"] if linha else padrao


def set_config(chave: str, valor: str):
    conn = conectar()
    conn.execute(
        "INSERT INTO config (chave, valor) VALUES (?, ?) "
        "ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor",
        (chave, valor)
    )
    conn.commit()
    conn.close()