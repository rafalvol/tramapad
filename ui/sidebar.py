"""
ui/sidebar.py — Painel lateral de gerenciamento de Projetos e Capítulos.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QInputDialog, QMessageBox, QMenu
)
import core.database as db

class SidebarWidget(QWidget):
    # Emitido quando o usuário seleciona um capítulo (capitulo_id, projeto_id)
    capituloSelecionado = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(200)
        self.setMaximumWidth(350)
        
        self._setup_ui()
        self.recarregar_arvore()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # Árvore de Projetos e Capítulos
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._mostrar_menu_contexto)
        self.tree.itemSelectionChanged.connect(self._on_item_selected)
        layout.addWidget(self.tree)

        # Barra de Botões para ações rápidas
        btn_layout = QHBoxLayout()
        
        self.btn_novo_proj = QPushButton("+ Proj")
        self.btn_novo_proj.setToolTip("Novo Projeto")
        self.btn_novo_proj.clicked.connect(self._novo_projeto)

        self.btn_novo_cap = QPushButton("+ Cap")
        self.btn_novo_cap.setToolTip("Novo Capítulo no Projeto Selecionado")
        self.btn_novo_cap.clicked.connect(self._novo_capitulo)

        self.btn_up = QPushButton("▲")
        self.btn_up.setToolTip("Mover capítulo para cima")
        self.btn_up.clicked.connect(lambda: self._mover_capitulo(-1))

        self.btn_down = QPushButton("▼")
        self.btn_down.setToolTip("Mover capítulo para baixo")
        self.btn_down.clicked.connect(lambda: self._mover_capitulo(1))

        btn_layout.addWidget(self.btn_novo_proj)
        btn_layout.addWidget(self.btn_novo_cap)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        layout.addLayout(btn_layout)

    def recarregar_arvore(self, selecionar_capitulo_id: int = None):
        self.tree.blockSignals(True)
        self.tree.clear()

        projetos = db.listar_projetos()
        item_para_selecionar = None

        for proj in projetos:
            proj_item = QTreeWidgetItem(self.tree)
            proj_item.setText(0, proj["nome"])
            proj_item.setData(0, Qt.UserRole, {"tipo": "projeto", "id": proj["id"]})
            proj_item.setExpanded(True)

            capitulos = db.listar_capitulos_do_projeto(proj["id"])
            for cap in capitulos:
                cap_item = QTreeWidgetItem(proj_item)
                cap_item.setText(0, cap["titulo"])
                cap_item.setData(0, Qt.UserRole, {"tipo": "capitulo", "id": cap["id"], "projeto_id": proj["id"]})
                
                if selecionar_capitulo_id and cap["id"] == selecionar_capitulo_id:
                    item_para_selecionar = cap_item

        self.tree.blockSignals(False)

        if item_para_selecionar:
            self.tree.setCurrentItem(item_para_selecionar)

    def _on_item_selected(self):
        item = self.tree.currentItem()
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if data and data.get("tipo") == "capitulo":
            self.capituloSelecionado.emit(data["id"], data["projeto_id"])

    def _mostrar_menu_contexto(self, pos):
        item = self.tree.itemAt(pos)
        if not item:
            return

        data = item.data(0, Qt.UserRole)
        menu = QMenu(self)

        if data["tipo"] == "projeto":
            act_add_cap = menu.addAction("Novo Capítulo")
            act_renomear = menu.addAction("Renomear Projeto")
            act_excluir = menu.addAction("Excluir Projeto")
            
            action = menu.exec_(self.tree.mapToGlobal(pos))
            if action == act_add_cap:
                self._novo_capitulo(data["id"])
            elif action == act_renomear:
                self._renomear_projeto(data["id"], item.text(0))
            elif action == act_excluir:
                self._excluir_projeto(data["id"], item.text(0))

        elif data["tipo"] == "capitulo":
            act_renomear = menu.addAction("Renomear Capítulo")
            act_excluir = menu.addAction("Excluir Capítulo")

            action = menu.exec_(self.tree.mapToGlobal(pos))
            if action == act_renomear:
                self._renomear_capitulo(data["id"], item.text(0))
            elif action == act_excluir:
                self._excluir_capitulo(data["id"], item.text(0))

    def _novo_projeto(self):
        nome, ok = QInputDialog.getText(self, "Novo Projeto", "Nome do projeto:")
        if ok and nome.strip():
            proj_id = db.criar_projeto(nome.strip())
            cap_id = db.criar_capitulo(proj_id, "Capítulo 1", ordem=0)
            self.recarregar_arvore(selecionar_capitulo_id=cap_id)

    def _renomear_projeto(self, proj_id: int, nome_atual: str):
        novo_nome, ok = QInputDialog.getText(self, "Renomear Projeto", "Nome do projeto:", text=nome_atual)
        if ok and novo_nome.strip():
            db.renomear_projeto(proj_id, novo_nome.strip())
            self.recarregar_arvore()

    def _excluir_projeto(self, proj_id: int, nome: str):
        confirm = QMessageBox.question(
            self, "Excluir Projeto",
            f"Tem certeza que deseja excluir o projeto '{nome}' e todos os seus capítulos?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            db.excluir_projeto(proj_id)
            self.recarregar_arvore()

    def _novo_capitulo(self, proj_id: int = None):
        if not proj_id:
            item = self.tree.currentItem()
            if not item:
                return
            data = item.data(0, Qt.UserRole)
            proj_id = data["projeto_id"] if data["tipo"] == "capitulo" else data["id"]

        titulo, ok = QInputDialog.getText(self, "Novo Capítulo", "Título do capítulo:")
        if ok and titulo.strip():
            caps = db.listar_capitulos_do_projeto(proj_id)
            ordem = len(caps)
            cap_id = db.criar_capitulo(proj_id, titulo.strip(), ordem=ordem)
            self.recarregar_arvore(selecionar_capitulo_id=cap_id)

    def _renomear_capitulo(self, cap_id: int, titulo_atual: str):
        novo_titulo, ok = QInputDialog.getText(self, "Renomear Capítulo", "Título do capítulo:", text=titulo_atual)
        if ok and novo_titulo.strip():
            db.renomear_capitulo(cap_id, novo_titulo.strip())
            self.recarregar_arvore()

    def _excluir_capitulo(self, cap_id: int, titulo: str):
        confirm = QMessageBox.question(
            self, "Excluir Capítulo",
            f"Tem certeza que deseja excluir o capítulo '{titulo}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            db.excluir_capitulo(cap_id)
            self.recarregar_arvore()

    def _mover_capitulo(self, direcao: int):
        item = self.tree.currentItem()
        if not item:
            return
        
        data = item.data(0, Qt.UserRole)
        if not data or data["tipo"] != "capitulo":
            return

        proj_item = item.parent()
        index_atual = proj_item.indexOfChild(item)
        novo_index = index_atual + direcao

        if 0 <= novo_index < proj_item.childCount():
            proj_id = data["projeto_id"]
            capitulos = db.listar_capitulos_do_projeto(proj_id)
            
            # Troca de posição na lista
            capitulos[index_atual], capitulos[novo_index] = capitulos[novo_index], capitulos[index_atual]
            
            ordens = [(cap["id"], i) for i, cap in enumerate(capitulos)]
            db.reordenar_capitulos(ordens)
            self.recarregar_arvore(selecionar_capitulo_id=data["id"])