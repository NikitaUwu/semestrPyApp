from __future__ import annotations
import datetime as dt

from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QRegion, QPainterPath
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QLabel
)

# Отображаемые на русском периоды и соответствующие коды в БД
PERIOD_MAP = {
    "ежедневно": "daily",
    "еженедельно": "weekly",
    "ежемесячно": "monthly",
    "ежегодно": "yearly",
}

class SubscriptionDialog(QDialog):
    """Диалог создания или редактирования подписки."""
    def __init__(self, parent=None):  # type: ignore
        super().__init__(parent)  # type: ignore
        self.setWindowTitle("Добавить подписку")
        self.setModal(True)
        self.setFixedSize(400, 400)
        self.setObjectName("SubscriptionDialog")

        # Центральный контейнер для стиля
        central = QWidget(self)
        central.setObjectName("SubscriptionDialogWidget")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(central)

        form = QFormLayout(central)
        form.setContentsMargins(26, 26, 26, 26)
        form.setSpacing(15)

        self.name_edit = QLineEdit(self)
        self.name_edit.setPlaceholderText("Введите название")
        form.addRow("Название:", self.name_edit)

        self.cost_spin = QDoubleSpinBox(self)
        self.cost_spin.setRange(0.0, 1_000_000.0)
        self.cost_spin.setSuffix(" ₽")
        self.cost_spin.setDecimals(2)
        form.addRow("Стоимость:", self.cost_spin)

        self.period_combo = QComboBox(self)
        self.period_combo.addItems(list(PERIOD_MAP.keys()))  # type: ignore
        form.addRow("Период:", self.period_combo)

        self.date_edit = QDateEdit(self)
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Дата след. платежа:", self.date_edit)

        self.notes_edit = QTextEdit(self)
        self.notes_edit.setPlaceholderText("Дополнительные заметки (необязательно)")
        self.notes_edit.setFixedHeight(48)
        form.addRow("Заметки:", self.notes_edit)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel,
            parent=self
        )
        btns.accepted.connect(self.accept)  # type: ignore
        btns.rejected.connect(self.reject)  # type: ignore
        btns.button(QDialogButtonBox.StandardButton.Ok).setText("Сохранить")  # type: ignore
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")  # type: ignore
        form.addRow(btns)

    def get_data(self) -> tuple[str, float, str, dt.date, str] | None:
        name = self.name_edit.text().strip()
        if not name:
            return None
        cost = float(self.cost_spin.value())
        period_ru = self.period_combo.currentText()
        period_code = PERIOD_MAP[period_ru]
        qdate = self.date_edit.date()
        next_due = dt.date(qdate.year(), qdate.month(), qdate.day())
        notes = self.notes_edit.toPlainText().strip()
        return (name, cost, period_code, next_due, notes)


class DeleteConfirmDialog(QDialog):
    def __init__(self, parent=None):  # type: ignore
        super().__init__(parent)  # type: ignore
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.setWindowTitle("Подтверждение удаления")
        self.setFixedSize(350, 150)
        self.setObjectName("DeleteConfirmDialog")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(18)

        label = QLabel(
            "Удалить подписку?\nЭто действие нельзя отменить.", self
        )
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 16px;")
        layout.addWidget(label)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Yes |
            QDialogButtonBox.StandardButton.Cancel,
            Qt.Orientation.Horizontal,
            self
        )
        btns.button(QDialogButtonBox.StandardButton.Yes).setText("Удалить")  # type: ignore
        btns.button(QDialogButtonBox.StandardButton.Cancel).setText("Отмена")  # type: ignore
        btns.button(QDialogButtonBox.StandardButton.Cancel).setObjectName("CancelDeleteBtn")  # type: ignore
        btns.accepted.connect(self.accept)  # type: ignore
        btns.rejected.connect(self.reject)  # type: ignore
        layout.addWidget(btns)

        self._drag_pos = None

    def mousePressEvent(self, event):  # type: ignore
        if event.button() == Qt.MouseButton.LeftButton:  # type: ignore
            self._drag_pos = ( # type: ignore
                event.globalPosition().toPoint() - self.frameGeometry().topLeft() # type: ignore
            )  # type: ignore
            event.accept()  # type: ignore
        else:
            super().mousePressEvent(event)  # type: ignore

    def mouseMoveEvent(self, event):  # type: ignore
        if (
            self._drag_pos is not None and # type: ignore
            event.buttons() == Qt.MouseButton.LeftButton # type: ignore
        ):
            self.move(event.globalPosition().toPoint() - self._drag_pos)  # type: ignore
            event.accept()  # type: ignore
        else:
            super().mouseMoveEvent(event)  # type: ignore

    def mouseReleaseEvent(self, event):  # type: ignore
        self._drag_pos = None
        event.accept()  # type: ignore

    def resizeEvent(self, event):  # type: ignore
        # Скругляем углы через маску
        radius = 18
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), radius, radius)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        return super().resizeEvent(event)  # type: ignore
