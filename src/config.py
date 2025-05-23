import sys
import os

# Определяем базовый каталог для ресурсов и приложения
# При запуске из exe (PyInstaller) sys.frozen и sys._MEIPASS укажут на временную папку
if getattr(sys, "frozen", False):
    BASE_DIR = sys._MEIPASS # type: ignore
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__)) # type: ignore

# Пути к основным ресурсам (для импорта из остальных модулей)
SQL_SCHEMA_PATH = os.path.join(BASE_DIR, "sql", "schema.sql") # type: ignore
STYLE_PATH = os.path.join(BASE_DIR, "resources", "style.qss") # type: ignore
ICON_PATH  = os.path.join(BASE_DIR, "resources", "icons", "app_icon.ico") # type: ignore
SOUND_PATH = os.path.join(BASE_DIR, "resources", "ding.wav") # type: ignore
FONT_PATH  = os.path.join(BASE_DIR, "resources", "fonts", "Roboto.ttf") # type: ignore