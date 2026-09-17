# ============================================================
# PHARMACHAIN
# Blockchain-Based Pharmaceutical Supply Chain
# ============================================================

import sys
from pathlib import Path
from datetime import datetime

import streamlit as st
import qrcode
from io import BytesIO


# ============================================================
# LOAD PROJECT MODULES
# ============================================================

import sys
import importlib.util
from pathlib import Path


# ------------------------------------------------------------
# PROJECT PATH
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_FILE = (
    PROJECT_ROOT
    / "database"
    / "database.py"
)

BLOCKCHAIN_FILE = (
    PROJECT_ROOT
    / "Blockchain"
    / "blockchain.py"
)


# ------------------------------------------------------------
# CHECK FILES
# ------------------------------------------------------------

if not DATABASE_FILE.exists():

    st.error(
        f"Database file not found:\n{DATABASE_FILE}"
    )

    st.stop()


if not BLOCKCHAIN_FILE.exists():

    st.error(
        f"Blockchain file not found:\n{BLOCKCHAIN_FILE}"
    )

    st.stop()


# ------------------------------------------------------------
# LOAD DATABASE.PY
# ------------------------------------------------------------

try:

    database_spec = importlib.util.spec_from_file_location(
        "pharmachain_database",
        DATABASE_FILE
    )

    database = importlib.util.module_from_spec(
        database_spec
    )

    database_spec.loader.exec_module(
        database
    )

except Exception as e:

    st.error(
        "Unable to load database.py"
    )

    st.code(str(e))

    st.stop()


# ------------------------------------------------------------
# DATABASE FUNCTIONS
# ------------------------------------------------------------

create_database = database.create_database
add_drug = database.add_drug
add_transaction = database.add_transaction
db_drug_exists = database.drug_exists
db_get_drug = database.get_drug
update_drug = database.update_drug
get_transactions = database.get_transactions


# ------------------------------------------------------------
# LOAD BLOCKCHAIN.PY
# ------------------------------------------------------------

try:

    blockchain_spec = importlib.util.spec_from_file_location(
        "pharmachain_blockchain",
        BLOCKCHAIN_FILE
    )

    blockchain = importlib.util.module_from_spec(
        blockchain_spec
    )

    blockchain_spec.loader.exec_module(
        blockchain
    )

except Exception as e:

    st.error(
        "Unable to load blockchain.py"
    )

    st.code(str(e))

    st.stop()


# ------------------------------------------------------------
# BLOCKCHAIN FUNCTIONS
# ------------------------------------------------------------

blockchain_connected = blockchain.blockchain_connected
blockchain_drug_exists = blockchain.blockchain_drug_exists

manufacture_drug = blockchain.manufacture_drug
get_drug = blockchain.get_drug
ship_drug = blockchain.ship_drug
receive_drug = blockchain.receive_drug
ship_to_hospital = blockchain.ship_to_hospital
hospital_receive_drug = blockchain.hospital_receive_drug
dispense_drug = blockchain.dispense_drug

CONTRACT_ADDRESS = blockchain.CONTRACT_ADDRESS

manufacturer = blockchain.manufacturer
distributor = blockchain.distributor
hospital = blockchain.hospital

get_status_name = blockchain.get_status_name

# ============================================================
# DATABASE INITIALIZATION
# ============================================================

try:
    create_database()
except Exception as e:
    st.error("Database initialization failed.")
    st.code(str(e))
    st.stop()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PharmaChain",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM HEADER
# ============================================================

st.title("💊 PharmaChain")

st.caption(
    "Blockchain-Based Pharmaceutical Supply Chain Tracking System"
)

st.divider()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("PharmaChain")

st.sidebar.write(
    "Supply Chain Management"
)

st.sidebar.divider()

menu = st.sidebar.selectbox(
    "Select Module",
    [
        "Dashboard",
        "Register Drug",
        "Supply Chain",
        "Verify Drug"
    ]
)

st.sidebar.divider()

st.sidebar.subheader("System Status")

if blockchain_connected():

    st.sidebar.success("Blockchain Connected")

else:

    st.sidebar.error("Blockchain Disconnected")


st.sidebar.write(
    "Contract:"
)

