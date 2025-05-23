"""
logic.py – напоминания с QSoundEffect.
"""
import pathlib

from PyQt6.QtCore import QObject, QTimer, QUrl
from PyQt6.QtMultimedia import QSoundEffect

from src.db import Database


SND = pathlib.Path(__file__).parent / "resources" / "ding.wav"


class Reminder(QObject):
    def __init__(self, db: Database, parent=None): # type: ignore
        super().__init__(parent) # type: ignore
        self.db = db

        self.player = QSoundEffect()
        self.player.setSource(QUrl.fromLocalFile(str(SND)))
        self.player.setVolume(0.5)

        self.timer = QTimer(self)
        self.timer.setInterval(3_600_000)  # 1 ч
        self.timer.timeout.connect(self.check) # type: ignore
        self.timer.start()

        self.check()

    def check(self):
        if self.db.due_soon():
            self.player.play()
