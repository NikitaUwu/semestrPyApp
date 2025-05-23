import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont, QIcon
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

from src.config import STYLE_PATH, ICON_PATH, FONT_PATH, SOUND_PATH
from src.db import Database
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    # Применяем глобальный стиль
    if Path(STYLE_PATH).exists():
        with open(STYLE_PATH, encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    # Загружаем шрифт Roboto
    font_id = QFontDatabase.addApplicationFont(FONT_PATH)
    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            app.setFont(QFont(families[0], 10))

    # Устанавливаем иконку приложения
    if Path(ICON_PATH).exists():
        app.setWindowIcon(QIcon(ICON_PATH))

    # Проигрываем стартовый звук
    if Path(SOUND_PATH).exists():
        sound = QSoundEffect()
        sound.setSource(QUrl.fromLocalFile(SOUND_PATH))
        sound.setLoopCount(1)
        sound.play()

    # Подключаем и инициализируем базу
    db_file = Path("subscriptions.db")
    db = Database(db_file)
    db.connect()

    # Создаём главное окно
    win = MainWindow(db)
    win.resize(900, 600)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
