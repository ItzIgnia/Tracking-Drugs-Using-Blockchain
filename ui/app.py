import streamlit as st
import qrcode

from io import BytesIO
from datetime import datetime


# ============================================================
# DATABASE
# ============================================================

from database import (
    create_database,
    drug_exists,
    add_drug,
    add_transaction
)


# ============================================================
# BLOCKCHAIN
# ============================================================

from blockchain import (
    blockchain_connected,
    blockchain_drug_exists,
    manufacture_drug,
    get_drug,
    CONTRACT_ADDRESS,
    ACCOUNT_ADDRESS
)


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(

    page_title="PharmaChain",

    page_icon="💊",

    layout="wide"
)


# ============================================================
# APPLICATION TITLE
# ============================================================

st.title("💊 PharmaChain")

st.write(
    "Blockchain-Based Drug Tracking System"
)

st.caption(
    "Track pharmaceutical drugs using "
    "Blockchain, QR Codes and SQLite."
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

create_database()


# ============================================================
# BLOCKCHAIN CONNECTION STATUS
# ============================================================

if blockchain_connected():

    st.sidebar.success(
        "🟢 Blockchain Connected"
    )

else:

    st.sidebar.error(
        "🔴 Blockchain Disconnected"
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("📋 Navigation")

menu = st.sidebar.radio(

    "Select Module",

    [
        "Register Drug",
        "Verify Drug"
    ]
)


# ============================================================
# REGISTER DRUG
# ============================================================

if menu == "Register Drug":

    st.header("💊 Register New Drug")

    st.write(
        "Register a pharmaceutical drug on the "
        "blockchain and generate its QR code."
    )


    # ========================================================
    # FORM
    # ========================================================

    with st.form(
        "register_drug_form"
    ):

        col1, col2 = st.columns(2)


        # ----------------------------------------------------
        # DRUG NAME
        # ----------------------------------------------------

        with col1:

            drug_name = st.text_input(
                "Drug Name",
                placeholder="Example: Paracetamol"
            )


        # ----------------------------------------------------
        # BATCH NUMBER
        # ----------------------------------------------------

        with col2:

            batch_number = st.text_input(
                "Batch Number",
                placeholder="Example: PAA2"
            )


        col3, col4 = st.columns(2)


        # ----------------------------------------------------
        # MANUFACTURER
        # ----------------------------------------------------

        with col3:

            manufacturer = st.text_input(
                "Manufacturer",
                placeholder="Example: ABC Pharma"
            )


        # ----------------------------------------------------
        # QUANTITY
        # ----------------------------------------------------

        with col4:

            quantity = st.number_input(

                "Quantity",

                min_value=1,

                value=100,

                step=1
            )


        col5, col6 = st.columns(2)


        # ----------------------------------------------------
        # MANUFACTURING DATE
        # ----------------------------------------------------

        with col5:

            manufacturing_date = st.date_input(
                "Manufacturing Date"
            )


        # ----------------------------------------------------
        # EXPIRY DATE
        # ----------------------------------------------------

        with col6:

            expiry_date = st.date_input(
                "Expiry Date"
            )


        submitted = st.form_submit_button(
            "🚀 Register Drug",
            use_container_width=True
        )


    # ========================================================
    # FORM SUBMITTED
    # ========================================================

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


        if not manufacturer.strip():

            st.error(
                "Please enter the manufacturer."
            )

            st.stop()


        if expiry_date <= manufacturing_date:

            st.error(
                "Expiry date must be after "
                "manufacturing date."
            )

            st.stop()


        if not blockchain_connected():

            st.error(
                "Blockchain connection failed. "
                "Please check your RPC configuration."
            )

            st.stop()


        # ----------------------------------------------------
        # CREATE DRUG ID
        # ----------------------------------------------------

        drug_id = (

            f"DRG-{manufacturing_date.year}-"

            f"{batch_number.upper().strip()}"
        )


        # ----------------------------------------------------
        # CHECK LOCAL DATABASE
        # ----------------------------------------------------

        if drug_exists(drug_id):

            st.error(
                f"Drug ID {drug_id} already exists "
                "in the database."
            )

            st.stop()


        # ----------------------------------------------------
        # CHECK BLOCKCHAIN
        # ----------------------------------------------------

        if blockchain_drug_exists(drug_id):

            st.error(
                f"Drug ID {drug_id} already exists "
                "on the blockchain."
            )

            st.stop()


        # ----------------------------------------------------
        # QR DATA
        # ----------------------------------------------------

        qr_data = drug_id


        # ----------------------------------------------------
        # SHOW PROGRESS
        # ----------------------------------------------------

        with st.spinner(
            "Recording drug on blockchain..."
        ):

            try:

                # ============================================
                # BLOCKCHAIN TRANSACTION
                # ============================================

                blockchain_result = manufacture_drug(

                    drug_id=drug_id,

                    batch_id=batch_number.strip(),

                    drug_name=drug_name.strip(),

                    manufacturer_name=
                        manufacturer.strip(),

                    quantity=int(quantity),

                    manufacturing_date=
                        manufacturing_date.strftime(
                            "%Y-%m-%d"
                        ),

                    expiry_date=
                        expiry_date.strftime(
                            "%Y-%m-%d"
                        )
                )


                # ============================================
                # TRANSACTION INFORMATION
                # ============================================

                transaction_hash = (
                    blockchain_result[
                        "transaction_hash"
                    ]
                )

                block_number = (
                    blockchain_result[
                        "block_number"
                    ]
                )

                sender = (
                    blockchain_result[
                        "sender"
                    ]
                )


                # ============================================
                # SAVE TO SQLITE
                # ============================================

                add_drug(

                    drug_id=drug_id,

                    drug_name=drug_name.strip(),

                    batch_number=
                        batch_number.strip(),

                    manufacturing_date=
                        manufacturing_date.strftime(
                            "%Y-%m-%d"
                        ),

                    expiry_date=
                        expiry_date.strftime(
                            "%Y-%m-%d"
                        ),

                    quantity=int(quantity),

                    manufacturer=
                        manufacturer.strip(),

                    current_owner=sender,

                    status="Manufactured",

                    qr_data=qr_data,

                    created_at=
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                )


                # ============================================
                # SAVE TRANSACTION
                # ============================================

                add_transaction(

                    drug_id=drug_id,

                    action="Manufactured",

                    sender=sender,

                    receiver=sender,

                    timestamp=
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),

                    block_number=block_number,

                    transaction_hash=
                        transaction_hash
                )


                # ============================================
                # SUCCESS MESSAGE
                # ============================================

                st.success(
                    "✅ Drug registered successfully!"
                )

                st.info(
                    "The drug has been recorded on "
                    "the blockchain and database."
                )


                # ============================================
                # DISPLAY INFORMATION
                # ============================================

                st.subheader(
                    "📦 Drug Information"
                )


                info_col1, info_col2 = st.columns(2)


                with info_col1:

                    st.write(
                        f"**Drug ID:** {drug_id}"
                    )

                    st.write(
                        f"**Drug Name:** {drug_name}"
                    )

                    st.write(
                        f"**Batch:** {batch_number}"
                    )

                    st.write(
                        f"**Manufacturer:** "
                        f"{manufacturer}"
                    )

                    st.write(
                        f"**Quantity:** {quantity}"
                    )


                with info_col2:

                    st.write(
                        f"**Manufacturing Date:** "
                        f"{manufacturing_date}"
                    )

                    st.write(
                        f"**Expiry Date:** "
                        f"{expiry_date}"
                    )

                    st.write(
                        "**Status:** Manufactured"
                    )

                    st.write(
                        f"**Owner:** {sender}"
                    )


                # ============================================
                # BLOCKCHAIN INFORMATION
                # ============================================

                st.subheader(
                    "⛓️ Blockchain Information"
                )


                st.code(
                    f"Contract Address:\n"
                    f"{CONTRACT_ADDRESS}"
                )


                st.code(
                    f"Transaction Hash:\n"
                    f"{transaction_hash}"
                )


                st.write(
                    f"**Block Number:** "
                    f"{block_number}"
                )


                # ============================================
                # QR CODE
                # ============================================

                st.subheader(
                    "📱 Drug QR Code"
                )


                qr = qrcode.QRCode(

                    version=1,

                    box_size=10,

                    border=5
                )


                qr.add_data(
                    qr_data
                )

                qr.make(
                    fit=True
                )


                qr_image = qr.make_image(

                    fill_color="black",

                    back_color="white"
                )


                # Convert image to bytes

                img_bytes = BytesIO()

                qr_image.save(
                    img_bytes,
                    format="PNG"
                )

                qr_bytes = (
                    img_bytes.getvalue()
                )


                qr_col1, qr_col2 = st.columns(2)


                with qr_col1:

                    st.image(

                        qr_bytes,

                        caption=drug_id,

                        width=300
                    )


                with qr_col2:

                    st.write(
                        "### QR Data"
                    )

                    st.code(
                        qr_data
                    )


                    st.download_button(

                        label=
                            "⬇️ Download QR Code",

                        data=qr_bytes,

                        file_name=
                            f"{drug_id}.png",

                        mime="image/png",

                        use_container_width=True
                    )


            # ====================================================
            # ERROR HANDLING
            # ====================================================

            except Exception as e:

                st.error(
                    "❌ Drug registration failed."
                )

                st.exception(e)


# ============================================================
# VERIFY DRUG
# ============================================================

elif menu == "Verify Drug":

    st.header("🔍 Verify Drug")

    st.write(
        "Enter a Drug ID to verify its "
        "blockchain record."
    )


    # ========================================================
    # INPUT
    # ========================================================

    drug_id_input = st.text_input(

        "Drug ID",

        placeholder="Example: DRG-2026-PAA2"
    )


    verify_button = st.button(
        "🔍 Verify Drug",
        use_container_width=True
    )


    # ========================================================
    # VERIFY
    # ========================================================

    if verify_button:

        drug_id = drug_id_input.strip()


        if not drug_id:

            st.warning(
                "Please enter a Drug ID."
            )

            st.stop()


        if not blockchain_connected():

            st.error(
                "Blockchain connection failed."
            )

            st.stop()


        # ----------------------------------------------------
        # CHECK BLOCKCHAIN
        # ----------------------------------------------------

        with st.spinner(
            "Checking blockchain..."
        ):

            try:

                exists = blockchain_drug_exists(
                    drug_id
                )


                if not exists:

                    st.error(
                        "❌ Drug not found on blockchain."
                    )

                    st.stop()


                # ------------------------------------------------
                # GET BLOCKCHAIN RECORD
                # ------------------------------------------------

                drug = get_drug(
                    drug_id
                )


                st.success(
                    "✅ Drug verified successfully!"
                )


                # ------------------------------------------------
                # DISPLAY BLOCKCHAIN DATA
                # ------------------------------------------------

                st.subheader(
                    "⛓️ Blockchain Record"
                )


                (
                    returned_drug_id,

                    batch_id,

                    returned_drug_name,

                    manufacturer_name,

                    blockchain_quantity,

                    manufacturing_timestamp,

                    expiry_timestamp,

                    shipping_timestamp,

                    receiving_timestamp,

                    manufacturer_address,

                    current_owner,

                    status,

                    exists

                ) = drug


                # ------------------------------------------------
                # STATUS CONVERSION
                # ------------------------------------------------

                status_names = {

                    0: "Manufactured",

                    1: "Shipped",

                    2: "Received",

                    3: "Dispensed"
                }


                status_text = status_names.get(

                    int(status),

                    str(status)
                )


                # ------------------------------------------------
                # DATE CONVERSION
                # ------------------------------------------------

                manufacturing_date_text = (
                    datetime.fromtimestamp(
                        int(manufacturing_timestamp)
                    ).strftime(
                        "%Y-%m-%d"
                    )
                )


                expiry_date_text = (
                    datetime.fromtimestamp(
                        int(expiry_timestamp)
                    ).strftime(
                        "%Y-%m-%d"
                    )
                )


                # ------------------------------------------------
                # DISPLAY
                # ------------------------------------------------

                col1, col2 = st.columns(2)


                with col1:

                    st.write(
                        f"**Drug ID:** "
                        f"{returned_drug_id}"
                    )

                    st.write(
                        f"**Drug Name:** "
                        f"{returned_drug_name}"
                    )

                    st.write(
                        f"**Batch ID:** "
                        f"{batch_id}"
                    )

                    st.write(
                        f"**Manufacturer:** "
                        f"{manufacturer_name}"
                    )

                    st.write(
                        f"**Quantity:** "
                        f"{blockchain_quantity}"
                    )


                with col2:

                    st.write(
                        f"**Manufacturing Date:** "
                        f"{manufacturing_date_text}"
                    )

                    st.write(
                        f"**Expiry Date:** "
                        f"{expiry_date_text}"
                    )

                    st.write(
                        f"**Status:** "
                        f"{status_text}"
                    )

                    st.write(
                        f"**Manufacturer Address:** "
                        f"{manufacturer_address}"
                    )

                    st.write(
                        f"**Current Owner:** "
                        f"{current_owner}"
                    )


                # ------------------------------------------------
                # SHIPPING DATE
                # ------------------------------------------------

                if int(shipping_timestamp) > 0:

                    shipping_date = (
                        datetime.fromtimestamp(
                            int(shipping_timestamp)
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )

                    st.write(
                        f"**Shipping Date:** "
                        f"{shipping_date}"
                    )


                # ------------------------------------------------
                # RECEIVING DATE
                # ------------------------------------------------

                if int(receiving_timestamp) > 0:

                    receiving_date = (
                        datetime.fromtimestamp(
                            int(receiving_timestamp)
                        ).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )

                    st.write(
                        f"**Receiving Date:** "
                        f"{receiving_date}"
                    )


                # ------------------------------------------------
                # CONTRACT INFORMATION
                # ------------------------------------------------

                st.subheader(
                    "🔗 Contract"
                )

                st.code(
                    CONTRACT_ADDRESS
                )


                # ------------------------------------------------
                # LOCAL DATABASE CHECK
                # ------------------------------------------------

                st.subheader(
                    "🗄️ Database Verification"
                )


                if drug_exists(drug_id):

                    st.success(
                        "Drug also exists in "
                        "the local database."
                    )

                else:

                    st.warning(
                        "Drug exists on blockchain "
                        "but is not present in the "
                        "local database."
                    )


            except Exception as e:

                st.error(
                    "❌ Verification failed."
                )

                st.exception(e)
