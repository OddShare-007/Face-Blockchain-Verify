"""Compile and deploy Verifier.sol to the configured Ethereum network."""

import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv
from solcx import compile_source, get_installed_solc_versions, install_solc, set_solc_version
from web3 import Web3


SOLC_VERSION = "0.8.20"
PROJECT_ROOT = Path(__file__).resolve().parent
CONTRACT_PATH = PROJECT_ROOT / "contracts" / "Verifier.sol"
OUTPUT_PATH = PROJECT_ROOT / "output" / "deployment.json"


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")

    rpc_url = os.getenv("SEPOLIA_RPC_URL", "").strip()
    private_key = os.getenv("PRIVATE_KEY", "").strip()
    if not rpc_url:
        raise ValueError("SEPOLIA_RPC_URL is missing from .env")
    if not private_key or private_key == "your_wallet_private_key_without_0x_prefix":
        raise ValueError("PRIVATE_KEY is missing from .env; set a Sepolia test wallet key")

    private_key = private_key.removeprefix("0x")
    if not re.fullmatch(r"[0-9a-fA-F]{64}", private_key):
        raise ValueError("PRIVATE_KEY must be a 64-character hexadecimal key")
    if not CONTRACT_PATH.is_file():
        raise FileNotFoundError(f"Contract source not found: {CONTRACT_PATH}")

    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        raise ConnectionError("Could not connect to SEPOLIA_RPC_URL")

    account = web3.eth.account.from_key(private_key)
    print(f"Deploying from: {account.address}")
    print(f"Network chain ID: {web3.eth.chain_id}")

    if SOLC_VERSION not in {str(version) for version in get_installed_solc_versions()}:
        try:
            install_solc(SOLC_VERSION)
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                "Could not download Solidity compiler from solc-bin.ethereum.org. "
                "Check DNS/internet access, or deploy contracts/Verifier.sol with Remix."
            ) from e
    set_solc_version(SOLC_VERSION)
    source = CONTRACT_PATH.read_text(encoding="utf-8")
    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
    )
    _, contract_interface = compiled.popitem()
    contract = web3.eth.contract(
        abi=contract_interface["abi"],
        bytecode=contract_interface["bin"],
    )

    nonce = web3.eth.get_transaction_count(account.address)
    transaction = contract.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": web3.eth.chain_id,
            "gasPrice": web3.eth.gas_price,
        }
    )
    transaction["gas"] = web3.eth.estimate_gas(transaction)
    signed = web3.eth.account.sign_transaction(transaction, private_key)
    transaction_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Transaction: {transaction_hash.hex()}")
    receipt = web3.eth.wait_for_transaction_receipt(transaction_hash, timeout=120)

    result = {
        "contract_address": receipt["contractAddress"],
        "deployer_address": account.address,
        "transaction_hash": transaction_hash.hex(),
        "chain_id": web3.eth.chain_id,
        "etherscan_link": f"https://sepolia.etherscan.io/address/{receipt['contractAddress']}",
    }
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Contract: {receipt['contractAddress']}")
    print(f"Saved deployment details to: {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")
    print("Set VERIFIER_CONTRACT_ADDRESS in .env to the contract address above.")


if __name__ == "__main__":
    main()