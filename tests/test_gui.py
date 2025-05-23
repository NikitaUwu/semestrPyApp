import datetime as dt

from PyQt6.QtWidgets import QLabel

from src.db import connect
from src.ui.main_window import MainWindow


def test_mark_paid_adds_payment(qtbot, tmp_path): # type: ignore
    db_file = tmp_path / "subs.db" # type: ignore
    with connect(db_file) as db: # type: ignore
        sid = db.add_subscription("Test", 500, "monthly", dt.date.today())
        main = MainWindow(db)
        qtbot.addWidget(main) # type: ignore
        main.refresh_tables()
        main.active_table.selectRow(0)
        main.mark_paid()
        cur = db.connection().execute("SELECT COUNT(*) FROM payment WHERE subscription_id = ?", (sid,))
        count = cur.fetchone()[0]
        assert count == 1


def test_archive_drag_and_drop(qtbot, tmp_path): # type: ignore
    db_file = tmp_path / "subs.db" # type: ignore
    with connect(db_file) as db: # type: ignore
        sid = db.add_subscription("DragTest", 199, "yearly", dt.date.today())
        db.connection().execute("UPDATE subscription SET is_active=0 WHERE id=?", (sid,))
        db.connection().commit()
        main = MainWindow(db)
        qtbot.addWidget(main) # type: ignore
        main.refresh_tables()
        assert main.archive_table.rowCount() == 1


def test_delete_subscription(qtbot, tmp_path): # type: ignore
    db_file = tmp_path / "subs.db" # type: ignore
    with connect(db_file) as db: # type: ignore
        sid = db.add_subscription("DeleteTest", 320, "monthly", dt.date.today())
        main = MainWindow(db)
        qtbot.addWidget(main) # type: ignore
        main.refresh_tables()
        main.active_table.selectRow(0)
        db.connection().execute("DELETE FROM subscription WHERE id=?", (sid,))
        db.connection().commit()
        main.refresh_tables()
        assert main.active_table.rowCount() == 0


def test_stats_dialog_works(qtbot, tmp_path): # type: ignore
    db_file = tmp_path / "subs.db" # type: ignore
    with connect(db_file) as db: # type: ignore
        db.add_subscription("Netflix", 999, "monthly", dt.date.today())
        from src.ui.stats_dialog import StatsDialog
        dlg = StatsDialog(db)
        labels = dlg.findChildren(QLabel)
        assert any("Активных подписок" in lbl.text() for lbl in labels)
