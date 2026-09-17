# PharmaChain — Blockchain Drug Tracking

A Streamlit + Web3.py + SQLite application for tracking drugs with the `DrugTracking.sol` smart contract.

## Network

The deployment target is **Ethereum Sepolia**:

- Chain ID: `11155111`
- RPC pattern: `https://eth-sepolia.g.alchemy.com/v2/<API_KEY>`
- Explorer: https://sepolia.etherscan.io

## Project structure

```text
Tracking-Drugs-Using-Blockchain/
├── contracts/
│   └── DrugTracking.sol
├── scripts/
│   └── deploy_contract.py
├── ui/
│   ├── app.py
│   ├── blockchain.py
│   ├── database.py
│   ├── DrugTracking.json
│   └── requirements.txt
├── hardhat.config.ts
├── package.json
├── package-lock.json
├── tsconfig.json
├── .env.example
└── .gitignore
```

## 1. Install dependencies

From the repository root:

```powershell
npm install
pip install -r ui/requirements.txt
```

Use Python 3.12 locally to match the Streamlit Community Cloud default.

## 2. Create `.env`

Copy `.env.example` to `.env` and fill in your own values:

```env
SEPOLIA_RPC_URL=https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY
PRIVATE_KEY=YOUR_TEST_WALLET_PRIVATE_KEY
CONTRACT_ADDRESS=YOUR_SEPOLIA_CONTRACT_ADDRESS
```

Use a dedicated test wallet. Never commit `.env` or share the private key.

## 3. Compile the contract

```powershell
npx hardhat compile
```

## 4. Deploy `DrugTracking.sol` to Sepolia

After compilation:

```powershell
python scripts/deploy_contract.py
```

The script checks that the RPC is actually connected to chain ID `11155111`, deploys the contract, and prints the new contract address.

Copy that address into `.env` as `CONTRACT_ADDRESS`.

## 5. Run the Streamlit app locally

```powershell
streamlit run ui/app.py
```

The app has:

- Register Drug
- Verify Drug
- Drug Lifecycle
  - Ship to Distributor
  - Receive
  - Ship to Hospital
  - Dispense

The QR code contains the Drug ID and can be used to identify the blockchain record.

## 6. Streamlit Community Cloud

Push the repository to GitHub. In Streamlit Community Cloud select:

- Repository: your GitHub repository
- Branch: `master` (or your actual branch)
- Main file: `ui/app.py`
- Python: 3.12

In **Advanced settings → Secrets**, add:

```toml
RPC_URL = "https://eth-sepolia.g.alchemy.com/v2/YOUR_API_KEY"
PRIVATE_KEY = "YOUR_TEST_WALLET_PRIVATE_KEY"
CONTRACT_ADDRESS = "YOUR_SEPOLIA_CONTRACT_ADDRESS"
```

Do not commit these secrets to GitHub.

## Important SQLite note

SQLite is included for MVP/local application records. Streamlit Community Cloud does not guarantee permanent local filesystem storage, so a production deployment should move application data to a persistent database such as PostgreSQL.

The blockchain record remains on Sepolia.
