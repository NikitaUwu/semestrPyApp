import datetime as dt  # модуль для работы с датами
from src.db import connect  # контекстный менеджер для подключения к БД


def test_add_subscription_to_db(tmp_path):  # type: ignore
    """
    Проверяет добавление подписки в базу данных.
    Шаги:
    1. Создаём файл БД во временной папке.
    2. Подключаемся к нему через connect().
    3. Вызываем add_subscription() с тестовыми данными.
    4. Достаём эту запись через get_subscription().
    5. Проверяем, что поля name, cost и period соответствуют переданным.
    """
    db_file = tmp_path / "subs.db"  # type: ignore
    with connect(db_file) as db:  # type: ignore
        # Добавляем подписку и получаем её ID
        sid = db.add_subscription("Test", 100, "monthly", dt.date.today(), "test note")
        # Читаем подписку по ID
        sub = db.get_subscription(sid)
        # Убеждаемся, что запись существует
        assert sub is not None
        # Проверяем отдельные поля записи
        assert sub["name"] == "Test"
        assert sub["cost"] == 100
        assert sub["period"] == "monthly"
