"""
ui/search_dialog.py — Diálogo para busca global no projeto (Ctrl+Shift+F).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QLabel
)
import core.database as db

class GlobalSearchDialog(QDialog):
    # Emitido quando o usuário clica num resultado: (capitulo_id, termo_buscado)
    resultadoSelecionado = Signal(int, str)

    def __init__(self, projeto_id: int, parent=None):
        super().__init__(parent)
        self.projeto_id = projeto_id
        self.setWindowTitle("Pesquisa Global no Projeto")
        self.resize(550, 400)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Campo de entrada
        search_layout = QHBoxLayout()
        self.input_busca = QLineEdit(self)
        self.input_busca.setPlaceholderText("Digite o termo para buscar em todos os capítulos...")
        self.input_busca.returnPressed.connect(self._executar_busca)
        
        btn_buscar = QPushButton("Buscar", self)
        btn_buscar.clicked.connect(self._executar_busca)

        search_layout.addWidget(self.input_busca)
        search_layout.addWidget(btn_buscar)
        layout.addLayout(search_layout)

        # Lista de Resultados
        self.lista_resultados = QListWidget(self)
        self.lista_resultados.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.lista_resultados)

        self.label_info = QLabel("Pressione Enter para buscar.", self)
        layout.addWidget(self.label_info)

    def _executar_busca(self):
        termo = self.input_busca.text().strip()
        if not termo:
            return

        self.lista_resultados.clear()
        resultados = db.busca_global_fts(self.projeto_id, termo)

        if not resultados:
            self.label_info.setText("Nenhum resultado encontrado.")
            return

        self.label_info.setText(f"{len(resultados)} ocorrência(s) encontrada(s):")

        for r in resultados:
            # Formata texto limpo das tags HTML retornadas pelo FTS snippet
            snippet_limpo = r["trecho"].replace("<b>", "").replace("</b>", "")
            
            item = QListWidgetItem(self.lista_resultados)
            item.setText(f"📄 {r['capitulo_titulo']}\n    {snippet_limpo}")
            item.setData(Qt.UserRole, (r["capitulo_id"], termo))

    def _on_item_double_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.UserRole)
        if data:
            cap_id, termo = data
            self.resultadoSelecionado.emit(cap_id, termo)
            self.accept()