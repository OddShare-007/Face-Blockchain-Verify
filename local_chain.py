"""
Local Chain Fallback
If Ethereum Sepolia setup isn't available, this provides a simulated append-only hash chain
using SQLite. Each record stores hash(previous_record_hash + new_data_hash).
"""

import os
import json
import sqlite3
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class LocalHashChain:
    """
    Simple append-only hash chain using SQLite.
    Each record contains: id, data_hash, chain_hash (previous_hash + current_hash), timestamp
    """
    
    def __init__(self, db_path: str = "output/local_chain.db"):
        """Initialize the hash chain database"""
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create database table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chain_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data_hash TEXT NOT NULL,
                    chain_hash TEXT NOT NULL,
                    previous_hash TEXT,
                    timestamp TEXT NOT NULL,
                    metadata TEXT
                )
            """)
            conn.commit()
    
    def _get_latest_hash(self) -> str:
        """Get the hash of the latest record in the chain"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT chain_hash FROM chain_records ORDER BY id DESC LIMIT 1"
            )
            result = cursor.fetchone()
            return result[0] if result else "genesis"
    
    def add_record(self, data_hash: str, metadata: Dict = None) -> Dict:
        """
        Add a new record to the chain.
        
        Args:
            data_hash: SHA-256 hash of the data to store
            metadata: Optional metadata about this record
            
        Returns:
            dict: The record that was added
        """
        
        if not data_hash:
            raise ValueError("data_hash cannot be empty")
        
        # Get previous hash
        previous_hash = self._get_latest_hash()
        
        # Compute chain hash: hash(previous_hash + current_data_hash)
        combined = f"{previous_hash}{data_hash}"
        chain_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        # Prepare record
        timestamp = datetime.now().isoformat()
        metadata_json = json.dumps(metadata or {})
        
        # Add to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO chain_records (data_hash, chain_hash, previous_hash, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (data_hash, chain_hash, previous_hash, timestamp, metadata_json))
            conn.commit()
            record_id = cursor.lastrowid
        
        return {
            "id": record_id,
            "data_hash": data_hash,
            "chain_hash": chain_hash,
            "previous_hash": previous_hash,
            "timestamp": timestamp,
            "metadata": metadata
        }
    
    def get_latest_record(self) -> Optional[Dict]:
        """Get the most recent record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, data_hash, chain_hash, previous_hash, timestamp, metadata FROM chain_records ORDER BY id DESC LIMIT 1"
            )
            result = cursor.fetchone()
            
            if not result:
                return None
            
            return {
                "id": result[0],
                "data_hash": result[1],
                "chain_hash": result[2],
                "previous_hash": result[3],
                "timestamp": result[4],
                "metadata": json.loads(result[5]) if result[5] else {}
            }
    
    def get_all_records(self) -> List[Dict]:
        """Get all records in the chain"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id, data_hash, chain_hash, previous_hash, timestamp, metadata FROM chain_records ORDER BY id"
            )
            
            records = []
            for row in cursor.fetchall():
                records.append({
                    "id": row[0],
                    "data_hash": row[1],
                    "chain_hash": row[2],
                    "previous_hash": row[3],
                    "timestamp": row[4],
                    "metadata": json.loads(row[5]) if row[5] else {}
                })
            
            return records
    
    def verify_chain_integrity(self) -> bool:
        """
        Verify that the entire chain is valid.
        Each record's chain_hash should equal hash(previous_hash + current_data_hash)
        """
        records = self.get_all_records()
        
        if not records:
            return True  # Empty chain is valid
        
        prev_hash = "genesis"
        
        for record in records:
            # Compute what the chain hash should be
            combined = f"{prev_hash}{record['data_hash']}"
            expected_chain_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            # Verify it matches what's stored
            if record['chain_hash'] != expected_chain_hash:
                print(f"  ✗ Chain integrity failed at record {record['id']}")
                print(f"    Expected: {expected_chain_hash}")
                print(f"    Got: {record['chain_hash']}")
                return False
            
            prev_hash = record['chain_hash']
        
        return True
    
    def to_json(self, output_path: str = "output/local_chain.json"):
        """Export the entire chain to JSON"""
        records = self.get_all_records()
        
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump({
                "chain_records": records,
                "total_records": len(records),
                "integrity_verified": self.verify_chain_integrity(),
                "export_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        return output_path


def main():
    """Example usage and testing"""
    
    print("[Local Chain] Initializing local hash chain...")
    
    chain = LocalHashChain()
    
    # Example: Add a test record
    test_hash = hashlib.sha256(b"test_data").hexdigest()
    record = chain.add_record(test_hash, {"source": "test", "timestamp": datetime.now().isoformat()})
    
    print(f"  ✓ Added record: {record['id']}")
    print(f"    Data hash: {record['data_hash']}")
    print(f"    Chain hash: {record['chain_hash']}")
    
    # Verify chain integrity
    if chain.verify_chain_integrity():
        print("  ✓ Chain integrity verified")
    else:
        print("  ✗ Chain integrity check failed")
    
    # Export to JSON
    chain.to_json()
    print(f"  ✓ Chain exported to output/local_chain.json")


if __name__ == "__main__":
    main()
