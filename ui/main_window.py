from PySide6.QtCore import QTimer, QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtWidgets import QMainWindow, QLabel, QStatusBar, QGraphicsOpacityEffect, QSplitter, QVBoxLayout, QWidget
from PySide6.QtGui import QAction, QKeySequence, QShortcut

import core.database as db
from core.autosave import AutosaveManager
from ui.editor_widget import EditorWidget
from ui.sidebar import SidebarWidget
from ui.search_bar import LocalSearchBar
from ui.search_dialog import GlobalSearchDialog


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
        self._configurar_atalhos()
        self._conectar_sinais()

        self._restaurar_sessao_inicial()

    def _criar_menu(self):
        menu_bar = self.menuBar()

        # --- Menu Arquivo ---
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

        # --- Menu Editar ---
        menu_editar = menu_bar.addMenu("&Editar")

        acao_buscar_local = QAction("Buscar no Capítulo", self)
        acao_buscar_local.setShortcut("Ctrl+F")
        acao_buscar_local.triggered.connect(self._abrir_busca_local)
        menu_editar.addAction(acao_buscar_local)

        acao_buscar_global = QAction("Buscar no Projeto...", self)
        acao_buscar_global.setShortcut("Ctrl+Shift+F")
        acao_buscar_global.triggered.connect(self._abrir_busca_global)
        menu_editar.addAction(acao_buscar_global)

        # --- Menu Exibir ---
        menu_exibir = menu_bar.addMenu("E&xibir")

    def _setup_central_ui(self):
        splitter = QSplitter(Qt.Horizontal, self)

        self.sidebar = SidebarWidget(self)
        
        # Container do lado direito para empilhar o Editor e a Barra Local de Pesquisa
        editor_container = QWidget(self)
        editor_layout = QVBoxLayout(editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)

        self.editor = EditorWidget(self)
        self.search_bar = LocalSearchBar(self.editor, self)
        self.search_bar.hide()

        editor_layout.addWidget(self.editor, stretch=1)
        editor_layout.addWidget(self.search_bar, stretch=0)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(editor_container)
        splitter.setStretchFactor(1, 1)

        self.setCentralWidget(splitter)
        self.autosave = AutosaveManager(capitulo_id=-1, parent=self)

    def _configurar_atalhos(self):
        shortcut_f = QShortcut(QKeySequence("Ctrl+F"), self)
        shortcut_f.activated.connect(self._abrir_busca_local)

        shortcut_global_f = QShortcut(QKeySequence("Ctrl+Shift+F"), self)
        shortcut_global_f.activated.connect(self._abrir_busca_global)

    def _abrir_busca_local(self):
        self.search_bar.abrir()

    def _abrir_busca_global(self):
        if not self.projeto_atual_id:
            return
        dialog = GlobalSearchDialog(self.projeto_atual_id, self)
        dialog.resultadoSelecionado.connect(self._on_resultado_busca_global)
        dialog.exec_()

    def _on_resultado_busca_global(self, capitulo_id: int, termo: str):
        self.sidebar.recarregar_arvore(selecionar_capitulo_id=capitulo_id)
        self.search_bar.abrir()
        self.search_bar.input_busca.setText(termo)
        self.search_bar.buscar()

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
        ultimo_cap_id = db.get_config("ultimo_capitulo_aberto")
        
        if ultimo_cap_id and ultimo_cap_id.isdigit():
            cap = db.buscar_capitulo(int(ultimo_cap_id))
            if cap:
                self.sidebar.recarregar_arvore(selecionar_capitulo_id=cap["id"])
                return

        cap_id = db.obter_ou_criar_capitulo_padrao()
        self.sidebar.recarregar_arvore(selecionar_capitulo_id=cap_id)

    def _abrir_capitulo(self, capitulo_id: int, projeto_id: int):
        if self.capitulo_atual_id == capitulo_id:
            return

        if self.capitulo_atual_id is not None:
            db.salvar_posicao_cursor(self.capitulo_atual_id, self.editor.obter_posicao_cursor())
            self.autosave.trocar_capitulo(capitulo_id)
        else:
            self.autosave.capitulo_id = capitulo_id

        self.capitulo_atual_id = capitulo_id
        self.projeto_atual_id = projeto_id

        db.set_config("ultimo_capitulo_aberto", str(capitulo_id))
        db.set_config(f"ultimo_capitulo_projeto_{projeto_id}", str(capitulo_id))

        capitulo = db.buscar_capitulo(capitulo_id)
        conteudo = capitulo["conteudo"] if capitulo else ""
        posicao_cursor = db.obter_posicao_cursor(capitulo_id)
        
        self.editor.carregar_conteudo(conteudo, posicao_cursor)

        if self.search_bar.isVisible():
            self.search_bar.buscar()

    def closeEvent(self, event):
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