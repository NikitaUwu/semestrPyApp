import datetime as dt
from src.db import connect

def test_add_subscription_to_db(tmp_path): # type: ignore
    db_file = tmp_path / "subs.db" # type: ignore
    with connect(db_file) as db: # type: ignore
        sid = db.add_subscription("Test", 100, "monthly", dt.date.today(), "test note")
        sub = db.get_subscription(sid)
        assert sub is not None
        assert sub["name"] == "Test"
        assert sub["cost"] == 100
        assert sub["period"] == "monthly"
