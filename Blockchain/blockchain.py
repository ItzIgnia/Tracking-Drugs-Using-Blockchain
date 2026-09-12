# ============================================================
# PHARMACHAIN - BLOCKCHAIN BACKEND
# ============================================================

import json

from pathlib import Path

from datetime import (
    date,
    datetime
)

from web3 import Web3


# ============================================================
# BLOCKCHAIN CONNECTION
# ============================================================

RPC_URL = (
    "http://127.0.0.1:8545"
)

w3 = Web3(
    Web3.HTTPProvider(
        RPC_URL
    )
)


# ============================================================
# PROJECT PATHS
# ============================================================

BLOCKCHAIN_FOLDER = (
    Path(__file__).resolve().parent
)

PROJECT_ROOT = (
    BLOCKCHAIN_FOLDER.parent
)


ARTIFACT_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "contracts"
    / "DrugTracking.sol"
    / "DrugTracking.json"
)


ADDRESS_FILE = (
    BLOCKCHAIN_FOLDER
    / "contract_address.txt"
)


# ============================================================
# BLOCKCHAIN CONNECTION CHECK
# ============================================================

def blockchain_connected():

    return w3.is_connected()


if not blockchain_connected():

    raise Exception(
        "Cannot connect to Hardhat.\n"
        "Make sure 'npx hardhat node' is running."
    )


# ============================================================
# LOAD CONTRACT ARTIFACT
# ============================================================

if not ARTIFACT_PATH.exists():

    raise FileNotFoundError(
        f"Contract artifact not found:\n"
        f"{ARTIFACT_PATH}\n\n"
        "Run 'npx hardhat compile' first."
    )


with open(
    ARTIFACT_PATH,
    "r"
) as file:

    artifact = json.load(
        file
    )


ABI = artifact["abi"]


# ============================================================
# LOAD CONTRACT ADDRESS
# ============================================================

if not ADDRESS_FILE.exists():

    raise FileNotFoundError(
        f"Contract address file not found:\n"
        f"{ADDRESS_FILE}\n\n"
        "Deploy the smart contract first."
    )


with open(
    ADDRESS_FILE,
    "r"
) as file:

    CONTRACT_ADDRESS = (
        file.read().strip()
    )


if not CONTRACT_ADDRESS:

    raise Exception(
        "Contract address file is empty."
    )


CONTRACT_ADDRESS = (
    Web3.to_checksum_address(
        CONTRACT_ADDRESS
    )
)


# ============================================================
# CONTRACT INSTANCE
# ============================================================

contract = w3.eth.contract(
    address=CONTRACT_ADDRESS,
    abi=ABI
)


# ============================================================
# HARDHAT ACCOUNTS
# ============================================================

accounts = w3.eth.accounts


if len(accounts) < 3:

    raise Exception(
        "At least 3 Hardhat accounts are required."
    )


manufacturer = accounts[0]

distributor = accounts[1]

hospital = accounts[2]


# ============================================================
# STATUS
# ============================================================

STATUS_NAMES = {

    0: "MANUFACTURED",

    1: "SHIPPED",

    2: "RECEIVED",

    3: "DISPENSED"
}


def get_status_name(status):

    return STATUS_NAMES.get(
        int(status),
        "UNKNOWN"
    )


# ============================================================
# DATE → UNIX TIMESTAMP
# ============================================================

def convert_to_timestamp(value):

    # datetime
    if isinstance(
        value,
        datetime
    ):

        return int(
            value.timestamp()
        )

    # date
    if isinstance(
        value,
        date
    ):

        dt = datetime.combine(
            value,
            datetime.min.time()
        )

        return int(
            dt.timestamp()
        )

    # already timestamp
    return int(value)


# ============================================================
# CHECK DRUG
# ============================================================

def blockchain_drug_exists(
    drug_id
):

    return contract.functions.drugExists(
        drug_id
    ).call()


# ============================================================
# GET DRUG
# ============================================================

def get_drug(
    drug_id
):

    return contract.functions.getDrug(
        drug_id
    ).call()


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

    manufacturing_timestamp = (
        convert_to_timestamp(
            manufacturing_date
        )
    )

    expiry_timestamp = (
        convert_to_timestamp(
            expiry_date
        )
    )

    transaction = (
        contract.functions.manufactureDrug(

            drug_id,

            batch_id,

            drug_name,

            manufacturer_name,

            int(quantity),

            manufacturing_timestamp,

            expiry_timestamp

        ).transact({

            "from": manufacturer

        })
    )

    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction
        )
    )

    return {

        "action":
            "MANUFACTURE",

        "transaction_hash":
            receipt[
                "transactionHash"
            ].hex(),

        "block_number":
            receipt[
                "blockNumber"
            ],

        "sender":
            manufacturer,

        "receiver":
            manufacturer
    }


# ============================================================
# SHIP TO DISTRIBUTOR
# ============================================================

def ship_drug(
    drug_id,
    receiver_address=None,
    sender_address=None
):

    if receiver_address is None:

        receiver_address = distributor


    if sender_address is None:

        sender_address = manufacturer


    sender_address = (
        Web3.to_checksum_address(
            sender_address
        )
    )

    receiver_address = (
        Web3.to_checksum_address(
            receiver_address
        )
    )


    transaction = (
        contract.functions.shipDrug(

            drug_id,

            receiver_address

        ).transact({

            "from":
                sender_address

        })
    )


    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction
        )
    )


    return {

        "action":
            "SHIP_TO_DISTRIBUTOR",

        "transaction_hash":
            receipt[
                "transactionHash"
            ].hex(),

        "block_number":
            receipt[
                "blockNumber"
            ],

        "sender":
            sender_address,

        "receiver":
            receiver_address
    }


