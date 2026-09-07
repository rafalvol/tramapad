"""
ui/editor_widget.py — Widget de escrita do TramaPad.

Responsabilidades:
  - Aparência confortável para escrita longa.
  - Contagem de palavras/caracteres em tempo real (sinal próprio).

Este widget NÃO sabe que autosave existe. Ele só emite `textEdited`
com o conteúdo atual a cada mudança; quem decide o que fazer com isso
(agendar salvamento, por exemplo) é o MainWindow, ligando este sinal
ao AutosaveManager (core/autosave.py).
"""

import re

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QPlainTextEdit

WORD_RE = re.compile(r"\S+")


class EditorWidget(QPlainTextEdit):
    wordCountChanged = Signal(int, int)  # palavras, caracteres
    textEdited = Signal(str)             # conteúdo completo, a cada mudança

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_appearance()
        self.textChanged.connect(self._on_text_changed)

    def _setup_appearance(self):
        family = "Georgia" if QFontDatabase.hasFamily("Georgia") else "Serif"
        font = QFont(family)
        font.setPointSize(13)
        self.setFont(font)

        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabChangesFocus(False)
        self.document().setDocumentMargin(24)

        self.setStyleSheet(
            """
            QPlainTextEdit {
                background-color: #fdfaf5;
                color: #2b2b2b;
                border: none;
                selection-background-color: #d8cfc0;
            }
            """
        )

    def _on_text_changed(self):
        texto = self.toPlainText()
        self._emitir_contagem(texto)
        self.textEdited.emit(texto)

    def _emitir_contagem(self, texto: str):
        palavras = len(WORD_RE.findall(texto))
        caracteres = len(texto)
        self.wordCountChanged.emit(palavras, caracteres)

    def carregar_conteudo(self, texto: str, posicao_cursor: int = 0):
        """
        Define o texto e posiciona o cursor sem disparar autosave/contagem espúrios.
        """
        self.blockSignals(True)
        self.setPlainText(texto)
        
        # Posiciona o cursor na posição salva (sem ultrapassar o tamanho do texto)
        cursor = self.textCursor()
        cursor.setPosition(min(posicao_cursor, len(texto)))
        self.setTextCursor(cursor)
        
        self.blockSignals(False)
        self._emitir_contagem(texto)

    def obter_posicao_cursor(self) -> int:
        return self.textCursor().position()