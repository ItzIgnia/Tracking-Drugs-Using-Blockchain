import sqlite3


# ============================================================
# DATABASE FILE
# ============================================================

DATABASE_NAME = "drugs.db"


# ============================================================
# CREATE DATABASE
# ============================================================

def create_database():

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()


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

            transaction_id
                INTEGER PRIMARY KEY AUTOINCREMENT,

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


    conn.commit()

    conn.close()


# ============================================================
# CHECK DRUG IN LOCAL DATABASE
# ============================================================

def drug_exists(drug_id):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT 1
        FROM drugs
        WHERE drug_id = ?
        """,
        (drug_id,)
    )


    result = cursor.fetchone()

    conn.close()


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
    current_owner,
    status,
    qr_data,
    created_at
):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()


    cursor.execute(
        """
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
        """,

        (
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
    )


    conn.commit()

    conn.close()


# ============================================================
# ADD BLOCKCHAIN TRANSACTION
# ============================================================

def add_transaction(
    drug_id,
    action,
    sender,
    receiver,
    timestamp,
    block_number,
    transaction_hash
):

    conn = sqlite3.connect(
        DATABASE_NAME
    )

    cursor = conn.cursor()


    cursor.execute(
        """
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
        """,

        (
            drug_id,

            action,

            sender,

            receiver,

            timestamp,

            block_number,

            transaction_hash
        )
    )


    conn.commit()

    conn.close()
