from __future__ import annotations

import calendar
import datetime as dt

from PyQt6.QtCore import Qt, QMimeData, QSettings, QUrl
from PyQt6.QtGui import QAction, QDrag, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDockWidget,
    QHeaderView,
    QMainWindow,
    QSplitter,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolBar,
    QSizePolicy,
)
from PyQt6.QtSql import QSqlDatabase
from PyQt6.QtMultimedia import QSoundEffect

from src.config import ICON_PATH, SOUND_PATH
from src.db import Database
from src.logic import Reminder
from src.ui.dialogs import SubscriptionDialog, DeleteConfirmDialog
from src.ui.stats_dialog import StatsDialog

# Русские подписи периодов
PERIOD_RU = {
    "daily": "ежедневно",
    "weekly": "еженедельно",
    "monthly": "ежемесячно",
    "yearly": "ежегодно",
}

class NumericItem(QTableWidgetItem):
    def __lt__(self, other): # type: ignore
        try:
            return float(self.text()) < float(other.text())
        except Exception:
            return super().__lt__(other)

class DateItem(QTableWidgetItem):
    def __lt__(self, other): # type: ignore
        try:
            d1 = dt.datetime.strptime(self.text(), "%d.%m.%Y").date()
            d2 = dt.datetime.strptime(other.text(), "%d.%m.%Y").date()
            return d1 < d2
        except Exception:
            return super().__lt__(other)

class DraggableTableWidget(QTableWidget):
    def __init__(self, parent=None): # type: ignore
        super().__init__(0, 5, parent) # type: ignore
        self.setHorizontalHeaderLabels([ # type: ignore
            "Название",
            "Сумма (руб.)",
            "Период",
            "Дата след. платежа",
            "Заметки",
        ])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch) # type: ignore
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setSortingEnabled(True)
        self.horizontalHeader().setSortIndicatorShown(True) # type: ignore
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDragDropMode(QTableWidget.DragDropMode.InternalMove)

    def startDrag(self, supportedActions): # type: ignore
        row = self.currentRow()
        if row < 0:
            return
        sub_id = int(self.item(row, 0).data(Qt.ItemDataRole.UserRole)) # type: ignore
        md = QMimeData()
        md.setData("application/x-subscription-id", str(sub_id).encode())
        drag = QDrag(self)
        drag.setMimeData(md)
        drag.exec(Qt.DropAction.MoveAction)