st.sidebar.code(
    CONTRACT_ADDRESS
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def format_timestamp(timestamp):
    """
    Convert Unix timestamp to readable date/time.
    """

    try:

        timestamp = int(timestamp)

        if timestamp == 0:
            return "Not recorded"

        return datetime.fromtimestamp(
            timestamp
        ).strftime("%d-%m-%Y %H:%M:%S")

    except Exception:

        return "Unknown"


def shorten_address(address):
    """
    Shorten blockchain address for display.
    """

    if not address:
        return "N/A"

    address = str(address)

    if len(address) <= 15:
        return address

    return address[:8] + "..." + address[-6:]


def generate_qr_code(data):
    """
    Generate QR code and return image bytes.
    """

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG"
    )

    buffer.seek(0)

    return buffer


def display_blockchain_drug(drug):
    """
    Display blockchain drug information.
    """

    st.subheader("Blockchain Drug Record")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Drug ID",
            drug[0]
        )

        st.write("**Drug Name**")
        st.write(drug[2])

        st.write("**Batch ID**")
        st.write(drug[1])

        st.write("**Manufacturer**")
        st.write(drug[3])

    with col2:

        st.metric(
            "Quantity",
            str(drug[4])
        )

        st.write("**Manufacturing Date**")
        st.write(
            format_timestamp(drug[5])
        )

        st.write("**Expiry Date**")
        st.write(
            format_timestamp(drug[6])
        )

    with col3:

        st.metric(
            "Status",
            get_status_name(drug[11])
        )

        st.write("**Manufacturer Wallet**")
        st.code(
            shorten_address(drug[9])
        )

        st.write("**Current Owner**")
        st.code(
            shorten_address(drug[10])
        )

    st.divider()

    st.subheader("Blockchain Timestamps")

    col1, col2 = st.columns(2)

    with col1:

        st.write("**Shipping Date**")

        st.write(
            format_timestamp(drug[7])
        )

    with col2:

        st.write("**Receiving Date**")

        st.write(
            format_timestamp(drug[8])
        )


def display_transaction_history(drug_id):
    """
    Display SQLite transaction history.
    """

    st.subheader("Transaction History")

    try:

        transactions = get_transactions(
            drug_id
        )

    except Exception as e:

        st.error(
            "Unable to load transaction history."
        )

        st.code(str(e))

        return

    if not transactions:

        st.info(
            "No transaction history found."
        )

        return

    for transaction in transactions:

        transaction_id = transaction[0]
        action = transaction[2]
        sender = transaction[3]
        receiver = transaction[4]
        timestamp = transaction[5]
        block_number = transaction[6]
        transaction_hash = transaction[7]

        with st.container(border=True):

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    f"### {action}"
                )

                st.write(
                    f"Transaction ID: {transaction_id}"
                )

            with col2:

                st.write(
                    "**Sender**"
                )

                st.code(
                    shorten_address(sender)
                )

                st.write(
                    "**Receiver**"
                )

                if receiver == "PATIENT":

                    st.write("Patient")

                else:

                    st.code(
                        shorten_address(receiver)
                    )

            with col3:

                st.write(
                    "**Block Number**"
                )

                st.write(
                    block_number
                )

                st.write(
                    "**Timestamp**"
                )

                st.write(
                    timestamp
                )

            if transaction_hash:

                st.write(
                    "**Transaction Hash**"
                )

                st.code(
                    transaction_hash
                )


# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.header("Dashboard")

    st.write(
        "Welcome to PharmaChain."
    )

    st.write(
        "A blockchain-based system for tracking "
        "pharmaceutical drugs through the supply chain."
    )

    st.divider()

    # --------------------------------------------------------
    # SYSTEM INFORMATION
    # --------------------------------------------------------

    st.subheader("System Information")

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        if blockchain_connected():

            st.metric(
                "Blockchain",
                "Connected"
            )

        else:

            st.metric(
                "Blockchain",
                "Disconnected"
            )

    with col2:

        st.metric(
            "Chain ID",
            "31337"
        )

    with col3:

        st.metric(
            "Manufacturer",
            shorten_address(manufacturer)
        )

    with col4:

        st.metric(
            "Hospital",
            shorten_address(hospital)
        )

    st.divider()

    # --------------------------------------------------------
    # SUPPLY CHAIN
    # --------------------------------------------------------

    st.subheader("Drug Supply Chain")

    st.markdown(
        """
        ### Manufacturer
        Drug is manufactured and registered on the blockchain.

        ↓

        ### Distributor
        Manufacturer ships the drug to the distributor.

        ↓

        ### Distributor Receipt
        Distributor confirms that the shipment has arrived.

        ↓

        ### Hospital
        Distributor ships the drug to the hospital.

        ↓

        ### Hospital Receipt
        Hospital confirms the shipment.

        ↓

        ### Patient
        Hospital dispenses the drug to the patient.
        """
    )

    st.divider()

    st.info(
        "Every blockchain operation produces a transaction "
        "hash and block number that can be verified."
    )


