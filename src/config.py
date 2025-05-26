import sys
import os

# Определяем базовый каталог для ресурсов и приложения
# При запуске из exe (PyInstaller) sys.frozen и sys._MEIPASS укажут на временную папку
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Пути к основным ресурсам (для импорта из остальных модулей)
SQL_SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql")
STYLE_PATH = os.path.join(BASE_DIR, "resources", "style.qss")
ICON_PATH  = os.path.join(BASE_DIR, "resources", "icons", "app_icon.ico")
SOUND_PATH = os.path.join(BASE_DIR, "resources", "ding.wav")
FONT_PATH  = os.path.join(BASE_DIR, "resources", "fonts", "Roboto.ttf")