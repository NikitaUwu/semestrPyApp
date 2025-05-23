from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableView, QHeaderView
from PyQt6.QtGui import QDropEvent, QDragEnterEvent, QDragMoveEvent
from PyQt6.QtSql import QSqlTableModel

import typing
if typing.TYPE_CHECKING:
    from src.db import Database


class ArchiveTableView(QTableView):
    """Таблица-приёмник Drag&Drop для архивирования подписок."""
    def __init__(self, parent=None): # type: ignore
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableView.DragDropMode.DropOnly)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore

    def dragEnterEvent(self, e: QDragEnterEvent): # type: ignore
        if e.mimeData().hasFormat("application/x-subscription-id"): # type: ignore
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e: QDragMoveEvent): # type: ignore
        if e.mimeData().hasFormat("application/x-subscription-id"): # type: ignore
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e: QDropEvent): # type: ignore
        data = e.mimeData().data("application/x-subscription-id") # type: ignore
        sub_id = int(bytes(data).decode()) # type: ignore
        # Обновляем БД
        main = self.window()
        db: Database = main.db # type: ignore
        conn = db.connection() # type: ignore
        conn.execute("UPDATE subscription SET is_active=0 WHERE id=?", (sub_id,)) # type: ignore
        conn.commit() # type: ignore
        # Обновляем обе модели
        main.model.select() # type: ignore
        main.archive.model.select() # type: ignore
        e.acceptProposedAction()


class ArchiveWidget(QWidget):
    """Контейнер для ArchiveTableView."""
    def __init__(self, sql_db, parent=None): # type: ignore
        super().__init__(parent) # type: ignore
        self.parent = parent # type: ignore

        self.model = QSqlTableModel(db=sql_db) # type: ignore
        self.model.setTable("subscription")
        self.model.setFilter("is_active = 0")
        self.model.select()

        self.view = ArchiveTableView(self)
        self.view.setModel(self.model)

        layout = QVBoxLayout(self)
        layout.addWidget(self.view)
