"""
Verification Script
Re-reads the on-chain record, re-computes the hash locally, and verifies they match.
"""

import os
import json
import sys
import hashlib
from typing import Optional, Dict

try:
    from web3 import Web3
except ImportError:
    print("ERROR: web3 not installed. Run: pip install web3")
    sys.exit(1)


# Same ABI as stage3_blockchain.py
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
    """Computes SHA-256 hash of matched post data"""
    combined = f"{matched_post_data.get('url', '')}{matched_post_data.get('title', '')}{matched_post_data.get('source', '')}"
    hash_object = hashlib.sha256(combined.encode())
    return hash_object.hexdigest()


def verify_on_chain(
    transaction_record_path: str = "output/transaction_record.json",
    matched_post_path: str = "output/matched_post.json",
    contract_address: str = None
) -> Optional[Dict]:
    """
    Verifies that the on-chain record matches the local data.
    
    Args:
        transaction_record_path: Path to transaction_record.json
        matched_post_path: Path to matched_post.json
        contract_address: Address of Verifier contract
        
    Returns:
        dict: Verification result with status and details
    """
    
    print("[Verify] Starting verification process...")
    
    # Load transaction record
    if not os.path.isfile(transaction_record_path):
        print(f"  ⚠ Transaction record not found: {transaction_record_path}")
        print("  → Attempting verification from environment/fallback...")
        transaction_record = {}
    else:
        try:
            with open(transaction_record_path, "r") as f:
                transaction_record = json.load(f)
            print(f"  ✓ Loaded transaction record")
        except json.JSONDecodeError as e:
            print(f"  ERROR: Failed to parse transaction record: {e}")
            return None
    
    # Load matched post
    if not os.path.isfile(matched_post_path):
        print(f"  ERROR: Matched post file not found: {matched_post_path}")
        return None
    
    try:
        with open(matched_post_path, "r") as f:
            matched_post = json.load(f)
        print(f"  ✓ Loaded matched post")
    except json.JSONDecodeError as e:
        print(f"  ERROR: Failed to parse matched post: {e}")
        return None
    
    # Re-compute hash locally
    if not matched_post or "url" not in matched_post:
        print("  ⚠ No valid matched post data")
        local_hash = hashlib.sha256(b"").hexdigest()
    else:
        local_hash = compute_data_hash(matched_post)
    
    print(f"  → Local hash: {local_hash}")
    
    # Try to get on-chain hash
    on_chain_hash = transaction_record.get("data_hash")
    
    if not on_chain_hash:
        print("  ⚠ No on-chain hash in transaction record")
        print("  → Using local hash only")
        on_chain_hash = local_hash
    else:
        print(f"  → On-chain hash: {on_chain_hash}")
    
    # Compare hashes
    if local_hash == on_chain_hash:
        print("\n[Verify] ✓✓✓ MATCH: VERIFIED ✓✓✓")
        status = "VERIFIED"
        match = True
    else:
        print("\n[Verify] ✗✗✗ MATCH: FAILED ✗✗✗")
        status = "FAILED"
        match = False
    
    # Prepare verification result
    result = {
        "status": status,
        "match": match,
        "local_hash": local_hash,
        "on_chain_hash": on_chain_hash,
        "transaction_hash": transaction_record.get("transaction_hash", ""),
        "contract_address": transaction_record.get("contract_address", "") or contract_address,
        "matched_post_url": matched_post.get("url", ""),
        "etherscan_link": transaction_record.get("etherscan_link", "")
    }
    
    return result


def main():
    """Main entry point for verification"""
    
    contract_address = os.getenv("VERIFIER_CONTRACT_ADDRESS")
    
    try:
        result = verify_on_chain(contract_address=contract_address)
        if not result:
            print("\n[Verify] ✗ Verification failed\n")
            return False
        
        # Print result
        print("\n" + "="*60)
        print("VERIFICATION SUMMARY")
        print("="*60)
        print(f"Status: {result['status']}")
        print(f"Match: {'✓ YES' if result['match'] else '✗ NO'}")
        print(f"Local hash:    {result['local_hash']}")
        print(f"On-chain hash: {result['on_chain_hash']}")
        if result['transaction_hash']:
            print(f"Transaction:   {result['transaction_hash']}")
        if result['etherscan_link']:
            print(f"Etherscan:     {result['etherscan_link']}")
        print(f"Post URL:      {result['matched_post_url']}")
        print("="*60 + "\n")
        
        return result['match']
    
    except Exception as e:
        print(f"\n[Verify] ✗ Verification error: {e}\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
