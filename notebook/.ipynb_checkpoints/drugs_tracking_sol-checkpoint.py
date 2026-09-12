import streamlit as st
import qrcode

from io import BytesIO


# ============================================================
# DATABASE
# ============================================================

from database import (
    create_database,
    add_drug,
    add_transaction,
    drug_exists as db_drug_exists
)


# ============================================================
# BLOCKCHAIN
# ============================================================

from blockchain import (
    blockchain_connected,
    blockchain_drug_exists,
    manufacture_drug,
    get_drug,
    CONTRACT_ADDRESS
)


# ============================================================
# INITIALIZE DATABASE
# ============================================================

create_database()


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="PharmaChain",
    page_icon="💊",
    layout="wide"
)


# ============================================================
# HEADER
# ============================================================

st.title("💊 PharmaChain")

st.write(
    "Blockchain-Based Drug Tracking System"
)

st.divider()


# ============================================================
# BLOCKCHAIN STATUS
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

st.sidebar.title("PharmaChain")

menu = st.sidebar.selectbox(
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
        "Enter the drug production details below."
    )


    # ========================================================
    # REGISTRATION FORM
    # ========================================================

    with st.form("drug_registration"):

        col1, col2 = st.columns(2)


        # ----------------------------------------------------
        # LEFT COLUMN
        # ----------------------------------------------------

        with col1:

            drug_name = st.text_input(
                "Drug Name",
                placeholder="Example: Paracetamol 500mg"
            )

            batch_number = st.text_input(
                "Batch Number",
                placeholder="Example: PCM-001"
            )

            manufacturer = st.text_input(
                "Manufacturer",
                placeholder="Example: ABC Pharmaceuticals"
            )

            quantity = st.number_input(
                "Quantity",
                min_value=1,
                value=100,
                step=1
            )


        # ----------------------------------------------------
        # RIGHT COLUMN
        # ----------------------------------------------------

        with col2:

            manufacturing_date = st.date_input(
                "Manufacturing Date"
            )

            expiry_date = st.date_input(
                "Expiry Date"
            )


        register_button = st.form_submit_button(
            "💊 Register Drug",
            use_container_width=True
        )


    # ========================================================
    # REGISTRATION PROCESS
    # ========================================================

    if register_button:


        # ====================================================
        # VALIDATION
        # ====================================================

        if not drug_name.strip():

            st.error(
                "Please enter the drug name."
            )


        elif not batch_number.strip():

            st.error(
                "Please enter the batch number."
            )


        elif not manufacturer.strip():

            st.error(
                "Please enter the manufacturer."
            )


        elif expiry_date <= manufacturing_date:

            st.error(
                "Expiry date must be later than "
                "manufacturing date."
            )


        elif not blockchain_connected():

            st.error(
                "❌ Blockchain is not connected."
            )


        else:


            # =================================================
            # CREATE UNIQUE DRUG ID
            # =================================================

            drug_id = (
                f"DRG-{manufacturing_date.year}-"
                f"{batch_number.upper().strip()}"
            )


            # =================================================
            # CHECK SQLITE
            # =================================================

            database_exists = db_drug_exists(
                drug_id
            )


            # =================================================
            # CHECK BLOCKCHAIN
            # =================================================

            blockchain_exists = blockchain_drug_exists(
                drug_id
            )


            if database_exists:

                st.error(
                    f"❌ Drug ID {drug_id} already "
                    "exists in the database."
                )


            elif blockchain_exists:

                st.error(
                    f"❌ Drug ID {drug_id} already "
                    "exists on the blockchain."
                )


            else:

                try:


                    # =========================================
                    # QR DATA
                    # =========================================

                    qr_data = drug_id


                    # =========================================
                    # BLOCKCHAIN TRANSACTION
                    # =========================================

                    st.info(
                        "⛓️ Recording drug on blockchain..."
                    )


                    with st.spinner(
                        "Waiting for blockchain confirmation..."
                    ):

                        blockchain_result = manufacture_drug(

                            drug_id=drug_id,

                            batch_id=batch_number.strip(),

                            drug_name=drug_name.strip(),

                            manufacturer_name=
                                manufacturer.strip(),

                            quantity=int(quantity),

                            manufacturing_date=
                                manufacturing_date,

                            expiry_date=
                                expiry_date
                        )


                    # =========================================
                    # SAVE DRUG TO SQLITE
                    # =========================================

                    add_drug(

                        drug_id=drug_id,

                        drug_name=drug_name.strip(),

                        batch_number=
                            batch_number.strip(),

                        manufacturing_date=
                            str(manufacturing_date),

                        expiry_date=
                            str(expiry_date),

                        quantity=int(quantity),

                        manufacturer=
                            manufacturer.strip(),

                        qr_data=qr_data
                    )


                    # =========================================
                    # SAVE BLOCKCHAIN TRANSACTION
                    # =========================================

                    add_transaction(

                        drug_id=drug_id,

                        action="MANUFACTURED",

                        sender=
                            blockchain_result["sender"],

                        receiver=
                            manufacturer.strip(),

                        block_number=
                            blockchain_result[
                                "block_number"
                            ],

                        transaction_hash=
                            blockchain_result[
                                "transaction_hash"
                            ]
                    )


                    # =========================================
                    # GENERATE QR CODE
                    # =========================================

                    qr = qrcode.QRCode(

                        version=1,

                        error_correction=
                            qrcode.constants.ERROR_CORRECT_L,

                        box_size=10,

                        border=4
                    )


                    qr.add_data(qr_data)

                    qr.make(
                        fit=True
                    )


                    qr_image = qr.make_image(

                        fill_color="black",

                        back_color="white"
                    )


                    # =========================================
                    # SUCCESS MESSAGE
                    # =========================================

                    st.success(
                        "✅ Drug registered successfully!"
                    )

                    st.info(
                        "The drug has been recorded on "
                        "the blockchain and database."
                    )


                    st.divider()


                    # =========================================
                    # BLOCKCHAIN INFORMATION
                    # =========================================

                    st.subheader(
                        "⛓️ Blockchain Information"
                    )


                    blockchain_col1, blockchain_col2 = (
                        st.columns(2)
                    )


                    with blockchain_col1:

                        st.write(
                            "**Contract Address:**"
                        )

                        st.code(
                            CONTRACT_ADDRESS
                        )


                        st.write(
                            "**Block Number:** "
                            f"{blockchain_result['block_number']}"
                        )


                    with blockchain_col2:

                        st.write(
                            "**Transaction Hash:**"
                        )

                        st.code(
                            blockchain_result[
                                "transaction_hash"
                            ]
                        )


                    st.divider()


                    # =========================================
                    # RESULT COLUMNS
                    # =========================================

                    result_col1, result_col2 = (
                        st.columns(2)
                    )


                    # =========================================
                    # DRUG INFORMATION
                    # =========================================

                    with result_col1:

                        st.subheader(
                            "💊 Drug Information"
                        )


                        st.write(
                            f"**Drug ID:** {drug_id}"
                        )


                        st.write(
                            f"**Drug Name:** "
                            f"{drug_name}"
                        )


                        st.write(
                            f"**Batch Number:** "
                            f"{batch_number}"
                        )


                        st.write(
                            f"**Manufacturer:** "
                            f"{manufacturer}"
                        )


                        st.write(
                            f"**Quantity:** "
                            f"{quantity}"
                        )


                        st.write(
                            f"**Manufacturing Date:** "
                            f"{manufacturing_date}"
                        )


                        st.write(
                            f"**Expiry Date:** "
                            f"{expiry_date}"
                        )


                        st.write(
                            "**Status:** MANUFACTURED"
                        )


                        # ============================================================
                        # QR CODE
                        # ============================================================

                        with result_col2:

                            st.subheader("📱 Drug QR Code")

                            # Convert QR image to PNG bytes
                            img_bytes = BytesIO()

                            qr_image.save(
                                img_bytes,
                                format="PNG"
                            )

                            img_bytes.seek(0)

                            # Display QR code
                            st.image(
                            img_bytes.getvalue(),
                            caption=drug_id,
                            width=300
                            )

                            # Download QR code
                            st.download_button(
                                label="⬇️ Download QR Code",
                                data=img_bytes.getvalue(),
                                file_name=f"{drug_id}.png",
                                mime="image/png",
                                use_container_width=True
                            )


                # =================================================
                # ERROR HANDLING
                # =================================================

                except Exception as e:

                    st.error(
                        "❌ Drug registration failed."
                    )

                    st.error(
                        "The blockchain transaction "
                        "could not be completed."
                    )

                    st.exception(e)


