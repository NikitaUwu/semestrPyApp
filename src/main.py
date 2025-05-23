import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase, QFont

from src.db import Database
from src.ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    qss_path = Path(__file__).parent / "resources" / "style.qss"
    if qss_path.exists():
        with open(qss_path, encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    font_path = Path(__file__).parent / "resources" / "fonts" / "Roboto.ttf"
    if font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))

    font_id = QFontDatabase.addApplicationFont(str(font_path))
    if font_id != -1:
        families = QFontDatabase.applicationFontFamilies(font_id)
        if families:
            app.setFont(QFont(families[0], 10))

    db = Database(Path("subscriptions.db"))
    db.connect()

    win = MainWindow(db)
    win.resize(900, 600)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
