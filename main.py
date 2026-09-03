"""
Main Orchestration Script
Runs all three stages in sequence:
1. Face Detection & Encoding
2. Reverse Image Search
3. Blockchain Verification
Then runs the verification script to confirm the data matches.
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Import stage modules
import stage1_face
import stage2_search
import stage3_blockchain
import verify


def load_environment():
    """Load environment variables from .env file"""
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
        print("✓ Environment variables loaded from .env\n")
    else:
        print("⚠ .env file not found. Using system environment variables.\n")
        print("  Create a .env file with required variables (see .env.example)\n")


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def main():
    """Main orchestration"""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Face Identification & Blockchain Verification Pipeline"
    )
    parser.add_argument(
        "--image",
        type=str,
        default="input_face.jpg",
        help="Path to input face image (default: input_face.jpg)"
    )
    parser.add_argument(
        "--contract",
        type=str,
        default=None,
        help="Verifier contract address (default: from VERIFIER_CONTRACT_ADDRESS env var)"
    )
    parser.add_argument(
        "--skip-stage3",
        action="store_true",
        help="Skip Stage 3 (blockchain write) - useful for testing without contract deployment"
    )
    parser.add_argument(
        "--use-local-chain",
        action="store_true",
        help="Use local SQLite chain instead of Ethereum (fallback for testing)"
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_environment()
    
    print_header("FACE IDENTIFICATION & BLOCKCHAIN VERIFICATION")
    print("Pipeline started\n")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # ============================================================================
    # STAGE 1: FACE DETECTION & ENCODING
    # ============================================================================
    print_header("[1/4] STAGE 1: Face Detection & Encoding")
    
    if not os.path.isfile(args.image):
        print(f"✗ ERROR: Input image not found: {args.image}\n")
        print("  Make sure you have an image file named 'input_face.jpg' in the project root,")
        print("  or pass the image path with: python main.py --image /path/to/image.jpg\n")
        return False
    
    stage1_result = stage1_face.main(args.image)
    if not stage1_result:
        print("✗ Stage 1 failed. Cannot continue.\n")
        return False
    
    # ============================================================================
    # STAGE 2: REVERSE IMAGE SEARCH
    # ============================================================================
    print_header("[2/4] STAGE 2: Reverse Image Search")
    
    stage2_result = stage2_search.main(args.image)
    if not stage2_result:
        print("⚠ Stage 2 returned no results.")
        print("  This means the image was not found in SerpApi's reverse image search.")
        print("  Try using a face photo that's already posted on social media.\n")
        print("  Stage 3 will not run without output/matched_post.json.\n")
    
    # ============================================================================
    # STAGE 3: BLOCKCHAIN VERIFICATION (Conditional)
    # ============================================================================
    if args.skip_stage3:
        print_header("[3/4] STAGE 3: Blockchain Verification (SKIPPED)")
        print("Stage 3 skipped per --skip-stage3 flag\n")
        stage3_result = None
    elif args.use_local_chain:
        print_header("[3/4] STAGE 3: Blockchain Verification (LOCAL CHAIN)")
        print("Using local SQLite hash chain instead of Ethereum\n")

        if not os.path.isfile("output/matched_post.json"):
            print("✗ Stage 3 blocked: output/matched_post.json does not exist.\n")
            stage3_result = None
            verification_result = False
            return False
        
        try:
            import local_chain
            import hashlib
            import json
            
            # Read matched post
            with open("output/matched_post.json", "r") as f:
                matched_post = json.load(f)
            
            # Compute hash
            combined = f"{matched_post.get('url', '')}{matched_post.get('title', '')}{matched_post.get('source', '')}"
            data_hash = hashlib.sha256(combined.encode()).hexdigest()
            
            # Add to local chain
            chain = local_chain.LocalHashChain()
            record = chain.add_record(data_hash, {
                "matched_post_url": matched_post.get("url", ""),
                "matched_post_title": matched_post.get("title", "")
            })
            
            # Verify integrity
            if chain.verify_chain_integrity():
                print("✓ Record added to local chain")
                print(f"  Chain hash: {record['chain_hash']}")
                print("✓ Chain integrity verified\n")
                stage3_result = record
            else:
                print("✗ Local chain integrity failed\n")
                stage3_result = None
        
        except Exception as e:
            print(f"✗ Local chain error: {e}\n")
            stage3_result = None
    else:
        print_header("[3/4] STAGE 3: Blockchain Verification")

        if not os.path.isfile("output/matched_post.json"):
            print("⚠ Stage 3 blocked: output/matched_post.json does not exist.\n")
            stage3_result = None
            verification_result = False
            return False
        
        # Get contract address
        contract_address = args.contract or os.getenv("VERIFIER_CONTRACT_ADDRESS")
        
        if not contract_address:
            print("⚠ VERIFIER_CONTRACT_ADDRESS not set in environment.\n")
            print("  Stage 3 requires a deployed Verifier smart contract.\n")
            print("  To deploy:\n")
            print("  1. Copy contracts/Verifier.sol to Remix or Hardhat")
            print("  2. Deploy to Sepolia testnet")
            print("  3. Set VERIFIER_CONTRACT_ADDRESS in .env with the deployed address\n")
            print("  Skipping Stage 3 for now.\n")
            stage3_result = None
        else:
            stage3_result = stage3_blockchain.main("output/matched_post.json", contract_address)
            if not stage3_result:
                print("⚠ Stage 3 failed, but pipeline can still verify locally.\n")
    
    # ============================================================================
    # STAGE 4: VERIFICATION
    # ============================================================================
    print_header("[4/4] STAGE 4: Verification")
    
    verification_result = verify.main()
    
    # ============================================================================
    # FINAL SUMMARY
    # ============================================================================
    print_header("PIPELINE COMPLETE")
    
    print("Summary:")
    print(f"  ✓ Stage 1 (Face Detection): {'PASSED' if stage1_result else 'FAILED'}")
    print(f"  {'✓' if stage2_result else '⚠'} Stage 2 (Reverse Search): {'PASSED' if stage2_result else 'NO RESULTS'}")
    print(f"  {'✓' if stage3_result else '⚠'} Stage 3 (Blockchain): {'PASSED' if stage3_result else 'SKIPPED'}")
    print(f"  {'✓' if verification_result else '✗'} Stage 4 (Verification): {'PASSED' if verification_result else 'FAILED'}")
    
    if verification_result:
        print("\n✓✓✓ FULL PIPELINE SUCCESS ✓✓✓\n")
        return True
    else:
        print("\n⚠ Pipeline completed with issues. Check output above.\n")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}\n")
        sys.exit(1)
