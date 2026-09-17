import os
import json
from pathlib import Path

import streamlit as st
from web3 import Web3
from dotenv import load_dotenv


# ============================================================
# LOAD LOCAL .ENV
# ============================================================

load_dotenv()


# ============================================================
# HELPER: GET CONFIGURATION
# ============================================================

def get_config(key):
    """
    Get configuration from Streamlit Secrets first.
    If not available, use environment variables.
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
CONTRACT_ADDRESS = get_config("CONTRACT_ADDRESS")


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not RPC_URL:
    raise RuntimeError("RPC_URL is not configured.")

if not PRIVATE_KEY:
    raise RuntimeError("PRIVATE_KEY is not configured.")

if not CONTRACT_ADDRESS:
    raise RuntimeError("CONTRACT_ADDRESS is not configured.")


# ============================================================
# WEB3 CONNECTION
# ============================================================

web3 = Web3(Web3.HTTPProvider(RPC_URL))


def blockchain_connected():
    """
    Check whether Web3 can connect to the blockchain.
    """
    try:
        return web3.is_connected()
    except Exception:
        return False


# ============================================================
# CONTRACT ADDRESS
# ============================================================

CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS)


# ============================================================
# LOAD ABI
# ============================================================

ABI_PATH = Path(__file__).parent / "DrugTracking.json"

if not ABI_PATH.exists():
    raise FileNotFoundError(
        f"Contract ABI not found: {ABI_PATH}"
    )


with open(ABI_PATH, "r", encoding="utf-8") as file:
    artifact = json.load(file)


# The file may either be a Hardhat artifact
# containing "abi", or an ABI-only JSON file.

if isinstance(artifact, dict) and "abi" in artifact:
    CONTRACT_ABI = artifact["abi"]
else:
    CONTRACT_ABI = artifact


# ============================================================
# CONTRACT INSTANCE
# ============================================================

contract = web3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=CONTRACT_ABI
)


# ============================================================
# WALLET
# ============================================================

account = web3.eth.account.from_key(PRIVATE_KEY)

ACCOUNT_ADDRESS = account.address


# ============================================================
# TRANSACTION HELPER
# ============================================================

def send_transaction(function_call):
    """
    Sign and send a blockchain transaction.
    """

    nonce = web3.eth.get_transaction_count(
        ACCOUNT_ADDRESS,
        "pending"
    )

    transaction = function_call.build_transaction({
        "from": ACCOUNT_ADDRESS,
        "nonce": nonce,
        "chainId": web3.eth.chain_id,
    })

    # Estimate gas
    transaction["gas"] = web3.eth.estimate_gas(transaction)

    # Ethereum Sepolia uses EIP-1559.
    latest_block = web3.eth.get_block("latest")

    if latest_block.get("baseFeePerGas") is not None:

        priority_fee = web3.to_wei(1, "gwei")

        transaction["maxPriorityFeePerGas"] = priority_fee

        transaction["maxFeePerGas"] = (
            latest_block["baseFeePerGas"] * 2
            + priority_fee
        )

    else:
        transaction["gasPrice"] = web3.eth.gas_price

    # Sign
    signed_transaction = web3.eth.account.sign_transaction(
        transaction,
        PRIVATE_KEY
    )

    # Send
    tx_hash = web3.eth.send_raw_transaction(
        signed_transaction.raw_transaction
    )

    # Wait
    receipt = web3.eth.wait_for_transaction_receipt(
        tx_hash
    )

    return receipt


# ============================================================
# CHECK DRUG EXISTS
# ============================================================

def blockchain_drug_exists(drug_id):

    try:
        return contract.functions.drugExists(
            drug_id
        ).call()

    except Exception:
        return False


# ============================================================
# MANUFACTURE DRUG
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

    function_call = contract.functions.manufactureDrug(
        drug_id,
        batch_id,
        drug_name,
        manufacturer_name,
        quantity,
        manufacturing_date,
        expiry_date
    )

    receipt = send_transaction(function_call)

    return {
        "receipt": receipt,
        "sender": ACCOUNT_ADDRESS,
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"]
    }


# ============================================================
# GET DRUG
# ============================================================

def get_drug(drug_id):

    return contract.functions.getDrug(
        drug_id
    ).call()
