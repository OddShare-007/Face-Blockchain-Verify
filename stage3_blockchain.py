"""
Stage 3: Blockchain Verification
Writes the hash of the matched post to Ethereum Sepolia testnet.
Uses a deployed Verifier smart contract to store and emit records.
"""

import os
import json
import sys
import hashlib
from typing import Optional, Dict
from datetime import datetime

try:
    from web3 import Web3
except ImportError:
    print("ERROR: web3 not installed. Run: pip install web3")
    sys.exit(1)


# Verifier.sol contract ABI (minimal for storeRecord and reading events)
VERIFIER_ABI = [
    {
        "type": "event",
        "name": "RecordStored",
        "inputs": [
            {"name": "sender", "type": "address", "indexed": True},
            {"name": "hash", "type": "string", "indexed": False},
            {"name": "timestamp", "type": "uint256", "indexed": False}
        ]
    },
    {
        "type": "function",
        "name": "storeRecord",
        "inputs": [{"name": "hash", "type": "string"}],
        "outputs": [],
        "stateMutability": "nonpayable"
    },
    {
        "type": "function",
        "name": "getLatestRecord",
        "inputs": [],
        "outputs": [
            {"name": "", "type": "address"},
            {"name": "", "type": "string"},
            {"name": "", "type": "uint256"}
        ],
        "stateMutability": "view"
    }
]


def compute_data_hash(matched_post_data: dict) -> str:
    """
    Computes SHA-256 hash of matched post data.
    Combines image URL + title + source into a single string before hashing.
    
    Args:
        matched_post_data: Dictionary containing url, title, source
        
    Returns:
        str: SHA-256 hash in hex format
    """
    # Combine the three key pieces of data
    combined = f"{matched_post_data.get('url', '')}{matched_post_data.get('title', '')}{matched_post_data.get('source', '')}"
    
    # Compute SHA-256 hash
    hash_object = hashlib.sha256(combined.encode())
    return hash_object.hexdigest()


