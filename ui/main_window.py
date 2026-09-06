from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QMainWindow, QLabel, QStatusBar, QGraphicsOpacityEffect
from PySide6.QtGui import QAction

from core.database import obter_ou_criar_capitulo_padrao, buscar_capitulo
from core.autosave import AutosaveManager
from ui.editor_widget import EditorWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TramaPad")

        # Tamanho e posição inicial
        self.resize(1000, 700)   # largura x altura
        # self.move(100, 100)    # opcional: posição na tela (x, y)

        self._criar_menu()
        self._criar_editor()
        self._criar_status_bar()
        self._conectar_sinais()

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

    # ------------------------------------------------------------------
    # Etapa 2 — Editor, autosave e contagem de palavras
    # ------------------------------------------------------------------
    def _criar_editor(self):
        self.editor = EditorWidget()
        self.setCentralWidget(self.editor)

        # TEMPORÁRIO (Etapa 2): sem sidebar ainda, usamos sempre o
        # primeiro capítulo existente (ou criamos um "Sem título").
        # Na Etapa 3, troque por: self.capitulo_atual_id = <selecionado na sidebar>
        self.capitulo_atual_id = obter_ou_criar_capitulo_padrao()

        capitulo = buscar_capitulo(self.capitulo_atual_id)
        self.editor.carregar_conteudo(capitulo["conteudo"] if capitulo else "")

        self.autosave = AutosaveManager(self.capitulo_atual_id, parent=self)

    def _criar_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)

        self.label_contagem = QLabel("0 palavras · 0 caracteres")
        self.label_status_save = QLabel("")

        status.addPermanentWidget(self.label_contagem)
        status.addWidget(self.label_status_save)

        # --- Efeito de opacidade para o fade do "Salvo ✓" ---
        self._save_opacity = QGraphicsOpacityEffect(self.label_status_save)
        self._save_opacity.setOpacity(0.0)
        self.label_status_save.setGraphicsEffect(self._save_opacity)

        self._fade_anim = QPropertyAnimation(self._save_opacity, b"opacity", self)
        self._fade_anim.setDuration(900)  # duração do fade-out em ms
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        # Quanto tempo o "Salvo ✓" fica visível antes de começar a sumir
        self.SAVE_LABEL_HOLD_MS = 1800

    def _conectar_sinais(self):
        self.editor.wordCountChanged.connect(self._atualizar_label_contagem)
        self.editor.textEdited.connect(self.autosave.agendar_salvamento)
        self.autosave.statusChanged.connect(self._atualizar_label_save)

    def _atualizar_label_contagem(self, palavras: int, caracteres: int):
        self.label_contagem.setText(f"{palavras} palavras · {caracteres} caracteres")

    def _atualizar_label_save(self, estado: str):
        # Qualquer novo evento cancela um fade em andamento (ex: usuário
        # voltou a digitar enquanto o "Salvo ✓" ainda estava sumindo)
        self._fade_anim.stop()
        self._save_opacity.setOpacity(1.0)

        if estado == "salvando":
            self.label_status_save.setText("Salvando...")
        elif estado == "salvo":
            # Pequeno atraso só para o "Salvando..." ser perceptível
            QTimer.singleShot(300, self._mostrar_salvo)

    def _mostrar_salvo(self):
        self.label_status_save.setText("Salvo ✓")
        self._save_opacity.setOpacity(1.0)
        # Fica visível por um tempo, depois começa o fade-out
        QTimer.singleShot(self.SAVE_LABEL_HOLD_MS, self._fade_anim.start)