"""
core/autosave.py — Gerencia o ciclo de autosave com debounce.

Fica separado do editor_widget.py de propósito: o EditorWidget só emite
"o texto mudou, aqui está o conteúdo". Quem decide QUANDO e ONDE salvar
é este módulo. Isso permite reaproveitar o AutosaveManager para outras
coisas que também precisam de autosave (título do capítulo, notas,
metadados do projeto) sem duplicar lógica de timer.
"""

from PySide6.QtCore import QObject, QTimer, Signal

from core.database import atualizar_conteudo_capitulo


class AutosaveManager(QObject):
    # Emitido nas transições de estado, para a UI mostrar "Salvando..." / "Salvo ✓"
    statusChanged = Signal(str)  # "salvando" | "salvo"

    DEBOUNCE_MS = 2500  # 2.5s parado digitando -> salva

    def __init__(self, capitulo_id: int, parent=None):
        super().__init__(parent)
        self.capitulo_id = capitulo_id
        self._conteudo_pendente = None

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._salvar_agora)

    def agendar_salvamento(self, conteudo: str):
        """Chamado a cada textChanged do editor. Reinicia o debounce."""
        self._conteudo_pendente = conteudo
        self._timer.start(self.DEBOUNCE_MS)

    def _salvar_agora(self):
            if self._conteudo_pendente is None or self.capitulo_id is None or self.capitulo_id <= 0:
                return
            self.statusChanged.emit("salvando")
            atualizar_conteudo_capitulo(self.capitulo_id, self._conteudo_pendente)
            self._conteudo_pendente = None
            self.statusChanged.emit("salvo")

    def trocar_capitulo(self, novo_capitulo_id: int):
        """
        Usado na Etapa 3 quando o usuário troca de capítulo na sidebar:
        força o salvamento do que estava pendente antes de trocar o alvo.
        """
        if self._timer.isActive():
            self._timer.stop()
            self._salvar_agora()
        self.capitulo_id = novo_capitulo_id