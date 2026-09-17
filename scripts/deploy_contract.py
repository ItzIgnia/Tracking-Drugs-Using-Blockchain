import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL = os.getenv("SEPOLIA_RPC_URL") or os.getenv("RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

if not RPC_URL:
    raise SystemExit("SEPOLIA_RPC_URL is missing from .env")
if not PRIVATE_KEY:
    raise SystemExit("PRIVATE_KEY is missing from .env")

ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "artifacts" / "contracts" / "DrugTracking.sol" / "DrugTracking.json"

if not ARTIFACT.exists():
    raise SystemExit(
        "Hardhat artifact not found. Run `npx hardhat compile` first."
    )

with ARTIFACT.open("r", encoding="utf-8") as f:
    artifact = json.load(f)

w3 = Web3(Web3.HTTPProvider(RPC_URL, request_kwargs={"timeout": 30}))
if not w3.is_connected():
    raise SystemExit("Could not connect to the Sepolia RPC.")

if w3.eth.chain_id != 11155111:
    raise SystemExit(
        f"Wrong network. Expected Sepolia chain ID 11155111, got {w3.eth.chain_id}."
    )

account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Deploying from: {account.address}")
print(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} SepoliaETH")

contract = w3.eth.contract(
    abi=artifact["abi"],
    bytecode=artifact["bytecode"],
)

nonce = w3.eth.get_transaction_count(account.address, "pending")

transaction = contract.constructor().build_transaction({
    "from": account.address,
    "nonce": nonce,
    "chainId": 11155111,
})

transaction["gas"] = int(w3.eth.estimate_gas(transaction) * 1.15)
latest = w3.eth.get_block("latest")
base_fee = latest.get("baseFeePerGas")

if base_fee is not None:
    priority_fee = w3.to_wei(1, "gwei")
    transaction["maxPriorityFeePerGas"] = priority_fee
    transaction["maxFeePerGas"] = int(base_fee * 2 + priority_fee)
else:
    transaction["gasPrice"] = w3.eth.gas_price

signed = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
print(f"Deployment transaction: {tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)

if receipt["status"] != 1:
    raise SystemExit("Contract deployment transaction failed.")

address = receipt["contractAddress"]
print("\nSUCCESS")
print(f"Contract address: {address}")
print(f"Block number: {receipt['blockNumber']}")
print(f"Sepolia Etherscan: https://sepolia.etherscan.io/address/{address}")
print("\nPut this address in Streamlit Secrets as:")
print(f"CONTRACT_ADDRESS = \"{address}\"")
