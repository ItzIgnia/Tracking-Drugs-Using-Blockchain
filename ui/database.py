import sqlite3
from pathlib import Path

DATABASE_NAME = Path(__file__).resolve().parent / "drugs.db"


def _connect():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_database():
    with _connect() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drugs (
                drug_id TEXT PRIMARY KEY,
                drug_name TEXT NOT NULL,
                batch_number TEXT NOT NULL,
                manufacturing_date TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                manufacturer TEXT NOT NULL,
                current_owner TEXT NOT NULL,
                status TEXT NOT NULL,
                qr_data TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                drug_id TEXT NOT NULL,
                action TEXT NOT NULL,
                sender TEXT,
                receiver TEXT,
                timestamp TEXT NOT NULL,
                block_number INTEGER,
                transaction_hash TEXT,
                FOREIGN KEY (drug_id) REFERENCES drugs(drug_id)
            )
        """)


def drug_exists(drug_id):
    with _connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM drugs WHERE drug_id = ? LIMIT 1",
            (drug_id,),
        ).fetchone()
    return row is not None


def add_drug(
    drug_id,
    drug_name,
    batch_number,
    manufacturing_date,
    expiry_date,
    quantity,
    manufacturer,
    current_owner,
    status,
    qr_data,
    created_at,
):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO drugs (
                drug_id, drug_name, batch_number, manufacturing_date,
                expiry_date, quantity, manufacturer, current_owner,
                status, qr_data, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            drug_id, drug_name, batch_number, manufacturing_date,
            expiry_date, quantity, manufacturer, current_owner,
            status, qr_data, created_at,
        ))


def update_drug_status(drug_id, current_owner, status):
    with _connect() as conn:
        conn.execute(
            "UPDATE drugs SET current_owner = ?, status = ? WHERE drug_id = ?",
            (current_owner, status, drug_id),
        )


def add_transaction(
    drug_id,
    action,
    sender,
    receiver,
    timestamp,
    block_number,
    transaction_hash,
):
    with _connect() as conn:
        conn.execute("""
            INSERT INTO transactions (
                drug_id, action, sender, receiver, timestamp,
                block_number, transaction_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            drug_id, action, sender, receiver, timestamp,
            block_number, transaction_hash,
        ))


def get_transactions(drug_id):
    with _connect() as conn:
        rows = conn.execute("""
            SELECT action, sender, receiver, timestamp,
                   block_number, transaction_hash
            FROM transactions
            WHERE drug_id = ?
            ORDER BY transaction_id ASC
        """, (drug_id,)).fetchall()
    return rows
