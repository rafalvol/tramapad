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

def renomear_projeto(projeto_id: int, novo_nome: str):
    conn = conectar()
    conn.execute(
        "UPDATE projetos SET nome = ?, atualizado_em = ? WHERE id = ?",
        (novo_nome, agora(), projeto_id)
    )
    conn.commit()
    conn.close()

def excluir_projeto(projeto_id: int):
    conn = conectar()
    # Devido ao ON DELETE CASCADE configurado, isso removerá também os capítulos do projeto
    conn.execute("DELETE FROM projetos WHERE id = ?", (projeto_id,))
    conn.commit()
    conn.close()

# ---------- Helpers básicos de capítulo (CRUD mínimo, expandido na Etapa 3) ----------

def criar_capitulo(projeto_id: int, titulo: str, ordem: int = 0) -> int:
    conn = conectar()
    ts = agora()
    cursor = conn.execute(
        "INSERT INTO capitulos (projeto_id, titulo, conteudo, ordem, atualizado_em) "
        "VALUES (?, ?, '', ?, ?)",
        (projeto_id, titulo, ordem, ts)
    )
    conn.commit()
    capitulo_id = cursor.lastrowid
    conn.close()
    return capitulo_id


def buscar_capitulo(capitulo_id: int):
    conn = conectar()
    linha = conn.execute(
        "SELECT * FROM capitulos WHERE id = ?", (capitulo_id,)
    ).fetchone()
    conn.close()
    return linha


def atualizar_conteudo_capitulo(capitulo_id: int, conteudo: str):
    conn = conectar()
    try:
        conn.execute(
            "UPDATE capitulos SET conteudo = ?, atualizado_em = ? WHERE id = ?",
            (conteudo, agora(), capitulo_id)
        )
        # Busca título para manter FTS sincronizado, na MESMA transação
        cap = conn.execute("SELECT titulo FROM capitulos WHERE id = ?", (capitulo_id,)).fetchone()
        if cap:
            sync_fts_capitulo(capitulo_id, cap["titulo"], conteudo, conn=conn)
        conn.commit()
    finally:
        conn.close()


def obter_ou_criar_capitulo_padrao() -> int:
    """
    Placeholder temporário para a Etapa 2: sem sidebar de projetos ainda,
    o editor precisa de *algum* capítulo para salvar.

    Na Etapa 3 isso é substituído pela seleção real do usuário na árvore
    de projetos/capítulos — remover esta função quando aquela UI existir.
    """
    conn = conectar()
    linha = conn.execute("SELECT id FROM capitulos ORDER BY id LIMIT 1").fetchone()
    conn.close()

    if linha:
        return linha["id"]

    projeto_id = criar_projeto("Sem título")
    return criar_capitulo(projeto_id, "Capítulo 1", ordem=0)

def renomear_capitulo(capitulo_id: int, novo_titulo: str):
    conn = conectar()
    conn.execute(
        "UPDATE capitulos SET titulo = ?, atualizado_em = ? WHERE id = ?",
        (novo_titulo, agora(), capitulo_id)
    )
    conn.commit()
    conn.close()

def excluir_capitulo(capitulo_id: int):
    conn = conectar()
    conn.execute("DELETE FROM capitulos WHERE id = ?", (capitulo_id,))
    conn.commit()
    conn.close()

def reordenar_capitulos(ordens: list[tuple[int, int]]):
    """Recebe uma lista de tuplas (capitulo_id, nova_ordem)."""
    conn = conectar()
    cursor = conn.cursor()
    ts = agora()
    for cap_id, ordem in ordens:
        cursor.execute(
            "UPDATE capitulos SET ordem = ?, atualizado_em = ? WHERE id = ?",
            (ordem, ts, cap_id)
        )
    conn.commit()
    conn.close()

def listar_capitulos_do_projeto(projeto_id: int):
    conn = conectar()
    linhas = conn.execute(
        "SELECT * FROM capitulos WHERE projeto_id = ? ORDER BY ordem ASC, id ASC",
        (projeto_id,)
    ).fetchall()
    conn.close()
    return linhas

# ---------- Helpers básicos de config ----------

def salvar_posicao_cursor(capitulo_id: int, posicao: int):
    set_config(f"cursor_capitulo_{capitulo_id}", str(posicao))

def obter_posicao_cursor(capitulo_id: int) -> int:
    pos = get_config(f"cursor_capitulo_{capitulo_id}", "0")
    return int(pos) if pos.isdigit() else 0

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

def sync_fts_capitulo(capitulo_id: int, titulo: str, conteudo: str, conn=None):
    """
    Atualiza o índice FTS5 do capítulo.

    Se 'conn' for passada, reaproveita essa conexão e NÃO faz commit/close
    (quem chamou é responsável por isso — permite unir esta operação a
    outras na mesma transação). Se 'conn' não for passada, abre e fecha
    sua própria conexão, como antes.
    """
    conexao_propria = conn is None
    if conexao_propria:
        conn = conectar()
    try:
        conn.execute("DELETE FROM capitulos_fts WHERE rowid = ?", (capitulo_id,))
        conn.execute(
            "INSERT INTO capitulos_fts(rowid, titulo, conteudo) VALUES (?, ?, ?)",
            (capitulo_id, titulo, conteudo)
        )
        if conexao_propria:
            conn.commit()
    finally:
        if conexao_propria:
            conn.close()

def busca_global_fts(projeto_id: int, termo: str):
    """
    Realiza busca full-text nos capítulos do projeto informado usando FTS5 snippet.
    """
    if not termo.strip():
        return []
    
    conn = conectar()
    query = """
        SELECT 
            c.id AS capitulo_id,
            c.titulo AS capitulo_titulo,
            snippet(capitulos_fts, 1, '<b>', '</b>', '...', 12) AS trecho
        FROM capitulos_fts fts
        JOIN capitulos c ON c.id = fts.rowid
        WHERE c.projeto_id = ? AND capitulos_fts MATCH ?
        ORDER BY rank
    """
    
    # Tratamento de aspas simples/duplas para evitar erro de sintaxe
    termo_escapado = termo.replace('"', '""')
    termo_fts = f'"{termo_escapado}"*'
    
    try:
        resultados = conn.execute(query, (projeto_id, termo_fts)).fetchall()
    except sqlite3.OperationalError:
        query_fallback = """
            SELECT id AS capitulo_id, titulo AS capitulo_titulo, conteudo AS trecho
            FROM capitulos
            WHERE projeto_id = ? AND (conteudo LIKE ? OR titulo LIKE ?)
        """
        like_term = f"%{termo}%"
        linhas = conn.execute(query_fallback, (projeto_id, like_term, like_term)).fetchall()
        resultados = []
        for l in linhas:
            pos = l["trecho"].lower().find(termo.lower())
            inicio = max(0, pos - 20)
            fim = min(len(l["trecho"]), pos + len(termo) + 20)
            snippet = l["trecho"][inicio:fim]
            resultados.append({
                "capitulo_id": l["capitulo_id"],
                "capitulo_titulo": l["capitulo_titulo"],
                "trecho": f"...{snippet}..."
            })
            
    conn.close()
    return resultados