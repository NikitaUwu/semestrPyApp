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
    """
    Модальный беззаголовочный диалог для отображения статистики по подпискам.
    Поддерживает перетаскивание за любую область и скруглённые углы.
    """
    def __init__(self, db, parent=None):  # type: ignore
        super().__init__(parent)  # type: ignore
        # Уникальный идентификатор для QSS стилизации
        self.setObjectName("StatsDialog")
        # Скрыть стандартный заголовок ОС
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setModal(True)  # Сделать окно модальным
        self.setFixedSize(420, 300)  # Фиксированный размер

        # Центральный виджет для применения отступов и скруглений
        central = QWidget(self)
        central.setObjectName("StatsWidget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(central)

        # Внутренний layout для контента с отступами
        vbox = QVBoxLayout(central)
        vbox.setContentsMargins(32, 24, 32, 32)
        vbox.setSpacing(18)

        # === Пользовательский заголовок ===
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("Статистика")
        header.setObjectName("StatsTitleLabel")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(header, stretch=1)

        # Добавляем заголовок в общий вид
        vbox.addLayout(header_layout)

        # ===== Сбор метрик =====
        # Количество активных подписок
        n_subs = self._count_active_subs(db)  # type: ignore
        # Количество архивных подписок
        archived = self._count_archived_subs(db)  # type: ignore
        # Общие траты за всё время
        total = self._total_spent(db)  # type: ignore
        # Траты за последний год
        year = self._year_spent(db)  # type: ignore
        # Траты за текущий месяц
        month = self._month_spent(db)  # type: ignore

        # Формируем HTML-текст с данными
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

        # Кнопка подтверждения (OK)
        ok_btn = QPushButton("OK")
        ok_btn.setObjectName("StatsOkBtn")
        ok_btn.setMinimumWidth(100)
        ok_btn.clicked.connect(self.accept)  # Завершить диалог  # type: ignore
        vbox.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _count_active_subs(self, db):  # type: ignore
        """Возвращает число подписок с is_active=True."""
        rows = db.list_subscriptions(active_only=True)  # type: ignore
        return len(rows) if rows else 0  # type: ignore

    def _count_archived_subs(self, db):  # type: ignore
        """Возвращает число подписок с is_active=False."""
        rows = db.list_subscriptions(active_only=False)  # type: ignore
        return len([r for r in rows if not r["is_active"]]) if rows else 0  # type: ignore

    def _total_spent(self, db):  # type: ignore
        """Сумма всех платежей за всё время."""
        cur = db.connection().execute("SELECT SUM(amount) FROM payment")  # type: ignore
        val = cur.fetchone()[0]  # type: ignore
        return val if val else 0  # type: ignore

    def _year_spent(self, db):  # type: ignore
        """Сумма платежей за последние 365 дней."""
        start = (dt.date.today() - dt.timedelta(days=365)).isoformat()
        cur = db.connection().execute( # type: ignore
            "SELECT SUM(amount) FROM payment WHERE date_paid >= ?", (start,)
        )
        val = cur.fetchone()[0]  # type: ignore
        return val if val else 0  # type: ignore

    def _month_spent(self, db):  # type: ignore
        """Сумма платежей с начала текущего месяца."""
        today = dt.date.today()
        start = today.replace(day=1).isoformat()
        cur = db.connection().execute( # type: ignore
            "SELECT SUM(amount) FROM payment WHERE date_paid >= ?", (start,)
        )
        val = cur.fetchone()[0]  # type: ignore
        return val if val else 0  # type: ignore

    def resizeEvent(self, event):  # type: ignore
        """
        При изменении размера обновляем маску для скругления углов.
        """
        radius = 24
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        return super().resizeEvent(event)  # type: ignore

    def mousePressEvent(self, event):  # type: ignore
        """Начало перетаскивания окна за любую область."""
        if event.button() == Qt.MouseButton.LeftButton:  # type: ignore
            self._drag_pos = ( # type: ignore
                event.globalPosition().toPoint() # type: ignore
                - self.frameGeometry().topLeft()
            )  # type: ignore
            event.accept()  # type: ignore
        else:
            super().mousePressEvent(event)  # type: ignore

    def mouseMoveEvent(self, event):  # type: ignore
        """Перемещение окна при удержании левой кнопки мыши."""
        if (
            hasattr(self, '_drag_pos') and self._drag_pos is not None  # type: ignore
            and event.buttons() == Qt.MouseButton.LeftButton  # type: ignore
        ):
            self.move(event.globalPosition().toPoint() - self._drag_pos)  # type: ignore
            event.accept()  # type: ignore
        else:
            super().mouseMoveEvent(event)  # type: ignore

    def mouseReleaseEvent(self, event):  # type: ignore
        """Завершение перетаскивания и сброс смещения."""
        self._drag_pos = None
        event.accept()  # type: ignore
