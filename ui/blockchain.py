import json
import os
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

SEPOLIA_CHAIN_ID = 11155111


def get_config(key: str):
    """Read Streamlit Secrets first, then local environment variables."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.getenv(key)


RPC_URL = get_config("RPC_URL") or get_config("SEPOLIA_RPC_URL")
PRIVATE_KEY = get_config("PRIVATE_KEY")
CONTRACT_ADDRESS_VALUE = get_config("CONTRACT_ADDRESS")

CONFIG_ERROR = None

if not RPC_URL:
    CONFIG_ERROR = "RPC_URL is not configured. Add it to .env locally or Streamlit Cloud Secrets."
elif not PRIVATE_KEY:
    CONFIG_ERROR = "PRIVATE_KEY is not configured. Add it to .env locally or Streamlit Cloud Secrets."
elif not CONTRACT_ADDRESS_VALUE:
    CONFIG_ERROR = "CONTRACT_ADDRESS is not configured. Deploy the contract first, then add its address to .env/Secrets."

web3 = None
contract = None
account = None
ACCOUNT_ADDRESS = ""
CONTRACT_ADDRESS = ""

if CONFIG_ERROR is None:
    try:
        web3 = Web3(
            Web3.HTTPProvider(
                RPC_URL,
                request_kwargs={"timeout": 30},
            )
        )

        CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS_VALUE)

        ABI_PATH = Path(__file__).resolve().parent / "DrugTracking.json"
        if not ABI_PATH.exists():
            raise RuntimeError(f"Contract ABI not found: {ABI_PATH}")

        with ABI_PATH.open("r", encoding="utf-8") as file:
            artifact = json.load(file)

        CONTRACT_ABI = (
            artifact["abi"]
            if isinstance(artifact, dict) and "abi" in artifact
            else artifact
        )

        contract = web3.eth.contract(
            address=CONTRACT_ADDRESS,
            abi=CONTRACT_ABI,
        )

        account = web3.eth.account.from_key(PRIVATE_KEY)
        ACCOUNT_ADDRESS = account.address

        if web3.is_connected():
            actual_chain_id = web3.eth.chain_id
            if actual_chain_id != SEPOLIA_CHAIN_ID:
                CONFIG_ERROR = (
                    f"Wrong blockchain network. Expected Ethereum Sepolia "
                    f"(chain ID {SEPOLIA_CHAIN_ID}), but connected to chain ID {actual_chain_id}."
                )

    except Exception as exc:
        CONFIG_ERROR = str(exc)


def blockchain_ready() -> bool:
    return CONFIG_ERROR is None and web3 is not None and contract is not None


def blockchain_connected() -> bool:
    if not blockchain_ready():
        return False
    try:
        return web3.is_connected() and web3.eth.chain_id == SEPOLIA_CHAIN_ID
    except Exception:
        return False


def require_blockchain():
    if not blockchain_ready():
        raise RuntimeError(CONFIG_ERROR or "Blockchain is not configured.")
    if not blockchain_connected():
        raise RuntimeError("Could not connect to Ethereum Sepolia.")


def wallet_balance_eth() -> float:
    require_blockchain()
    balance = web3.eth.get_balance(ACCOUNT_ADDRESS)
    return float(web3.from_wei(balance, "ether"))


def send_transaction(function_call):
    """Build, sign, send and wait for a contract transaction."""
    require_blockchain()

    nonce = web3.eth.get_transaction_count(ACCOUNT_ADDRESS, "pending")

    transaction = function_call.build_transaction(
        {
            "from": ACCOUNT_ADDRESS,
            "nonce": nonce,
            "chainId": SEPOLIA_CHAIN_ID,
        }
    )

    transaction["gas"] = int(web3.eth.estimate_gas(transaction) * 1.15)

    latest_block = web3.eth.get_block("latest")
    base_fee = latest_block.get("baseFeePerGas")

    if base_fee is not None:
        priority_fee = web3.to_wei(1, "gwei")
        transaction["maxPriorityFeePerGas"] = priority_fee
        transaction["maxFeePerGas"] = int(base_fee * 2 + priority_fee)
    else:
        transaction["gasPrice"] = web3.eth.gas_price

    signed = web3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    if receipt["status"] != 1:
        raise RuntimeError(f"Blockchain transaction failed: {tx_hash.hex()}")

    return receipt


def blockchain_drug_exists(drug_id: str) -> bool:
    require_blockchain()
    return bool(contract.functions.drugExists(drug_id).call())


def _date_to_timestamp(date_string: str) -> int:
    dt = datetime.strptime(date_string, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def manufacture_drug(
    drug_id,
    batch_id,
    drug_name,
    manufacturer_name,
    quantity,
    manufacturing_date,
    expiry_date,
):
    require_blockchain()

    function_call = contract.functions.manufactureDrug(
        drug_id,
        batch_id,
        drug_name,
        manufacturer_name,
        int(quantity),
        _date_to_timestamp(manufacturing_date),
        _date_to_timestamp(expiry_date),
    )

    receipt = send_transaction(function_call)

    return {
        "receipt": receipt,
        "sender": ACCOUNT_ADDRESS,
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
    }


def ship_drug(drug_id: str, distributor_address: str):
    require_blockchain()
    distributor_address = Web3.to_checksum_address(distributor_address)
    receipt = send_transaction(
        contract.functions.shipDrug(drug_id, distributor_address)
    )
    return {
        "receipt": receipt,
        "sender": ACCOUNT_ADDRESS,
        "receiver": distributor_address,
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
    }


def receive_drug(drug_id: str):
    require_blockchain()
    receipt = send_transaction(contract.functions.receiveDrug(drug_id))
    return {
        "receipt": receipt,
        "sender": ACCOUNT_ADDRESS,
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
    }


def ship_to_hospital(drug_id: str, hospital_address: str):
    require_blockchain()
    hospital_address = Web3.to_checksum_address(hospital_address)
    receipt = send_transaction(
        contract.functions.shipToHospital(drug_id, hospital_address)
    )
    return {
        "receipt": receipt,
        "sender": ACCOUNT_ADDRESS,
        "receiver": hospital_address,
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
    }


def dispense_drug(drug_id: str):
    require_blockchain()
    receipt = send_transaction(contract.functions.dispenseDrug(drug_id))
    return {
        "receipt": receipt,
        "sender": ACCOUNT_ADDRESS,
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
    }


def get_drug(drug_id: str):
    require_blockchain()
    return contract.functions.getDrug(drug_id).call()
