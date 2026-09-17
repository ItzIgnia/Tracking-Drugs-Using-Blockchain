import "dotenv/config";
import { defineConfig } from "hardhat/config";

const SEPOLIA_RPC_URL = process.env.SEPOLIA_RPC_URL || "";
const PRIVATE_KEY = process.env.PRIVATE_KEY || "";

export default defineConfig({
  solidity: {
    version: "0.8.34",
  },
  networks: {
    sepolia: {
      type: "http",
      url: SEPOLIA_RPC_URL,
      accounts: PRIVATE_KEY ? [PRIVATE_KEY] : [],
      chainId: 11155111,
    },
  },
});
