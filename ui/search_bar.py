"""
ui/search_bar.py — Barra de pesquisa inline local (Ctrl+F).
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QTextEdit
)
from PySide6.QtGui import QTextDocument, QTextCursor, QColor, QPalette

# Alias para manter a compatibilidade com o resto do código
QExtraSelection = QTextEdit.ExtraSelection


class LocalSearchBar(QWidget):
    fecharSolicitado = Signal()

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.input_busca = QLineEdit(self)
        self.input_busca.setPlaceholderText("Buscar no capítulo...")
        self.input_busca.textChanged.connect(self.buscar)
        self.input_busca.returnPressed.connect(self.proximo)

        self.label_status = QLabel("0/0", self)

        self.btn_anterior = QPushButton("▲", self)
        self.btn_anterior.setToolTip("Anterior (Shift+Enter)")
        self.btn_anterior.clicked.connect(self.anterior)

        self.btn_proximo = QPushButton("▼", self)
        self.btn_proximo.setToolTip("Próximo (Enter)")
        self.btn_proximo.clicked.connect(self.proximo)

        self.btn_fechar = QPushButton("✕", self)
        self.btn_fechar.setToolTip("Fechar (Esc)")
        self.btn_fechar.clicked.connect(self.ocultar)

        layout.addWidget(self.input_busca)
        layout.addWidget(self.label_status)
        layout.addWidget(self.btn_anterior)
        layout.addWidget(self.btn_proximo)
        layout.addWidget(self.btn_fechar)

        self.setStyleSheet("""
            LocalSearchBar {
                background-color: #f0ede6;
                border-top: 1px solid #dcd7ce;
            }
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 3px 6px;
                background: #ffffff;
            }
            QPushButton {
                border: none;
                padding: 4px 8px;
                background: transparent;
            }
            QPushButton:hover {
                background: #e2ded4;
                border-radius: 3px;
            }
        """)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.ocultar()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            if event.modifiers() & Qt.ShiftModifier:
                self.anterior()
            else:
                self.proximo()
        else:
            super().keyPressEvent(event)

    def abrir(self):
        self.show()
        self.input_busca.setFocus()
        self.input_busca.selectAll()
        self.buscar()

    def ocultar(self):
        self.hide()
        self.limpar_destaques()
        self.editor.setFocus()
        self.fecharSolicitado.emit()

    def buscar(self):
        termo = self.input_busca.text()
        if not termo:
            self.limpar_destaques()
            self.label_status.setText("0/0")
            return

        doc = self.editor.document()
        extra_selections = []
        cursor = QTextCursor(doc)

        flags = QTextDocument.FindFlags()

        ocorrrencias = []
        while True:
            cursor = doc.find(termo, cursor, flags)
            if cursor.isNull():
                break

            selection = QExtraSelection()
            selection.cursor = cursor
            selection.format.setBackground(QColor("#ffe0b2"))
            extra_selections.append(selection)
            ocorrrencias.append(cursor.position())

        self.editor.setExtraSelections(extra_selections)

        qtd = len(ocorrrencias)
        if qtd > 0:
            # Encontra qual a ocorrência mais próxima do cursor atual
            pos_cursor = self.editor.textCursor().position()
            atual_idx = 1
            for idx, pos in enumerate(ocorrrencias):
                if pos >= pos_cursor:
                    atual_idx = idx + 1
                    break
            self.label_status.setText(f"{atual_idx}/{qtd}")
        else:
            self.label_status.setText("0/0")

    def proximo(self):
        termo = self.input_busca.text()
        if not termo:
            return
        encontrado = self.editor.find(termo)
        if not encontrado:
            # Wrap around para o início
            self.editor.moveCursor(QTextCursor.Start)
            self.editor.find(termo)
        self.buscar()

    def anterior(self):
        termo = self.input_busca.text()
        if not termo:
            return
        encontrado = self.editor.find(termo, QTextDocument.FindBackward)
        if not encontrado:
            # Wrap around para o fim
            self.editor.moveCursor(QTextCursor.End)
            self.editor.find(termo, QTextDocument.FindBackward)
        self.buscar()

    def limpar_destaques(self):
        self.editor.setExtraSelections([])