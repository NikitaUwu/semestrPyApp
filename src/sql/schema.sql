-- Таблица подписок (регулярных платежей)
CREATE TABLE IF NOT EXISTS subscription (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    cost        REAL    NOT NULL,
    period      TEXT    NOT NULL CHECK (period IN ('daily','weekly','monthly','yearly')),
    next_due    DATE    NOT NULL,
    notes       TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1          -- 1 = активна, 0 = архив
);

-- Фактические оплаты
CREATE TABLE IF NOT EXISTS payment (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    subscription_id INTEGER NOT NULL
        REFERENCES subscription(id) ON DELETE CASCADE,
    date_paid       DATE    NOT NULL,
    amount          REAL    NOT NULL,
    comment         TEXT
);

-- Индекс ускоряет выборки «что оплатить ближайшее»
CREATE INDEX IF NOT EXISTS ix_subscription_next_due ON subscription(next_due);

-- После вставки оплаты переносим дату next_due вперёд
CREATE TRIGGER IF NOT EXISTS trg_after_payment
AFTER INSERT ON payment
BEGIN
  UPDATE subscription
  SET next_due = CASE (SELECT period FROM subscription WHERE id = NEW.subscription_id)
       WHEN 'daily'   THEN DATE(NEW.date_paid, '+1 day')
       WHEN 'weekly'  THEN DATE(NEW.date_paid, '+7 days')
       WHEN 'monthly' THEN DATE(NEW.date_paid, '+1 month')
       WHEN 'yearly'  THEN DATE(NEW.date_paid, '+1 year')
  END
  WHERE id = NEW.subscription_id;
END;
