import streamlit as st
import qrcode

from io import BytesIO
from datetime import datetime, date

from database import (
    create_database,
    drug_exists,
    add_drug,
    update_drug_status,
    add_transaction,
    get_transactions,
)

from blockchain import (
    blockchain_ready,
    blockchain_connected,
    blockchain_drug_exists,
    manufacture_drug,
    ship_drug,
    receive_drug,
    ship_to_hospital,
    dispense_drug,
    get_drug,
    wallet_balance_eth,
    CONTRACT_ADDRESS,
    ACCOUNT_ADDRESS,
    CONFIG_ERROR,
)

st.set_page_config(
    page_title="PharmaChain",
    page_icon="💊",
    layout="wide",
)

create_database()

st.title("💊 PharmaChain")
st.caption("Blockchain-Based Drug Tracking System")

if blockchain_ready() and blockchain_connected():
    st.sidebar.success("🟢 Ethereum Sepolia Connected")
    st.sidebar.caption(f"Wallet: {ACCOUNT_ADDRESS[:8]}...{ACCOUNT_ADDRESS[-6:]}")
    st.sidebar.caption(f"Balance: {wallet_balance_eth():.6f} ETH")
elif CONFIG_ERROR:
    st.sidebar.error("🔴 Blockchain Not Ready")
else:
    st.sidebar.error("🔴 Blockchain Disconnected")

st.sidebar.title("📋 Navigation")
menu = st.sidebar.radio(
    "Select Module",
    [
        "Register Drug",
        "Verify Drug",
        "Drug Lifecycle",
    ],
)


def show_config_error():
    st.error("Blockchain configuration is incomplete.")
    if CONFIG_ERROR:
        st.code(CONFIG_ERROR)
    st.info(
        "For local testing use .env. For Streamlit Cloud use App Settings → Secrets. "
        "Never commit your private key."
    )


def make_qr(drug_id):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(drug_id)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def status_name(status):
    names = {
        0: "Manufactured",
        1: "Shipped",
        2: "Received",
        3: "Dispensed",
    }
    return names.get(int(status), str(status))


def timestamp_text(timestamp):
    if int(timestamp) <= 0:
        return "Not recorded"
    return datetime.fromtimestamp(int(timestamp)).strftime("%Y-%m-%d %H:%M:%S")