def write_to_blockchain(matched_post_json_path: str, contract_address: str, output_dir: str = "output") -> Optional[Dict]:
    """
    Writes the hash of matched post data to Ethereum Sepolia testnet.
    
    Args:
        matched_post_json_path: Path to the matched_post.json file
        contract_address: Address of deployed Verifier contract
        output_dir: Directory to save transaction details
        
    Returns:
        dict: Contains transaction hash, block number, etc.
        
    Raises:
        FileNotFoundError: If matched post file not found
        Exception: If blockchain write fails
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Validate input file
    if not os.path.isfile(matched_post_json_path):
        raise FileNotFoundError(f"Matched post file not found: {matched_post_json_path}")
    
    print(f"[Stage 3] Writing to Ethereum Sepolia testnet")
    
    # Load matched post data
    try:
        with open(matched_post_json_path, "r") as f:
            matched_post_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse matched post JSON: {e}")
    
    # Check if we have data to hash
    if not matched_post_data or "url" not in matched_post_data:
        print("  ⚠ No matched post data available, using empty hash")
        data_hash = hashlib.sha256(b"").hexdigest()
    else:
        # Compute hash of the matched post
        data_hash = compute_data_hash(matched_post_data)
        print(f"  → Computed hash of matched post: {data_hash}")
    
    # Get environment variables
    rpc_url = os.getenv("SEPOLIA_RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    
    if not rpc_url:
        raise ValueError(
            "SEPOLIA_RPC_URL environment variable not set. "
            "Set it to an Ethereum Sepolia RPC endpoint (e.g., from Alchemy or Infura)"
        )
    
    if not private_key:
        raise ValueError(
            "PRIVATE_KEY environment variable not set. "
            "Set it to your Ethereum wallet private key (without 0x prefix)"
        )
    
    # Clean up private key (remove 0x prefix if present)
    if private_key.startswith("0x"):
        private_key = private_key[2:]
    
    try:
        # Connect to Sepolia testnet
        print(f"  → Connecting to Sepolia RPC: {rpc_url[:50]}...")
        web3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not web3.is_connected():
            raise ConnectionError("Failed to connect to Sepolia RPC endpoint")
        
        # Get account from private key
        account = web3.eth.account.from_key(private_key)
        print(f"  → Using account: {account.address}")
        
        # Validate contract address
        contract_address = Web3.to_checksum_address(contract_address)
        print(f"  → Target contract: {contract_address}")
        
        # Create contract instance
        contract = web3.eth.contract(
            address=contract_address,
            abi=VERIFIER_ABI
        )
        
        # Build transaction to call storeRecord
        print(f"  → Building transaction...")
        transaction = contract.functions.storeRecord(data_hash).build_transaction({
            "from": account.address,
            "nonce": web3.eth.get_transaction_count(account.address),
            "gas": 100000,  # Estimate for storeRecord
            "gasPrice": web3.eth.gas_price,
        })
        
        # Sign transaction
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        
        # Send transaction
        print(f"  → Sending transaction...")
        tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_hash_hex = tx_hash.hex()
        
        print(f"  ✓ Transaction sent: {tx_hash_hex}")
        print(f"  → Waiting for confirmation...")
        
        # Wait for transaction receipt (up to 60 seconds)
        try:
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
        except Exception as e:
            print(f"  ⚠ Timeout waiting for receipt (transaction may still be pending): {e}")
            receipt = None
        
        # Prepare result
        result = {
            "transaction_hash": tx_hash_hex,
            "contract_address": contract_address,
            "data_hash": data_hash,
            "timestamp": datetime.now().isoformat(),
            "matched_post_url": matched_post_data.get("url", ""),
            "matched_post_title": matched_post_data.get("title", ""),
            "etherscan_link": f"https://sepolia.etherscan.io/tx/{tx_hash_hex}"
        }
        
        if receipt:
            result["block_number"] = receipt["blockNumber"]
            result["gas_used"] = receipt["gasUsed"]
            result["status"] = "confirmed" if receipt["status"] == 1 else "failed"
            print(f"  ✓ Transaction confirmed in block {receipt['blockNumber']}")
        else:
            result["status"] = "pending"
            print(f"  ⚠ Transaction pending (may take a few minutes)")
        
        # Save transaction details to output file
        output_file = os.path.join(output_dir, "transaction_record.json")
        with open(output_file, "w") as f:
            json.dump(result, f, indent=2)
        
        print(f"  ✓ Transaction details saved to: {output_file}")
        print(f"  ✓ View on Etherscan: {result['etherscan_link']}")
        
        return result
    
    except ConnectionError as e:
        print(f"ERROR: Failed to connect to blockchain: {e}")
        raise
    except Exception as e:
        print(f"ERROR: Blockchain write failed: {e}")
        raise


def main(matched_post_path: str = "output/matched_post.json", contract_address: str = None):
    """Main entry point for stage 3"""
    
    # Get contract address from environment or parameter
    if not contract_address:
        contract_address = os.getenv("VERIFIER_CONTRACT_ADDRESS")
    
    if not contract_address:
        print("\n[Stage 3] ✗ FAILED: VERIFIER_CONTRACT_ADDRESS not set in environment\n")
        print("  You need to deploy the Verifier.sol contract first and set its address in .env\n")
        return None
    
    try:
        result = write_to_blockchain(matched_post_path, contract_address)
        print("\n[Stage 3] ✓ SUCCESS: Hash written to blockchain\n")
        return result
    except FileNotFoundError as e:
        print(f"\n[Stage 3] ✗ FAILED: {e}\n")
        return None
    except ValueError as e:
        print(f"\n[Stage 3] ✗ FAILED: {e}\n")
        return None
    except Exception as e:
        print(f"\n[Stage 3] ✗ FAILED: {e}\n")
        return None


if __name__ == "__main__":
    main()
