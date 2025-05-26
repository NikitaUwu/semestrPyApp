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
    Модальный беззаголовочный диалог для отображения статистики по подпискам
    Поддерживает перетаскивание за любую область и имеет скруглённые углы
    """
    def __init__(self, db, parent=None):
        super().__init__(parent)
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
        n_subs = self._count_active_subs(db)
        # Количество архивных подписок
        archived = self._count_archived_subs(db)
        # Общие траты за всё время
        total = self._total_spent(db)
        # Траты за последний год
        year = self._year_spent(db)
        # Траты за текущий месяц
        month = self._month_spent(db)

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
        ok_btn.clicked.connect(self.accept)  # Завершить диалог
        vbox.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

    def _count_active_subs(self, db):
        """Возвращает число подписок с is_active=True."""
        rows = db.list_subscriptions(active_only=True)
        return len(rows) if rows else 0

    def _count_archived_subs(self, db):
        """Возвращает число подписок с is_active=False."""
        rows = db.list_subscriptions(active_only=False)
        return len([r for r in rows if not r["is_active"]]) if rows else 0 

    def _total_spent(self, db):
        """Сумма всех платежей за всё время."""
        cur = db.connection().execute("SELECT SUM(amount) FROM payment")
        val = cur.fetchone()[0]
        return val if val else 0

    def _year_spent(self, db):
        """Сумма платежей за последние 365 дней."""
        start = (dt.date.today() - dt.timedelta(days=365)).isoformat()
        cur = db.connection().execute(
            "SELECT SUM(amount) FROM payment WHERE date_paid >= ?", (start,)
        )
        val = cur.fetchone()[0]
        return val if val else 0

    def _month_spent(self, db):
        """Сумма платежей с начала текущего месяца."""
        today = dt.date.today()
        start = today.replace(day=1).isoformat()
        cur = db.connection().execute(
            "SELECT SUM(amount) FROM payment WHERE date_paid >= ?", (start,)
        )
        val = cur.fetchone()[0]
        return val if val else 0

    def resizeEvent(self, event):
        """
        При изменении размера обновляем маску для скругления углов.
        """
        radius = 24
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        return super().resizeEvent(event)

    def mousePressEvent(self, event):
        """Начало перетаскивания окна за любую область."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Перемещение окна при удержании левой кнопки мыши."""
        if (
            hasattr(self, '_drag_pos') and self._drag_pos is not None
            and event.buttons() == Qt.MouseButton.LeftButton
        ):
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Завершение перетаскивания и сброс смещения."""
        self._drag_pos = None
        event.accept()