if menu == "Register Drug":
    st.header("💊 Register New Drug")
    st.write("Register a drug on Ethereum Sepolia and generate its QR code.")

    with st.form("register_drug_form"):
        col1, col2 = st.columns(2)
        with col1:
            drug_name = st.text_input("Drug Name", placeholder="Example: Paracetamol")
        with col2:
            batch_number = st.text_input("Batch Number", placeholder="Example: PAA2")

        col3, col4 = st.columns(2)
        with col3:
            manufacturer = st.text_input("Manufacturer", placeholder="Example: ABC Pharma")
        with col4:
            quantity = st.number_input("Quantity", min_value=1, value=100, step=1)

        col5, col6 = st.columns(2)
        with col5:
            manufacturing_date = st.date_input("Manufacturing Date", value=date.today())
        with col6:
            expiry_date = st.date_input("Expiry Date", value=date.today())

        submitted = st.form_submit_button("🚀 Register Drug", use_container_width=True)

    if submitted:
        if not blockchain_connected():
            show_config_error()
            st.stop()
        if not drug_name.strip() or not batch_number.strip() or not manufacturer.strip():
            st.error("Drug name, batch number and manufacturer are required.")
            st.stop()
        if expiry_date <= manufacturing_date:
            st.error("Expiry date must be after manufacturing date.")
            st.stop()

        drug_id = f"DRG-{manufacturing_date.year}-{batch_number.upper().strip()}"

        if drug_exists(drug_id):
            st.error(f"Drug ID {drug_id} already exists in the local database.")
            st.stop()
        if blockchain_drug_exists(drug_id):
            st.error(f"Drug ID {drug_id} already exists on Ethereum Sepolia.")
            st.stop()

        try:
            with st.spinner("Recording drug on Ethereum Sepolia..."):
                result = manufacture_drug(
                    drug_id=drug_id,
                    batch_id=batch_number.strip(),
                    drug_name=drug_name.strip(),
                    manufacturer_name=manufacturer.strip(),
                    quantity=int(quantity),
                    manufacturing_date=manufacturing_date.strftime("%Y-%m-%d"),
                    expiry_date=expiry_date.strftime("%Y-%m-%d"),
                )

            tx_hash = result["transaction_hash"]
            block_number = result["block_number"]
            sender = result["sender"]
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            qr_data = drug_id

            add_drug(
                drug_id=drug_id,
                drug_name=drug_name.strip(),
                batch_number=batch_number.strip(),
                manufacturing_date=manufacturing_date.strftime("%Y-%m-%d"),
                expiry_date=expiry_date.strftime("%Y-%m-%d"),
                quantity=int(quantity),
                manufacturer=manufacturer.strip(),
                current_owner=sender,
                status="Manufactured",
                qr_data=qr_data,
                created_at=now,
            )
            add_transaction(
                drug_id=drug_id,
                action="Manufactured",
                sender=sender,
                receiver=sender,
                timestamp=now,
                block_number=block_number,
                transaction_hash=tx_hash,
            )

            st.success("✅ Drug registered successfully!")
            st.write(f"**Drug ID:** {drug_id}")
            st.write(f"**Transaction Hash:** `{tx_hash}`")
            st.write(f"**Block Number:** {block_number}")
            st.write(f"**Contract:** `{CONTRACT_ADDRESS}`")

            qr_bytes = make_qr(drug_id)
            qr_col1, qr_col2 = st.columns(2)
            with qr_col1:
                st.image(qr_bytes, caption=drug_id, width=300)
            with qr_col2:
                st.code(qr_data)
                st.download_button(
                    "⬇️ Download QR Code",
                    data=qr_bytes,
                    file_name=f"{drug_id}.png",
                    mime="image/png",
                    use_container_width=True,
                )

        except Exception as exc:
            st.error("❌ Drug registration failed.")
            st.exception(exc)


