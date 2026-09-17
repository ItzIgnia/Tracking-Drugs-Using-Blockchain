import os
import json
from pathlib import Path

import streamlit as st
from web3 import Web3
from dotenv import load_dotenv


# ============================================================
# LOAD LOCAL ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()


# ============================================================
# CONFIGURATION HELPER
# ============================================================

def get_config(key):
    """
    Get configuration from Streamlit Secrets first.
    If not available, use environment variables.

    This allows the same code to work:
    - Locally using .env
    - On Streamlit Cloud using Secrets
    """

    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return os.getenv(key)


# ============================================================
# BLOCKCHAIN CONFIGURATION
# ============================================================

RPC_URL = get_config("RPC_URL")
PRIVATE_KEY = get_config("PRIVATE_KEY")
CONTRACT_ADDRESS_VALUE = get_config("CONTRACT_ADDRESS")


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not RPC_URL:
    raise RuntimeError(
        "RPC_URL is not configured. "
        "Add it to .env locally or Streamlit Secrets."
    )

if not PRIVATE_KEY:
    raise RuntimeError(
        "PRIVATE_KEY is not configured. "
        "Add it to .env locally or Streamlit Secrets."
    )

if not CONTRACT_ADDRESS_VALUE:
    raise RuntimeError(
        "CONTRACT_ADDRESS is not configured. "
        "Add it to .env locally or Streamlit Secrets."
    )


# ============================================================
# WEB3 CONNECTION
# ============================================================

web3 = Web3(
    Web3.HTTPProvider(RPC_URL)
)


# ============================================================
# BLOCKCHAIN CONNECTION CHECK
# ============================================================

def blockchain_connected():
    """
    Returns True if Web3 is connected to the blockchain.
    """

    try:
        return web3.is_connected()

    except Exception:
        return False


# ============================================================
# CONTRACT ADDRESS
# ============================================================

CONTRACT_ADDRESS = Web3.to_checksum_address(
    CONTRACT_ADDRESS_VALUE
)


# ============================================================
# LOAD CONTRACT ABI
# ============================================================

ABI_PATH = Path(__file__).parent / "DrugTracking.json"


if not ABI_PATH.exists():

    raise FileNotFoundError(
        f"DrugTracking.json was not found at:\n{ABI_PATH}"
    )


with open(
    ABI_PATH,
    "r",
    encoding="utf-8"
) as file:

    contract_file = json.load(file)


# Hardhat artifact contains:
# {
#     "abi": [...],
#     "bytecode": "...",
#     ...
# }

if isinstance(contract_file, dict) and "abi" in contract_file:

    CONTRACT_ABI = contract_file["abi"]

else:

    # Also supports a JSON file containing only the ABI
    CONTRACT_ABI = contract_file


# ============================================================
# SMART CONTRACT INSTANCE
# ============================================================

contract = web3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=CONTRACT_ABI
)


# ============================================================
# WALLET
# ============================================================

account = web3.eth.account.from_key(
    PRIVATE_KEY
)

ACCOUNT_ADDRESS = account.address


# ============================================================
# SEND BLOCKCHAIN TRANSACTION
# ============================================================

def send_transaction(function_call):
    """
    Build, sign and send a blockchain transaction.

    Returns the transaction receipt.
    """

    # Get current nonce
    nonce = web3.eth.get_transaction_count(
        ACCOUNT_ADDRESS,
        "pending"
    )

    # Base transaction
    transaction = function_call.build_transaction({

        "from": ACCOUNT_ADDRESS,

        "nonce": nonce,

        "chainId": web3.eth.chain_id,
    })


    # Estimate gas
    transaction["gas"] = web3.eth.estimate_gas(
        transaction
    )


    # ========================================================
    # EIP-1559 GAS SETTINGS
    # ========================================================

    latest_block = web3.eth.get_block(
        "latest"
    )

    if latest_block.get("baseFeePerGas") is not None:

        priority_fee = web3.to_wei(
            1,
            "gwei"
        )

        transaction[
            "maxPriorityFeePerGas"
        ] = priority_fee

        transaction[
            "maxFeePerGas"
        ] = (
            latest_block["baseFeePerGas"] * 2
            + priority_fee
        )

    else:

        transaction[
            "gasPrice"
        ] = web3.eth.gas_price


    # ========================================================
    # SIGN TRANSACTION
    # ========================================================

    signed_transaction = web3.eth.account.sign_transaction(
        transaction,
        PRIVATE_KEY
    )


    # ========================================================
    # SEND TRANSACTION
    # ========================================================

    tx_hash = web3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )


    # ========================================================
    # WAIT FOR CONFIRMATION
    # ========================================================

    receipt = web3.eth.wait_for_transaction_receipt(
        tx_hash
    )


    return receipt


# ============================================================
# CHECK WHETHER DRUG EXISTS ON BLOCKCHAIN
# ============================================================

def blockchain_drug_exists(drug_id):

    try:

        return contract.functions.drugExists(
            drug_id
        ).call()

    except Exception:

        return False


# ============================================================
# MANUFACTURE / REGISTER DRUG
# ============================================================

def manufacture_drug(
    drug_id,
    batch_id,
    drug_name,
    manufacturer_name,
    quantity,
    manufacturing_date,
    expiry_date
):
    """
    Register a new drug on the blockchain.

    Dates are converted to Unix timestamps because
    the Solidity contract uses uint256 timestamps.
    """

    # Convert date strings to timestamps
    from datetime import datetime

    manufacturing_timestamp = int(
        datetime.strptime(
            manufacturing_date,
            "%Y-%m-%d"
        ).timestamp()
    )

    expiry_timestamp = int(
        datetime.strptime(
            expiry_date,
            "%Y-%m-%d"
        ).timestamp()
    )


    # ========================================================
    # SMART CONTRACT FUNCTION
    # ========================================================

    function_call = contract.functions.manufactureDrug(

        drug_id,

        batch_id,

        drug_name,

        manufacturer_name,

        int(quantity),

        manufacturing_timestamp,

        expiry_timestamp
    )


    # ========================================================
    # SEND TRANSACTION
    # ========================================================

    receipt = send_transaction(
        function_call
    )


    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "receipt": receipt,

        "sender": ACCOUNT_ADDRESS,

        "transaction_hash":
            receipt["transactionHash"].hex(),

        "block_number":
            receipt["blockNumber"]
    }


# ============================================================
# GET DRUG FROM BLOCKCHAIN
# ============================================================

def get_drug(drug_id):

    return contract.functions.getDrug(
        drug_id
    ).call()
