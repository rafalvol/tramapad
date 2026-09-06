from PySide6.QtWidgets import QMainWindow
from PySide6.QtGui import QAction

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TramaPad")

        # Tamanho e posição inicial
        self.resize(1000, 700)   # largura x altura
        # self.move(100, 100)    # opcional: posição na tela (x, y)

        self._criar_menu()

    def _criar_menu(self):
        menu_bar = self.menuBar()

        # --- Menu Arquivo ---
        menu_arquivo = menu_bar.addMenu("&Arquivo")

        acao_novo_projeto = QAction("Novo Projeto", self)
        acao_novo_projeto.setShortcut("Ctrl+N")
        acao_novo_projeto.triggered.connect(self._novo_projeto)
        menu_arquivo.addAction(acao_novo_projeto)

        menu_arquivo.addSeparator()

        acao_sair = QAction("Sair", self)
        acao_sair.setShortcut("Ctrl+Q")
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)

        # --- Menu Editar ---
        menu_editar = menu_bar.addMenu("&Editar")
        # (ações de editar virão na Etapa 2, junto com o editor)

        # --- Menu Exibir ---
        menu_exibir = menu_bar.addMenu("E&xibir")
        # (modo foco e temas entram aqui mais pra frente)

    def _novo_projeto(self):
        # Por enquanto só um placeholder — a lógica real vem na Etapa 3
        print("Novo projeto (ainda não implementado)")