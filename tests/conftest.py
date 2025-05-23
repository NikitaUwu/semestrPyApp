import datetime as dt
import pytest
from src.db import connect


@pytest.fixture
def db(): # type: ignore
    """Каждый тест получает чистую in-memory БД."""
    with connect(":memory:") as database: # type: ignore
        yield database


@pytest.fixture
def today():
    return dt.date.today()
