import sqlite3
from datetime import datetime, date, timedelta
import calendar
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "budget.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        category TEXT,
        amount REAL,
        date TEXT,
        recurring TEXT,
        recurrence_type TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS recurring_payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        amount REAL,
        category TEXT,
        interval TEXT,
        next_due TEXT,
        active INTEGER DEFAULT 1,
        description TEXT
    )""")
    conn.commit()
    conn.close()

def add_transaction(txn):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO transactions (type, category, amount, date, recurring, recurrence_type)
                 VALUES (?, ?, ?, ?, ?, ?)''', (txn.get("type"), txn.get("category"), txn.get("amount"),
                                               txn.get("date"), txn.get("recurring","no"), txn.get("recurrence_type")))
    conn.commit()
    conn.close()

def get_transactions():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions ORDER BY date DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_transactions_between(start_date, end_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM transactions WHERE date BETWEEN ? AND ? ORDER BY date ASC", (start_date, end_date))
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def add_recurring(rp):
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO recurring_payments (type, amount, category, interval, next_due, active, description)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''', (rp.get("type"), rp.get("amount"), rp.get("category"),
                                                  rp.get("interval"), rp.get("next_due"), 1 if rp.get("active",True) else 0, rp.get("description")))
    conn.commit()
    conn.close()

def get_recurring():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM recurring_payments ORDER BY next_due ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def update_recurring_next_due(rp_id, new_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE recurring_payments SET next_due = ? WHERE id = ?", (new_date, rp_id))
    conn.commit()
    conn.close()

def process_recurring():
    """
    Find recurring payments where next_due <= today, create a transaction entry for each, and update next_due.
    This function runs on app start; for production use a scheduler (APScheduler / Celery).
    """
    conn = get_conn()
    c = conn.cursor()
    today = date.today()
    c.execute("SELECT * FROM recurring_payments WHERE active = 1 AND date(next_due) <= date(?)", (today.isoformat(),))
    rows = c.fetchall()
    for row in rows:
        rp = dict(row)
        # create transaction for this due date
        add_transaction({
            "type": rp["type"],
            "category": rp["category"],
            "amount": rp["amount"],
            "date": rp["next_due"],
            "recurring": "yes",
            "recurrence_type": rp["interval"]
        })
        # compute next due
        next_due_date = compute_next_due(rp["next_due"], rp["interval"])
        update_recurring_next_due(rp["id"], next_due_date.isoformat())
    conn.close()

def compute_next_due(current_iso, interval):
    d = datetime.strptime(current_iso, "%Y-%m-%d").date()
    if interval == "daily":
        return (d + timedelta(days=1))
    elif interval == "weekly":
        return (d + timedelta(weeks=1))
    elif interval == "monthly":
        return add_months(d, 1)
    elif interval == "yearly":
        return add_months(d, 12)
    else:
        return d

def add_months(orig_date, months):
    month = orig_date.month - 1 + months
    year = orig_date.year + month // 12
    month = month % 12 + 1
    day = min(orig_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def export_transactions_csv(start_date, end_date):
    rows = get_transactions_between(start_date, end_date)
    import csv, os
    out_path = os.path.join(os.path.dirname(__file__), "transactions_export.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        if rows:
            keys = rows[0].keys()
            writer = csv.DictWriter(f, keys)
            writer.writeheader()
            writer.writerows(rows)
        else:
            f.write("")
    return out_path
