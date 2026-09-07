from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QMainWindow, QLabel, QStatusBar, QGraphicsOpacityEffect, QSplitter
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

import core.database as db
from core.autosave import AutosaveManager
from ui.editor_widget import EditorWidget
from ui.sidebar import SidebarWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TramaPad")
        self.resize(1100, 700)

        self.capitulo_atual_id = None
        self.projeto_atual_id = None

        self._criar_menu()
        self._setup_central_ui()
        self._criar_status_bar()
        self._conectar_sinais()

        self._restaurar_sessao_inicial()

    def _criar_menu(self):
        menu_bar = self.menuBar()

        menu_arquivo = menu_bar.addMenu("&Arquivo")

        acao_novo_projeto = QAction("Novo Projeto", self)
        acao_novo_projeto.setShortcut("Ctrl+N")
        acao_novo_projeto.triggered.connect(lambda: self.sidebar._novo_projeto())
        menu_arquivo.addAction(acao_novo_projeto)

        menu_arquivo.addSeparator()

        acao_sair = QAction("Sair", self)
        acao_sair.setShortcut("Ctrl+Q")
        acao_sair.triggered.connect(self.close)
        menu_arquivo.addAction(acao_sair)

    def _setup_central_ui(self):
        # QSplitter permite redimensionar a sidebar arrastando a borda
        splitter = QSplitter(Qt.Horizontal, self)
        
        self.sidebar = SidebarWidget(self)
        self.editor = EditorWidget(self)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.editor)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)
        self.autosave = AutosaveManager(capitulo_id=-1, parent=self)

    def _criar_status_bar(self):
        status = QStatusBar()
        self.setStatusBar(status)

        self.label_contagem = QLabel("0 palavras · 0 caracteres")
        self.label_status_save = QLabel("")

        status.addPermanentWidget(self.label_contagem)
        status.addWidget(self.label_status_save)

        self._save_opacity = QGraphicsOpacityEffect(self.label_status_save)
        self._save_opacity.setOpacity(0.0)
        self.label_status_save.setGraphicsEffect(self._save_opacity)

        self._fade_anim = QPropertyAnimation(self._save_opacity, b"opacity", self)
        self._fade_anim.setDuration(900)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.InOutQuad)

        self.SAVE_LABEL_HOLD_MS = 1800

    def _conectar_sinais(self):
        self.editor.wordCountChanged.connect(self._atualizar_label_contagem)
        self.editor.textEdited.connect(self.autosave.agendar_salvamento)
        self.autosave.statusChanged.connect(self._atualizar_label_save)
        self.sidebar.capituloSelecionado.connect(self._abrir_capitulo)

    def _restaurar_sessao_inicial(self):
        # Tenta carregar o último capítulo aberto salvo na tabela 'config'
        ultimo_cap_id = db.get_config("ultimo_capitulo_aberto")
        
        if ultimo_cap_id and ultimo_cap_id.isdigit():
            cap = db.buscar_capitulo(int(ultimo_cap_id))
            if cap:
                self.sidebar.recarregar_arvore(selecionar_capitulo_id=cap["id"])
                return

        # Fallback: garante que haja pelo menos 1 capítulo
        cap_id = db.obter_ou_criar_capitulo_padrao()
        self.sidebar.recarregar_arvore(selecionar_capitulo_id=cap_id)

    def _abrir_capitulo(self, capitulo_id: int, projeto_id: int):
        if self.capitulo_atual_id == capitulo_id:
            return

        # Salva o estado do capítulo atual antes de realizar a troca
        if self.capitulo_atual_id is not None:
            db.salvar_posicao_cursor(self.capitulo_atual_id, self.editor.obter_posicao_cursor())
            self.autosave.trocar_capitulo(capitulo_id)
        else:
            self.autosave.capitulo_id = capitulo_id

        self.capitulo_atual_id = capitulo_id
        self.projeto_atual_id = projeto_id

        # Atualiza a sessão no banco
        db.set_config("ultimo_capitulo_aberto", str(capitulo_id))
        db.set_config(f"ultimo_capitulo_projeto_{projeto_id}", str(capitulo_id))

        # Carrega o capítulo e restaura o cursor
        capitulo = db.buscar_capitulo(capitulo_id)
        conteudo = capitulo["conteudo"] if capitulo else ""
        posicao_cursor = db.obter_posicao_cursor(capitulo_id)
        
        self.editor.carregar_conteudo(conteudo, posicao_cursor)

    def closeEvent(self, event):
        # Salva o cursor e força flushing do autosave antes de encerrar
        if self.capitulo_atual_id is not None:
            db.salvar_posicao_cursor(self.capitulo_atual_id, self.editor.obter_posicao_cursor())
            if self.autosave._timer.isActive():
                self.autosave._timer.stop()
                self.autosave._salvar_agora()
        event.accept()

    def _atualizar_label_contagem(self, palavras: int, caracteres: int):
        self.label_contagem.setText(f"{palavras} palavras · {caracteres} caracteres")

    def _atualizar_label_save(self, estado: str):
        self._fade_anim.stop()
        self._save_opacity.setOpacity(1.0)

        if estado == "salvando":
            self.label_status_save.setText("Salvando...")
        elif estado == "salvo":
            QTimer.singleShot(300, self._mostrar_salvo)

    def _mostrar_salvo(self):
        self.label_status_save.setText("Salvo ✓")
        self._save_opacity.setOpacity(1.0)
        QTimer.singleShot(self.SAVE_LABEL_HOLD_MS, self._fade_anim.start)