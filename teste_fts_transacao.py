# teste_fts_transacao.py
from core.database import criar_projeto, criar_capitulo, atualizar_conteudo_capitulo, busca_global_fts

pid = criar_projeto("Teste FTS")
cid = criar_capitulo(pid, "Cap 1")
atualizar_conteudo_capitulo(cid, "Era uma vez um dragão")

resultados = busca_global_fts(pid, "dragão")
print(resultados)
assert len(resultados) == 1, "Busca deveria encontrar 1 resultado"
print("OK")