class MainWindow(QMainWindow):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.setWindowTitle("Трекер подписок")
        # Иконка окна
        self.setWindowIcon(QIcon(ICON_PATH))

        # Qt-SQL
        self.sql_db = QSqlDatabase.addDatabase("QSQLITE")
        self.sql_db.setDatabaseName(str(db.db_path))
        self.sql_db.open()

        # Таблицы
        self.active_table = DraggableTableWidget()
        self.archive_table = DraggableTableWidget()
        for tbl in (self.active_table, self.archive_table):
            tbl.dragEnterEvent = self._dragEnterEvent # type: ignore
            tbl.dragMoveEvent = self._dragMoveEvent # type: ignore
            tbl.dropEvent = self._dropEvent # type: ignore

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.addWidget(self.active_table)
        splitter.addWidget(self.archive_table)
        self.setCentralWidget(splitter)

        # Панель инструментов
        tb = QToolBar("MainToolbar")
        self.addToolBar(tb)
        style = QApplication.instance().style() # type: ignore
        icons = {
            "Добавить": QStyle.StandardPixmap.SP_FileDialogNewFolder,
            "Отметить оплату": QStyle.StandardPixmap.SP_DialogApplyButton,
            "Удалить": QStyle.StandardPixmap.SP_TrashIcon,
            "Статистика": QStyle.StandardPixmap.SP_FileDialogContentsView,
            "Архив": QStyle.StandardPixmap.SP_DirIcon,
        }
        slots = {
            "Добавить": self.add_subscription,
            "Отметить оплату": self.mark_paid,
            "Удалить": self.delete_subscription,
            "Статистика": self._show_stats,
        }
        for text, pix in icons.items():
            icon = style.standardIcon(pix) # type: ignore
            action = QAction(icon, text, self) # type: ignore
            if text in slots:
                action.triggered.connect(slots[text]) # type: ignore
            else:
                action.setCheckable(True)
                action.setChecked(True)
                action.toggled.connect(self._toggle_archive) # type: ignore
            tb.addAction(action) # type: ignore

        # Dock для архива
        self.archiveDock = QDockWidget("Архив", self)
        self.archiveDock.setWidget(self.archive_table)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.archiveDock)

        # Напоминания и стартовый звук
        self.reminder = Reminder(db, self)
        sound = QSoundEffect(self)
        sound.setSource(QUrl.fromLocalFile(SOUND_PATH))
        sound.setVolume(0.5)
        sound.play()

        self._restore_settings()
        self.refresh_tables()

    def _toggle_archive(self, visible: bool):
        self.archiveDock.setVisible(visible)

    def _show_stats(self):
        StatsDialog(self.db, self).exec()

    def refresh_tables(self):
        self.active_table.setSortingEnabled(False)
        self.archive_table.setSortingEnabled(False)
        active = self.db.list_subscriptions(active_only=True)
        all_subs = self.db.list_subscriptions(active_only=False)

        def fill(table, rows): # type: ignore
            table.setRowCount(len(rows)) # type: ignore
            for i, row in enumerate(rows): # type: ignore
                sid = row["id"] # type: ignore
                # Название
                name_item = QTableWidgetItem(row["name"]) # type: ignore
                name_item.setData(Qt.ItemDataRole.UserRole, sid)
                name_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 0, name_item) # type: ignore
                # Сумма
                cost = NumericItem(f"{row['cost']:.2f}")
                cost.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 1, cost) # type: ignore
                # Период
                pr = QTableWidgetItem(PERIOD_RU.get(row["period"], row["period"])) # type: ignore
                pr.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 2, pr) # type: ignore
                # Дата
                try:
                    d = dt.datetime.strptime(row["next_due"], "%Y-%m-%d").date() # type: ignore
                    ds = d.strftime("%d.%m.%Y")
                except Exception:
                    ds = row["next_due"] # type: ignore
                date_item = DateItem(ds) # type: ignore
                date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 3, date_item) # type: ignore
                # Заметки
                notes = row["notes"] or "" # type: ignore
                notes_item = QTableWidgetItem(notes) # type: ignore
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(i, 4, notes_item) # type: ignore

        fill(self.active_table, active)
        self.active_table.setSortingEnabled(True)
        fill(self.archive_table, [r for r in all_subs if not r["is_active"]])
        self.archive_table.setSortingEnabled(True)

    def _dragEnterEvent(self, e): # type: ignore
        if e.mimeData().hasFormat("application/x-subscription-id"): # type: ignore
            e.acceptProposedAction() # type: ignore
        else:
            e.ignore() # type: ignore

    def _dragMoveEvent(self, e): # type: ignore
        if e.mimeData().hasFormat("application/x-subscription-id"): # type: ignore
            e.acceptProposedAction() # type: ignore
        else:
            e.ignore() # type: ignore

    def _dropEvent(self, e): # type: ignore
        raw = e.mimeData().data("application/x-subscription-id") # type: ignore
        try:
            sid = int(bytes(raw).decode()) # type: ignore
        except Exception:
            return e.ignore() # type: ignore
        new_state = 0 if e.source() is self.active_table else 1 # type: ignore
        conn = self.db.connection()
        conn.execute("UPDATE subscription SET is_active=? WHERE id=?", (new_state, sid))
        conn.commit()
        self.refresh_tables()
        e.acceptProposedAction() # type: ignore

    def _compute_next_due(self, current: str, period: str) -> str:
        cur = dt.datetime.strptime(current, "%Y-%m-%d").date()
        if period == "daily":
            nd = cur + dt.timedelta(days=1)
        elif period == "weekly":
            nd = cur + dt.timedelta(weeks=1)
        elif period == "monthly":
            y = cur.year + (cur.month // 12)
            m = cur.month % 12 + 1
            d = min(cur.day, calendar.monthrange(y, m)[1])
            nd = dt.date(y, m, d)
        elif period == "yearly":
            try:
                nd = dt.date(cur.year + 1, cur.month, cur.day)
            except ValueError:
                nd = dt.date(cur.year + 1, 2, 28)
        else:
            nd = cur
        return nd.isoformat()

    def mark_paid(self):
        row = self.active_table.currentRow()
        if row < 0:
            return
        sid = int(self.active_table.item(row, 0).data(Qt.ItemDataRole.UserRole)) # type: ignore
        rec = self.db.get_subscription(sid)
        if rec:
            self.db.add_payment(sid, dt.date.today(), rec["cost"])
            new_due = self._compute_next_due(rec["next_due"], rec["period"])
            conn = self.db.connection()
            conn.execute("UPDATE subscription SET next_due=? WHERE id=?", (new_due, sid))
            conn.commit()
            self.refresh_tables()

    def add_subscription(self):
        dlg = SubscriptionDialog(self)
        if dlg.exec() and (data := dlg.get_data()) and data[0]:
            self.db.add_subscription(*data)
            self.refresh_tables()

    def delete_subscription(self):
        row = self.active_table.currentRow()
        if row < 0:
            return
        sid = int(self.active_table.item(row, 0).data(Qt.ItemDataRole.UserRole)) # type: ignore
        dlg = DeleteConfirmDialog(self)
        if dlg.exec():
            conn = self.db.connection()
            conn.execute("DELETE FROM subscription WHERE id=?", (sid,))
            conn.commit()
            self.refresh_tables()

    def _restore_settings(self):
        st = QSettings("MyCompany", "SubscriptionTracker")
        if geo := st.value("geometry"):
            self.restoreGeometry(geo)
        if state := st.value("windowState"):
            self.restoreState(state)

    def closeEvent(self, e): # type: ignore
        st = QSettings("MyCompany", "SubscriptionTracker")
        st.setValue("geometry", self.saveGeometry())
        st.setValue("windowState", self.saveState())
        super().closeEvent(e) # type: ignore