elif menu == "Verify Drug":
    st.header("🔍 Verify Drug")
    st.write("Enter a Drug ID to read its record directly from the blockchain.")

    drug_id = st.text_input("Drug ID", placeholder="Example: DRG-2026-PAA2").strip()

    if st.button("🔍 Verify Drug", use_container_width=True):
        if not drug_id:
            st.warning("Please enter a Drug ID.")
            st.stop()
        if not blockchain_connected():
            show_config_error()
            st.stop()

        try:
            if not blockchain_drug_exists(drug_id):
                st.error("❌ Drug not found on Ethereum Sepolia.")
                st.stop()

            drug = get_drug(drug_id)
            (
                returned_drug_id,
                batch_id,
                returned_drug_name,
                manufacturer_name,
                quantity,
                manufacturing_timestamp,
                expiry_timestamp,
                shipping_timestamp,
                receiving_timestamp,
                manufacturer_address,
                current_owner,
                status,
                exists,
            ) = drug

            st.success("✅ Drug verified successfully!")

            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Drug ID:** {returned_drug_id}")
                st.write(f"**Drug Name:** {returned_drug_name}")
                st.write(f"**Batch ID:** {batch_id}")
                st.write(f"**Manufacturer:** {manufacturer_name}")
                st.write(f"**Quantity:** {quantity}")
                st.write(f"**Status:** {status_name(status)}")
            with col2:
                st.write(f"**Manufacturing Date:** {timestamp_text(manufacturing_timestamp)}")
                st.write(f"**Expiry Date:** {timestamp_text(expiry_timestamp)}")
                st.write(f"**Shipping Date:** {timestamp_text(shipping_timestamp)}")
                st.write(f"**Receiving Date:** {timestamp_text(receiving_timestamp)}")
                st.write(f"**Manufacturer Address:** {manufacturer_address}")
                st.write(f"**Current Owner:** {current_owner}")

            st.subheader("⛓️ Blockchain")
            st.code(CONTRACT_ADDRESS)

            if drug_exists(drug_id):
                st.success("The drug also exists in the local SQLite database.")
            else:
                st.warning("The drug exists on-chain but is not in the local SQLite database.")

            history = get_transactions(drug_id)
            if history:
                st.subheader("🧾 Local Transaction History")
                st.dataframe(
                    [
                        {
                            "Action": row[0],
                            "Sender": row[1],
                            "Receiver": row[2],
                            "Timestamp": row[3],
                            "Block": row[4],
                            "Transaction Hash": row[5],
                        }
                        for row in history
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

        except Exception as exc:
            st.error("❌ Verification failed.")
            st.exception(exc)


elif menu == "Drug Lifecycle":
    st.header("🔄 Drug Lifecycle")
    st.write("Perform shipment and ownership transitions using the connected Sepolia wallet.")

    if not blockchain_connected():
        show_config_error()
        st.stop()

    drug_id = st.text_input("Drug ID", placeholder="Example: DRG-2026-PAA2").strip()

    if drug_id and st.button("Load Drug", use_container_width=True):
        try:
            if not blockchain_drug_exists(drug_id):
                st.error("Drug does not exist on the blockchain.")
            else:
                drug = get_drug(drug_id)
                st.info(f"Current blockchain status: **{status_name(drug[11])}**")
                st.write(f"Current owner: `{drug[10]}`")
        except Exception as exc:
            st.error("Could not load drug.")
            st.exception(exc)

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📦 Ship to Distributor",
        "📥 Receive",
        "🏥 Ship to Hospital",
        "💊 Dispense",
    ])

    with tab1:
        distributor = st.text_input("Distributor wallet address", key="distributor")
        if st.button("Ship Drug", key="ship_button", use_container_width=True):
            try:
                result = ship_drug(drug_id, distributor.strip())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_drug_status(drug_id, result["receiver"], "Shipped")
                add_transaction(
                    drug_id, "Shipped", result["sender"], result["receiver"],
                    now, result["block_number"], result["transaction_hash"]
                )
                st.success("Drug shipped successfully.")
                st.code(result["transaction_hash"])
            except Exception as exc:
                st.error("Shipment failed.")
                st.exception(exc)

    with tab2:
        if st.button("Receive Drug", key="receive_button", use_container_width=True):
            try:
                result = receive_drug(drug_id)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_drug_status(drug_id, result["sender"], "Received")
                add_transaction(
                    drug_id, "Received", result["sender"], result["sender"],
                    now, result["block_number"], result["transaction_hash"]
                )
                st.success("Drug received successfully.")
                st.code(result["transaction_hash"])
            except Exception as exc:
                st.error("Receive operation failed.")
                st.exception(exc)

    with tab3:
        hospital = st.text_input("Hospital wallet address", key="hospital")
        if st.button("Ship to Hospital", key="hospital_button", use_container_width=True):
            try:
                result = ship_to_hospital(drug_id, hospital.strip())
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_drug_status(drug_id, result["receiver"], "Shipped")
                add_transaction(
                    drug_id, "Shipped to Hospital", result["sender"], result["receiver"],
                    now, result["block_number"], result["transaction_hash"]
                )
                st.success("Drug shipped to hospital successfully.")
                st.code(result["transaction_hash"])
            except Exception as exc:
                st.error("Hospital shipment failed.")
                st.exception(exc)

    with tab4:
        if st.button("Dispense Drug", key="dispense_button", use_container_width=True):
            try:
                result = dispense_drug(drug_id)
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                update_drug_status(drug_id, result["sender"], "Dispensed")
                add_transaction(
                    drug_id, "Dispensed", result["sender"], result["sender"],
                    now, result["block_number"], result["transaction_hash"]
                )
                st.success("Drug dispensed successfully.")
                st.code(result["transaction_hash"])
            except Exception as exc:
                st.error("Dispense operation failed.")
                st.exception(exc)
