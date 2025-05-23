import datetime as dt

from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
    QHBoxLayout,
)
from PyQt6.QtGui import QRegion, QPainterPath
from PyQt6.QtCore import Qt

class StatsDialog(QDialog):
    def __init__(self, db, parent=None):  # type: ignore
        super().__init__(parent)  # type: ignore
        self.setObjectName("StatsDialog")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)  # Без хедера ОС
        self.setModal(True)
        self.setFixedSize(420, 300)  # фиксированный размер

        # Слой для отступов и скругления
        central = QWidget(self)
        central.setObjectName("StatsWidget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(central)
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(32, 24, 32, 32)
        vbox.setSpacing(18)

        # === Кастомный заголовок ===
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Статистика")
        header.setObjectName("StatsTitleLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header, stretch=1)

        vbox.addLayout(header_layout)

        # ===== Статистика =====
        n_subs = self._count_active_subs(db)  # type: ignore
        archived = self._count_archived_subs(db)  # type: ignore
        total = self._total_spent(db)  # type: ignore
        year = self._year_spent(db)  # type: ignore
        month = self._month_spent(db)  # type: ignore

        stats_label = QLabel(
            f"<b>Активных подписок:</b> {n_subs}<br>"
            f"<b>В архиве:</b> {archived}<br>"
            f"<b>Трат всего:</b> {total:.2f} руб.<br>"
            f"<b>Трат за год:</b> {year:.2f} руб.<br>"
            f"<b>Трат за месяц:</b> {month:.2f} руб."
        )
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_label.setStyleSheet("font-size: 16px;")
        vbox.addWidget(stats_label)

        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("StatsOkBtn")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.accept)  # type: ignore
        vbox.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _count_active_subs(self, db):  # type: ignore
        rows = db.list_subscriptions(active_only=True)  # type: ignore
        return len(rows) if rows else 0  # type: ignore

    def _count_archived_subs(self, db):  # type: ignore
        rows = db.list_subscriptions(active_only=False)  # type: ignore
        return len([r for r in rows if not r["is_active"]]) if rows else 0  # type: ignore

    def _total_spent(self, db):  # type: ignore
        cur = db.connection().execute("SELECT SUM(amount) FROM payment")  # type: ignore
        val = cur.fetchone()[0]  # type: ignore
        return val if val else 0  # type: ignore

    def _year_spent(self, db):  # type: ignore
        start = (dt.date.today() - dt.timedelta(days=365)).isoformat()
        cur = db.connection().execute(  # type: ignore
            "SELECT SUM(amount) FROM payment WHERE date_paid >= ?", (start,)
        )
        val = cur.fetchone()[0]  # type: ignore
        return val if val else 0  # type: ignore

    def _month_spent(self, db):  # type: ignore
        today = dt.date.today()
        start = today.replace(day=1).isoformat()
        cur = db.connection().execute(  # type: ignore
            "SELECT SUM(amount) FROM payment WHERE date_paid >= ?", (start,)
        )
        val = cur.fetchone()[0]  # type: ignore
        return val if val else 0  # type: ignore

    def resizeEvent(self, event):  # type: ignore
        # При изменении размера окна обновляем маску для скругления
        radius = 24
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        return super().resizeEvent(event)  # type: ignore

    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:  # type: ignore
            self._drag_pos = (  # type: ignore
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()  # type: ignore
            )  # type: ignore
            event.accept()  # type: ignore
        else:
            super().mousePressEvent(event)  # type: ignore

    def mouseMoveEvent(self, event):  # type: ignore
        if (
            hasattr(self, "_drag_pos")
            and self._drag_pos is not None  # type: ignore
            and event.buttons() == Qt.MouseButton.LeftButton  # type: ignore
        ):  # type: ignore
            self.move(event.globalPosition().toPoint() - self._drag_pos)  # type: ignore
            event.accept()  # type: ignore
        else:
            super().mouseMoveEvent(event)  # type: ignore

    def mouseReleaseEvent(self, event):  # type: ignore
        self._drag_pos = None
        event.accept()  # type: ignore
