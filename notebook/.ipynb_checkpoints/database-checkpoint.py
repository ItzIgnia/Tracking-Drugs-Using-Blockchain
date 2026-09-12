import sqlite3
from datetime import datetime


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

DATABASE = "drugs.db"


# ============================================================
# CREATE DATABASE AND TABLES
# ============================================================

def create_database():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # ========================================================
    # DRUGS TABLE
    # ========================================================

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

    # ========================================================
    # TRANSACTIONS TABLE
    # ========================================================

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

        FOREIGN KEY (drug_id)
        REFERENCES drugs(drug_id)
    )
    """)

    connection.commit()
    connection.close()


# ============================================================
# CHECK IF DRUG EXISTS
# ============================================================

def drug_exists(drug_id):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute(
        "SELECT drug_id FROM drugs WHERE drug_id = ?",
        (drug_id,)
    )

    result = cursor.fetchone()

    connection.close()

    return result is not None


# ============================================================
# ADD DRUG
# ============================================================

def add_drug(
    drug_id,
    drug_name,
    batch_number,
    manufacturing_date,
    expiry_date,
    quantity,
    manufacturer,
    qr_data
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO drugs (
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
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (

        drug_id,
        drug_name,
        batch_number,
        manufacturing_date,
        expiry_date,
        quantity,
        manufacturer,
        manufacturer,
        "MANUFACTURED",
        qr_data,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    connection.commit()
    connection.close()


# ============================================================
# ADD TRANSACTION
# ============================================================

def add_transaction(
    drug_id,
    action,
    sender=None,
    receiver=None,
    block_number=None,
    transaction_hash=None
):

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    cursor.execute("""
    INSERT INTO transactions (
        drug_id,
        action,
        sender,
        receiver,
        timestamp,
        block_number,
        transaction_hash
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (

        drug_id,
        action,
        sender,
        receiver,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        block_number,
        transaction_hash
    ))

    connection.commit()
    connection.close()