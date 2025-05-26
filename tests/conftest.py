import datetime as dt
import pytest
from src.db import connect


@pytest.fixture
def db():
    """Каждый тест получает чистую in-memory БД."""
    with connect(":memory:") as database:
        yield database


@pytest.fixture
def today():
    return dt.date.today()
