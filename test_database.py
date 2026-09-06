from core.database import criar_tabelas, criar_projeto, listar_projetos, get_config, set_config

print("Criando tabelas...")
criar_tabelas()

print("Criando projeto de teste...")
projeto_id = criar_projeto("Meu Primeiro Romance")
print(f"Projeto criado com id: {projeto_id}")

print("\nListando projetos:")
for projeto in listar_projetos():
    print(f"  id={projeto['id']} | nome={projeto['nome']} | criado_em={projeto['criado_em']}")

print("\nTestando config...")
set_config("tema", "escuro")
tema = get_config("tema")
print(f"Tema salvo: {tema}")

tema_padrao = get_config("chave_que_nao_existe", "valor_padrao")
print(f"Valor padrão funcionando: {tema_padrao}")