# ============================================================
# REGISTER DRUG
# ============================================================

elif menu == "Register Drug":

    st.header("Register New Drug")

    st.write(
        "Register a pharmaceutical product on the "
        "PharmaChain blockchain."
    )

    st.divider()

    with st.form("register_drug_form"):

        col1, col2 = st.columns(2)

        with col1:

            drug_name = st.text_input(
                "Drug Name",
                placeholder="Example: Paracetamol 500mg"
            )

            batch_number = st.text_input(
                "Batch Number",
                placeholder="Example: BATCH001"
            )

            manufacturer_name = st.text_input(
                "Manufacturer Company",
                placeholder="Example: ABC Pharmaceuticals"
            )

        with col2:

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=100,
                step=1
            )

            manufacturing_date = st.date_input(
                "Manufacturing Date"
            )

            expiry_date = st.date_input(
                "Expiry Date"
            )

        st.divider()

        submitted = st.form_submit_button(
            "Register Drug",
            use_container_width=True
        )

    if submitted:

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not drug_name.strip():

            st.error(
                "Please enter the drug name."
            )

            st.stop()

        if not batch_number.strip():

            st.error(
                "Please enter the batch number."
            )

            st.stop()

        if not manufacturer_name.strip():

            st.error(
                "Please enter the manufacturer company name."
            )

            st.stop()

        if expiry_date <= manufacturing_date:

            st.error(
                "Expiry date must be after manufacturing date."
            )

            st.stop()

        # ----------------------------------------------------
        # CREATE DRUG ID
        # ----------------------------------------------------

        drug_id = (
            f"DRG-{manufacturing_date.year}-"
            f"{batch_number.upper().strip()}"
        )

        st.info(
            f"Generated Drug ID: {drug_id}"
        )

        # ----------------------------------------------------
        # CHECK SQLITE
        # ----------------------------------------------------

        try:

            if db_drug_exists(drug_id):

                st.error(
                    "This drug already exists in the database."
                )

                st.stop()

        except Exception as e:

            st.error(
                "Database check failed."
            )

            st.code(str(e))

            st.stop()

        # ----------------------------------------------------
        # CHECK BLOCKCHAIN
        # ----------------------------------------------------

        try:

            if blockchain_drug_exists(drug_id):

                st.error(
                    "This drug already exists on the blockchain."
                )

                st.stop()

        except Exception as e:

            st.error(
                "Blockchain check failed."
            )

            st.code(str(e))

            st.stop()

        # ----------------------------------------------------
        # BLOCKCHAIN REGISTRATION
        # ----------------------------------------------------

        try:

            with st.spinner(
                "Registering drug on blockchain..."
            ):

                blockchain_result = manufacture_drug(
                    drug_id=drug_id,
                    batch_id=batch_number.strip(),
                    drug_name=drug_name.strip(),
                    manufacturer_name=manufacturer_name.strip(),
                    quantity=int(quantity),
                    manufacturing_date=manufacturing_date,
                    expiry_date=expiry_date
                )

        except Exception as e:

            st.error(
                "Blockchain registration failed."
            )

            st.code(str(e))

            st.stop()

        # ----------------------------------------------------
        # SAVE TO SQLITE
        # ----------------------------------------------------

        try:
            add_drug(
                drug_id=drug_id,
                drug_name=drug_name.strip(),
                batch_number=batch_number.strip(),
                manufacturing_date=str(
                    manufacturing_date
                ),
                expiry_date=str(
                expiry_date
                ),
                quantity=int(quantity),
                manufacturer=manufacturer_name.strip(),
                qr_data=drug_id
            )

        except Exception as e:

            st.error(
                "Blockchain transaction succeeded, "
                "but database storage failed."
            )

            st.code(str(e))

            st.warning(
                "Transaction Hash:"
            )

            st.code(
                blockchain_result["transaction_hash"]
            )

            st.stop()

        # ----------------------------------------------------
        # SAVE TRANSACTION
        # ----------------------------------------------------

        try:

            add_transaction(
                drug_id=drug_id,
                action="MANUFACTURE",
                sender=blockchain_result["sender"],
                receiver=blockchain_result.get(
                    "receiver",
                    blockchain_result["sender"]
                ),
                block_number=blockchain_result[
                    "block_number"
                ],
                transaction_hash=blockchain_result[
                    "transaction_hash"
                ]
            )

        except Exception as e:

            st.warning(
                "Drug saved successfully, but transaction "
                "history could not be saved."
            )

            st.code(str(e))

        # ----------------------------------------------------
        # GENERATE QR CODE
        # ----------------------------------------------------

        qr_image = generate_qr_code(
            drug_id
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        st.success(
            "Drug successfully registered!"
        )

        st.divider()

        col1, col2 = st.columns(2)

        with col1:

            st.subheader(
                "Drug Information"
            )

            st.write(
                "**Drug ID:**",
                drug_id
            )

            st.write(
                "**Drug Name:**",
                drug_name
            )

            st.write(
                "**Batch Number:**",
                batch_number
            )

            st.write(
                "**Quantity:**",
                quantity
            )

            st.write(
                "**Manufacturer:**",
                manufacturer_name
            )

            st.write(
                "**Status:**",
                "MANUFACTURED"
            )

        with col2:

            st.subheader(
                "Drug QR Code"
            )

            st.image(
                qr_image,
                width=250
            )

            st.download_button(
                label="Download QR Code",
                data=qr_image,
                file_name=f"{drug_id}.png",
                mime="image/png"
            )

        st.divider()

        st.subheader(
            "Blockchain Transaction"
        )

        st.write(
            "**Block Number:**",
            blockchain_result["block_number"]
        )

        st.write(
            "**Transaction Hash:**"
        )

        st.code(
            blockchain_result["transaction_hash"]
        )


# ============================================================
# SUPPLY CHAIN
# ============================================================

elif menu == "Supply Chain":

    st.header("Drug Supply Chain")

    st.write(
        "Move a drug through each stage of the "
        "pharmaceutical supply chain."
    )

    st.divider()

    drug_id = st.text_input(
        "Enter Drug ID",
        placeholder="Example: DRG-2026-BATCH001"
    ).strip()

    if drug_id:

        # ----------------------------------------------------
        # CHECK BLOCKCHAIN
        # ----------------------------------------------------

        try:

            if not blockchain_drug_exists(drug_id):

                st.error(
                    "Drug does not exist on the blockchain."
                )

                st.stop()

        except Exception as e:

            st.error(
                "Unable to check blockchain."
            )

            st.code(str(e))

            st.stop()

        # ----------------------------------------------------
        # GET BLOCKCHAIN RECORD
        # ----------------------------------------------------

        try:

            drug = get_drug(
                drug_id
            )

        except Exception as e:

            st.error(
                "Unable to retrieve drug from blockchain."
            )

            st.code(str(e))

            st.stop()

        status = int(drug[11])
        current_owner = drug[10]

        # ----------------------------------------------------
        # DISPLAY BASIC INFORMATION
        # ----------------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.write("**Drug ID**")
            st.write(drug[0])

        with col2:

            st.write("**Drug Name**")
            st.write(drug[2])

        with col3:

            st.write("**Current Status**")

            status_name = get_status_name(
                status
            )

            if status_name == "MANUFACTURED":

                st.info(status_name)

            elif status_name == "SHIPPED":

                st.warning(status_name)

            elif status_name == "RECEIVED":

                st.success(status_name)

            elif status_name == "DISPENSED":

                st.success(status_name)

        st.divider()

        # ----------------------------------------------------
        # CURRENT OWNER
        # ----------------------------------------------------

        st.write(
            "**Current Owner Wallet:**"
        )

        st.code(
            current_owner
        )

        st.divider()

        # ====================================================
        # STAGE 1
        # MANUFACTURER → DISTRIBUTOR
        # ====================================================

        if (
            status == 0
            and current_owner.lower()
            == manufacturer.lower()
        ):

            st.subheader(
                "Stage 1 — Ship to Distributor"
            )

            st.write(
                "The manufacturer can now ship this "
                "drug to the distributor."
            )

            if st.button(
                "Ship to Distributor",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Processing blockchain transaction..."
                    ):

                        result = ship_drug(
                            drug_id=drug_id,
                            receiver_address=distributor,
                            sender_address=manufacturer
                        )

                    update_drug(
                        drug_id,
                        current_owner=distributor,
                        status="SHIPPED"
                    )

                    add_transaction(
                        drug_id=drug_id,
                        action="SHIP_TO_DISTRIBUTOR",
                        sender=result["sender"],
                        receiver=result["receiver"],
                        block_number=result[
                            "block_number"
                        ],
                        transaction_hash=result[
                            "transaction_hash"
                        ]
                    )

                    st.success(
                        "Drug shipped to distributor."
                    )

                    st.write(
                        "**Transaction Hash:**"
                    )

                    st.code(
                        result["transaction_hash"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Shipment failed."
                    )

                    st.code(str(e))


        # ====================================================
        # STAGE 2
        # DISTRIBUTOR RECEIVES
        # ====================================================

        elif (
            status == 1
            and current_owner.lower()
            == distributor.lower()
        ):

            st.subheader(
                "Stage 2 — Distributor Receives Drug"
            )

            st.write(
                "The distributor must confirm receipt "
                "before shipping the drug to the hospital."
            )

            if st.button(
                "Distributor Receive",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Confirming receipt on blockchain..."
                    ):

                        result = receive_drug(
                            drug_id=drug_id,
                            receiver_address=distributor
                        )

                    update_drug(
                        drug_id,
                        current_owner=distributor,
                        status="RECEIVED"
                    )

                    add_transaction(
                        drug_id=drug_id,
                        action="DISTRIBUTOR_RECEIVE",
                        sender=distributor,
                        receiver=distributor,
                        block_number=result[
                            "block_number"
                        ],
                        transaction_hash=result[
                            "transaction_hash"
                        ]
                    )

                    st.success(
                        "Distributor received the drug."
                    )

                    st.code(
                        result["transaction_hash"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Receiving transaction failed."
                    )

                    st.code(str(e))


        # ====================================================
        # STAGE 3
        # DISTRIBUTOR → HOSPITAL
        # ====================================================

        elif (
            status == 2
            and current_owner.lower()
            == distributor.lower()
        ):

            st.subheader(
                "Stage 3 — Ship to Hospital"
            )

            st.write(
                "The distributor can now ship the drug "
                "to the hospital."
            )

            if st.button(
                "Ship to Hospital",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Processing hospital shipment..."
                    ):

                        result = ship_to_hospital(
                            drug_id=drug_id,
                            hospital_address=hospital,
                            distributor_address=distributor
                        )

                    update_drug(
                        drug_id,
                        current_owner=hospital,
                        status="SHIPPED"
                    )

                    add_transaction(
                        drug_id=drug_id,
                        action="SHIP_TO_HOSPITAL",
                        sender=result["sender"],
                        receiver=result["receiver"],
                        block_number=result[
                            "block_number"
                        ],
                        transaction_hash=result[
                            "transaction_hash"
                        ]
                    )

                    st.success(
                        "Drug shipped to hospital."
                    )

                    st.code(
                        result["transaction_hash"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Hospital shipment failed."
                    )

                    st.code(str(e))

        # STAGE 4
        # HOSPITAL RECEIVES
        # ====================================================
        elif (
            status == 1
            and current_owner.lower()
            == hospital.lower()
        ):
            st.subheader(
                "Stage 4 — Hospital Receives Drug"
            )

            st.write(
                "The hospital must confirm receipt "
                "of the shipment."
            )

            if st.button(
                "Hospital Receive",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Confirming hospital receipt..."
                    ):

                        result = hospital_receive_drug(
                            drug_id=drug_id,
                            hospital_address=hospital
                        )

                    update_drug(
                        drug_id,
                        current_owner=hospital,
                        status="RECEIVED"
                    )

                    add_transaction(
                        drug_id=drug_id,
                        action="HOSPITAL_RECEIVE",
                        sender=hospital,
                        receiver=hospital,
                        block_number=result[
                            "block_number"
                        ],
                        transaction_hash=result[
                            "transaction_hash"
                        ]
                    )

                    st.success(
                        "Hospital received the drug."
                    )

                    st.code(
                        result["transaction_hash"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Hospital receiving failed."
                    )

                    st.code(str(e))


        # ====================================================
        # STAGE 5
        # HOSPITAL → PATIENT
        # ====================================================

        elif (
            status == 2
            and current_owner.lower()
            == hospital.lower()
        ):

            st.subheader(
                "Stage 5 — Dispense to Patient"
            )

            st.write(
                "The hospital can now dispense the "
                "drug to the patient."
            )

            if st.button(
                "Dispense to Patient",
                use_container_width=True
            ):

                try:

                    with st.spinner(
                        "Recording dispensing transaction..."
                    ):

                        result = dispense_drug(
                            drug_id=drug_id,
                            hospital_address=hospital
                        )

                    update_drug(
                        drug_id,
                        current_owner=hospital,
                        status="DISPENSED"
                    )

                    add_transaction(
                        drug_id=drug_id,
                        action="DISPENSE_TO_PATIENT",
                        sender=hospital,
                        receiver="PATIENT",
                        block_number=result[
                            "block_number"
                        ],
                        transaction_hash=result[
                            "transaction_hash"
                        ]
                    )

                    st.success(
                        "Drug dispensed to patient successfully."
                    )

                    st.code(
                        result["transaction_hash"]
                    )

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Dispensing transaction failed."
                    )

                    st.code(str(e))


        # ====================================================
        # COMPLETED
        # ====================================================

        elif status == 3:

            st.success(
                "Supply chain completed. "
                "This drug has been dispensed to the patient."
            )

            st.balloons()


        # ====================================================
        # UNEXPECTED STATE
        # ====================================================

        else:

            st.warning(
                "No action is currently available "
                "for this drug."
            )


# ============================================================
# VERIFY DRUG
# ============================================================

elif menu == "Verify Drug":

    st.header("Verify Drug")

    st.write(
        "Verify the authenticity and complete history "
        "of a pharmaceutical drug."
    )

    st.divider()

    drug_id = st.text_input(
        "Enter Drug ID",
        placeholder="Example: DRG-2026-BATCH001"
    ).strip()

    if st.button(
        "Verify Drug",
        use_container_width=True
    ):

        if not drug_id:

            st.error(
                "Please enter a Drug ID."
            )

            st.stop()

        # ----------------------------------------------------
        # BLOCKCHAIN CHECK
        # ----------------------------------------------------

        try:

            blockchain_exists = (
                blockchain_drug_exists(
                    drug_id
                )
            )

        except Exception as e:

            st.error(
                "Blockchain verification failed."
            )

            st.code(str(e))

            st.stop()

        # ----------------------------------------------------
        # DATABASE CHECK
        # ----------------------------------------------------

        try:

            database_exists = (
                db_drug_exists(
                    drug_id
                )
            )

        except Exception:

            database_exists = False

        # ----------------------------------------------------
        # BOTH EXIST
        # ----------------------------------------------------

        if blockchain_exists:

            st.success(
                "✓ Drug verified on blockchain."
            )

            if database_exists:

                st.success(
                    "✓ Drug found in local database."
                )

            else:

                st.warning(
                    "Drug exists on blockchain but "
                    "was not found in the local database."
                )

            # ------------------------------------------------
            # GET BLOCKCHAIN DATA
            # ------------------------------------------------

            try:

                drug = get_drug(
                    drug_id
                )

            except Exception as e:

                st.error(
                    "Unable to retrieve blockchain record."
                )

                st.code(str(e))

                st.stop()

            st.divider()

            display_blockchain_drug(
                drug
            )

            # ------------------------------------------------
            # VERIFICATION STATUS
            # ------------------------------------------------

            st.divider()

            st.subheader(
                "Authenticity Status"
            )

            if database_exists:

                st.success(
                    "AUTHENTIC — Blockchain and database records exist."
                )

            else:

                st.warning(
                    "BLOCKCHAIN VERIFIED — Local database record missing."
                )

            # ------------------------------------------------
            # TRANSACTION HISTORY
            # ------------------------------------------------

            st.divider()

            display_transaction_history(
                drug_id
            )

            # ------------------------------------------------
            # CONTRACT
            # ------------------------------------------------

            st.divider()

            st.subheader(
                "Smart Contract"
            )

            st.write(
                "Contract Address:"
            )

            st.code(
                CONTRACT_ADDRESS
            )

        # ----------------------------------------------------
        # ONLY DATABASE
        # ----------------------------------------------------

        elif database_exists:
            st.warning(
                "Drug exists in the local database "
                "but could not be verified on blockchain."
            )
            try:

                db_record = db_get_drug(
                    drug_id
                )

                st.subheader(
                    "Local Database Record"
                )

                st.write(
                    db_record
                )

            except Exception as e:

                st.code(str(e))

        else:
            st.error(
                "Drug not found."
            )
            st.write(
                "No matching drug was found in "
                "the blockchain or database."
            )
# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption(
    "PharmaChain | Blockchain-Based Pharmaceutical "
    "Supply Chain Tracking System"
)