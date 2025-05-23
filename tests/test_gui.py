import datetime as dt

from PyQt6.QtWidgets import QLabel

from src.db import connect
from src.ui.main_window import MainWindow


def test_mark_paid_adds_payment(qtbot, tmp_path):  # type: ignore
    """
    Тест проверяет, что метод mark_paid() добавляет запись в таблицу payment.
    Шаги:
    1. Создаём временную БД в tmp_path.
    2. Добавляем подписку на сумму 500 руб., период monthly.
    3. Инициализируем MainWindow с этой БД.
    4. Обновляем таблицы и выбираем первую строку (нашую подписку).
    5. Вызываем main.mark_paid(), который должен добавить запись об оплате
       и обновить дату.
    6. Проводим SQL-запрос к таблице payment подсчитывая записи для данной подписки.
    Ожидаем, что count == 1.
    """
    db_file = tmp_path / "subs.db"  # type: ignore
    with connect(db_file) as db:  # type: ignore
        # Добавляем новую подписку и запоминаем её id
        sid = db.add_subscription("Test", 500, "monthly", dt.date.today())
        # Создаём главное окно и помещаем его в qtbot для тестирования
        main = MainWindow(db)
        qtbot.addWidget(main)  # type: ignore
        main.refresh_tables()  # Заполняем таблицы данными
        main.active_table.selectRow(0)  # Выбираем первую строку
        main.mark_paid()  # Отмечаем оплату подписки

        # Проверяем, что в таблице payment появилась одна запись
        cur = db.connection().execute(
            "SELECT COUNT(*) FROM payment WHERE subscription_id = ?", (sid,)
        )
        count = cur.fetchone()[0]
        assert count == 1



def test_archive_drag_and_drop(qtbot, tmp_path):  # type: ignore
    """
    Тестирует, что при обновлении данных записей в архив, архивная таблица MainWindow содержит нужное количество строк.
    Шаги:
    1. Создаём подписку, сразу делаем её архивной (is_active=0).
    2. Открываем MainWindow и обновляем таблицы.
    3. Проверяем, что в archive_table одна строка.
    """
    db_file = tmp_path / "subs.db"  # type: ignore
    with connect(db_file) as db:  # type: ignore
        # Добавляем и сразу архивируем запись
        sid = db.add_subscription("DragTest", 199, "yearly", dt.date.today())
        conn = db.connection()
        conn.execute("UPDATE subscription SET is_active=0 WHERE id=?", (sid,))
        conn.commit()

        # Создаем окно и обновляем таблицы
        main = MainWindow(db)
        qtbot.addWidget(main)  # type: ignore
        main.refresh_tables()

        # Должна быть ровно одна запись в архивном окне
        assert main.archive_table.rowCount() == 1



def test_delete_subscription(qtbot, tmp_path):  # type: ignore
    """
    Проверяет удаление подписки из активных.
    Шаги:
    1. Создаём подписку.
    2. Открываем MainWindow, обновляем таблицы.
    3. Удаляем запись напрямую из БД.
    4. Повторно обновляем таблицы и ожидаем, что активная таблица пуста.
    """
    db_file = tmp_path / "subs.db"  # type: ignore
    with connect(db_file) as db:  # type: ignore
        sid = db.add_subscription("DeleteTest", 320, "monthly", dt.date.today())
        main = MainWindow(db)
        qtbot.addWidget(main)  # type: ignore
        main.refresh_tables()
        main.active_table.selectRow(0)  # Выбираем строку для удаления

        # Удаляем подписку через SQL и коммитим
        conn = db.connection()
        conn.execute("DELETE FROM subscription WHERE id=?", (sid,))
        conn.commit()
        main.refresh_tables()

        # После удаления активных подписок не должно остаться
        assert main.active_table.rowCount() == 0



def test_stats_dialog_works(qtbot, tmp_path):  # type: ignore
    """
    Проверяет работу StatsDialog: отображает данные о подписках.
    Шаги:
    1. Добавляем подписку в временную БД.
    2. Открываем StatsDialog.
    3. Ищем все QLabel внутри диалога и проверяем,
       что среди них есть метка с текстом «Активных подписок».
    """
    db_file = tmp_path / "subs.db"  # type: ignore
    with connect(db_file) as db:  # type: ignore
        db.add_subscription("Netflix", 999, "monthly", dt.date.today())
        from src.ui.stats_dialog import StatsDialog
        dlg = StatsDialog(db)

        # Смотрим все QLabel в диалоге
        labels = dlg.findChildren(QLabel)
        # Ожидаем, что хотя бы один лейбл содержит «Активных подписок»
        assert any(
            "Активных подписок" in lbl.text() for lbl in labels
        )