# ============================================================
# VERIFY DRUG
# ============================================================

elif menu == "Verify Drug":

    st.header("🔍 Verify Drug")

    st.write(
        "Verify a drug using the blockchain."
    )


    # ========================================================
    # DRUG ID INPUT
    # ========================================================

    drug_id = st.text_input(

        "Enter Drug ID",

        placeholder=
            "Example: DRG-2026-PCM-001"
    )


    # ========================================================
    # VERIFY BUTTON
    # ========================================================

    if st.button(

        "🔍 Verify Drug",

        use_container_width=True
    ):


        # ====================================================
        # VALIDATION
        # ====================================================

        if not drug_id.strip():

            st.warning(
                "Please enter a Drug ID."
            )


        elif not blockchain_connected():

            st.error(
                "❌ Blockchain is not connected."
            )


        else:

            try:


                # =============================================
                # CHECK BLOCKCHAIN
                # =============================================

                exists_on_blockchain = (
                    blockchain_drug_exists(
                        drug_id.strip()
                    )
                )


                # =============================================
                # CHECK DATABASE
                # =============================================

                exists_in_database = (
                    db_drug_exists(
                        drug_id.strip()
                    )
                )


                if exists_on_blockchain:


                    # =========================================
                    # GET BLOCKCHAIN DATA
                    # =========================================

                    drug_data = get_drug(
                        drug_id.strip()
                    )


                    st.success(
                        "✅ Drug verified successfully!"
                    )


                    st.divider()


                    # =========================================
                    # VERIFICATION STATUS
                    # =========================================

                    st.subheader(
                        "⛓️ Blockchain Verification"
                    )


                    st.write(
                        "**Blockchain:** 🟢 VERIFIED"
                    )


                    st.write(
                        "**Database:** "
                        +
                        (
                            "🟢 FOUND"
                            if exists_in_database
                            else
                            "🟡 NOT FOUND"
                        )
                    )


                    st.write(
                        f"**Drug ID:** {drug_id}"
                    )


                    st.divider()


                    # =========================================
                    # BLOCKCHAIN DRUG DETAILS
                    # =========================================

                    st.subheader(
                        "💊 Drug Details"
                    )


                    detail_col1, detail_col2 = (
                        st.columns(2)
                    )


                    with detail_col1:

                        st.write(
                            f"**Drug ID:** "
                            f"{drug_data[0]}"
                        )


                        st.write(
                            f"**Batch ID:** "
                            f"{drug_data[1]}"
                        )


                        st.write(
                            f"**Drug Name:** "
                            f"{drug_data[2]}"
                        )


                        st.write(
                            f"**Manufacturer Name:** "
                            f"{drug_data[3]}"
                        )


                        st.write(
                            f"**Quantity:** "
                            f"{drug_data[4]}"
                        )


                    with detail_col2:

                        st.write(
                            f"**Manufacturing Timestamp:** "
                            f"{drug_data[5]}"
                        )


                        st.write(
                            f"**Expiry Timestamp:** "
                            f"{drug_data[6]}"
                        )


                        st.write(
                            f"**Shipping Timestamp:** "
                            f"{drug_data[7]}"
                        )


                        st.write(
                            f"**Receiving Timestamp:** "
                            f"{drug_data[8]}"
                        )


                        st.write(
                            f"**Current Owner:** "
                            f"{drug_data[10]}"
                        )


                    # =========================================
                    # STATUS
                    # =========================================

                    st.divider()

                    st.subheader(
                        "📦 Drug Status"
                    )


                    status_value = drug_data[11]


                    status_names = {

                        0: "MANUFACTURED",

                        1: "SHIPPED",

                        2: "RECEIVED",

                        3: "DISPENSED"
                    }


                    status_text = status_names.get(

                        status_value,

                        str(status_value)
                    )


                    st.success(
                        f"Current Status: {status_text}"
                    )


                    # =========================================
                    # CONTRACT INFORMATION
                    # =========================================

                    st.divider()

                    st.subheader(
                        "🔗 Smart Contract"
                    )


                    st.write(
                        "**Contract Address:**"
                    )

                    st.code(
                        CONTRACT_ADDRESS
                    )


                else:

                    st.error(
                        "❌ Drug not found on blockchain."
                    )


                    if exists_in_database:

                        st.warning(
                            "⚠️ The drug exists in the "
                            "local database but was not "
                            "found on the blockchain."
                        )


            except Exception as e:

                st.error(
                    "❌ Verification failed."
                )

                st.exception(e)