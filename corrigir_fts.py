# corrigir_fts.py
import sqlite3

conn = sqlite3.connect("data/tramapad.db")

conn.execute("DROP TABLE IF EXISTS capitulos_fts")
conn.commit()

conn.execute("""
    CREATE VIRTUAL TABLE capitulos_fts USING fts5(
        titulo, conteudo, content='capitulos', content_rowid='id'
    )
""")

# Repopula o índice a partir da tabela real 'capitulos'
conn.execute("INSERT INTO capitulos_fts(capitulos_fts) VALUES('rebuild')")
conn.commit()
conn.close()

print("FTS reconstruído com sucesso")