# ============================================================
# RECEIVE DRUG
# ============================================================

def receive_drug(
    drug_id,
    receiver_address
):

    receiver_address = (
        Web3.to_checksum_address(
            receiver_address
        )
    )


    transaction = (
        contract.functions.receiveDrug(

            drug_id

        ).transact({

            "from":
                receiver_address

        })
    )


    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction
        )
    )


    return {

        "action":
            "RECEIVE",

        "transaction_hash":
            receipt[
                "transactionHash"
            ].hex(),

        "block_number":
            receipt[
                "blockNumber"
            ],

        "sender":
            receiver_address,

        "receiver":
            receiver_address
    }


# ============================================================
# SHIP TO HOSPITAL
# ============================================================

def ship_to_hospital(
    drug_id,
    hospital_address=None,
    distributor_address=None
):

    if hospital_address is None:

        hospital_address = hospital


    if distributor_address is None:

        distributor_address = distributor


    hospital_address = (
        Web3.to_checksum_address(
            hospital_address
        )
    )


    distributor_address = (
        Web3.to_checksum_address(
            distributor_address
        )
    )


    transaction = (
        contract.functions.shipToHospital(

            drug_id,

            hospital_address

        ).transact({

            "from":
                distributor_address

        })
    )


    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction
        )
    )


    return {

        "action":
            "SHIP_TO_HOSPITAL",

        "transaction_hash":
            receipt[
                "transactionHash"
            ].hex(),

        "block_number":
            receipt[
                "blockNumber"
            ],

        "sender":
            distributor_address,

        "receiver":
            hospital_address
    }


# ============================================================
# HOSPITAL RECEIVE
# ============================================================

def hospital_receive_drug(
    drug_id,
    hospital_address=None
):

    if hospital_address is None:

        hospital_address = hospital


    hospital_address = (
        Web3.to_checksum_address(
            hospital_address
        )
    )


    transaction = (
        contract.functions.receiveDrug(

            drug_id

        ).transact({

            "from":
                hospital_address

        })
    )


    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction
        )
    )


    return {

        "action":
            "HOSPITAL_RECEIVE",

        "transaction_hash":
            receipt[
                "transactionHash"
            ].hex(),

        "block_number":
            receipt[
                "blockNumber"
            ],

        "sender":
            hospital_address,

        "receiver":
            hospital_address
    }


# ============================================================
# DISPENSE DRUG
# ============================================================

def dispense_drug(
    drug_id,
    hospital_address=None
):

    if hospital_address is None:

        hospital_address = hospital


    hospital_address = (
        Web3.to_checksum_address(
            hospital_address
        )
    )


    transaction = (
        contract.functions.dispenseDrug(

            drug_id

        ).transact({

            "from":
                hospital_address

        })
    )


    receipt = (
        w3.eth.wait_for_transaction_receipt(
            transaction
        )
    )


    return {

        "action":
            "DISPENSE_TO_PATIENT",

        "transaction_hash":
            receipt[
                "transactionHash"
            ].hex(),

        "block_number":
            receipt[
                "blockNumber"
            ],

        "sender":
            hospital_address,

        "receiver":
            "PATIENT"
    }


# ============================================================
# DISPLAY DRUG
# ============================================================

def display_drug(
    drug_id
):

    drug = get_drug(
        drug_id
    )

    print()

    print(
        "=" * 65
    )

    print(
        "                    DRUG RECORD"
    )

    print(
        "=" * 65
    )

    print(
        "Drug ID             :",
        drug[0]
    )

    print(
        "Batch ID            :",
        drug[1]
    )

    print(
        "Drug Name           :",
        drug[2]
    )

    print(
        "Manufacturer Name   :",
        drug[3]
    )

    print(
        "Quantity            :",
        drug[4]
    )

    print(
        "Manufacturing Date  :",
        datetime.fromtimestamp(
            drug[5]
        )
    )

    print(
        "Expiry Date         :",
        datetime.fromtimestamp(
            drug[6]
        )
    )

    if drug[7] != 0:

        print(
            "Shipping Date       :",
            datetime.fromtimestamp(
                drug[7]
            )
        )

    if drug[8] != 0:

        print(
            "Receiving Date      :",
            datetime.fromtimestamp(
                drug[8]
            )
        )

    print(
        "Manufacturer Wallet :",
        drug[9]
    )

    print(
        "Current Owner       :",
        drug[10]
    )

    print(
        "Status              :",
        get_status_name(
            drug[11]
        )
    )

    print(
        "Exists              :",
        drug[12]
    )

    print(
        "=" * 65
    )


# ============================================================
# STARTUP INFORMATION
# ============================================================

print(
    "=============================================="
)

print(
    "       PHARMACHAIN BLOCKCHAIN BACKEND"
)

print(
    "=============================================="
)

print(
    "Blockchain Connected :",
    blockchain_connected()
)

print(
    "Chain ID              :",
    w3.eth.chain_id
)

print(
    "Contract Address      :",
    CONTRACT_ADDRESS
)

print(
    "Manufacturer          :",
    manufacturer
)

print(
    "Distributor           :",
    distributor
)

print(
    "Hospital              :",
    hospital
)

print(
    "=============================================="
)