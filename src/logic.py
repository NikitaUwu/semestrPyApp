from PyQt6.QtCore import QObject, QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect

from src.db import Database
from src.config import SOUND_PATH


class Reminder(QObject):
    def __init__(self, db: Database, parent=None):  # type: ignore
        super().__init__(parent)  # type: ignore
        self.db = db

        # Настройка плеера
        self.player = QSoundEffect()
        self.player.setSource(QUrl.fromLocalFile(SOUND_PATH))
        self.player.setVolume(0.5)

        # Таймер проверки подписок
        self.timer = QTimer(self)
        self.timer.setInterval(3_600_000)  # 1 час
        self.timer.timeout.connect(self.check)  # type: ignore
        self.timer.start()

        # Первичная проверка сразу
        self.check()

    def check(self):
        # Если есть подписки, срок которых скоро наступит — проигрываем звук
        if self.db.due_soon():
            self.player.play()
