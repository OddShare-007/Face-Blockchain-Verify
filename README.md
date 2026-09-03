# Face Identification & Blockchain Verification

A complete end-to-end Python pipeline that demonstrates face detection, reverse image search, and blockchain-based verification. This project is designed for hackathons and serves as a proof-of-concept for decentralized identity verification.

## Project Overview

This pipeline orchestrates three existing tools into one working demonstration:

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  Your Face Photo (input_face.jpg)                               │
│           ↓                                                      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Stage 1: Face Detection & Encoding (DeepFace)           │   │
│  │ • Detects face bounding box                              │   │
│  │ • Generates 512-dim Facenet embedding                    │   │
│  │ • Output: output/face_encoding.json                      │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       ↓                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Stage 2: Reverse Image Search (SerpApi Google Lens)     │   │
│  │ • Searches web for matching images                       │   │
│  │ • Filters for social media domains                       │   │
│  │ • Output: output/matched_post.json                       │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       ↓                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Stage 3: Blockchain Verification (Ethereum Sepolia)     │   │
│  │ • Computes SHA-256 hash of matched post data             │   │
│  │ • Writes hash to Verifier.sol smart contract             │   │
│  │ • Output: output/transaction_record.json                 │   │
│  └────────────────────┬─────────────────────────────────────┘   │
│                       ↓                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Stage 4: Verification (verify.py)                        │   │
│  │ • Re-reads on-chain record                               │   │
│  │ • Re-computes local hash                                 │   │
│  │ • Prints: MATCH: VERIFIED or MATCH: FAILED               │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Why This Design

- **Uses your own face photo**: The reverse image search only finds genuine matches if the image already exists online. Using your own social media photo ensures both an ethical, consenting search and a real test case.
- **Live API integration**: Each stage uses real APIs (DeepFace, SerpApi, Ethereum RPC), not mocked data.
- **Blockchain fallback**: If Sepolia setup is time-constrained, a local SQLite-based append-only hash chain provides an alternative.

## Repository Structure

```
face-blockchain-verify/
├── main.py                    # Orchestration script (runs all stages)
├── stage1_face.py            # Face detection & encoding using DeepFace
├── stage2_search.py          # Reverse image search using SerpApi
├── stage3_blockchain.py      # Write hash to Ethereum Sepolia
├── verify.py                 # Re-verify hash matches on-chain record
├── local_chain.py            # Fallback: SQLite-based append-only chain
├── contracts/
│   └── Verifier.sol          # Solidity smart contract for storing hashes
├── output/                   # (Auto-created) Output files from each stage
│   ├── face_encoding.json    # Face embedding from Stage 1
│   ├── matched_post.json     # Matched social media post from Stage 2
│   └── transaction_record.json # Blockchain transaction details from Stage 3
├── .env.example              # Template for environment variables
├── .env                       # (Create from .env.example) API keys & config
├── requirements.txt          # Python dependencies
├── README.md                 # This file
└── PROJECT_CONTEXT.md        # Checklist & project state tracking
```

## Setup Instructions

### 1. Clone & Environment Setup

```bash
# Clone the repository
git clone <this-repo>
cd face-blockchain-verify

# Create a Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Get API Keys & Configure Environment

#### 2a. SerpApi (Reverse Image Search)

1. Sign up at https://serpapi.com/ (free tier: 100/month)
2. Copy your API key from the dashboard
3. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
4. Add your SerpApi key:
   ```
   SERPAPI_KEY=your_serpapi_key_here
   ```

#### 2b. Ethereum Sepolia Testnet (Blockchain)

**Option A: Using Alchemy (Recommended)**

1. Sign up at https://www.alchemy.com/ (free tier)
2. Create a new app, select Ethereum → Sepolia testnet
3. Copy the HTTPS RPC URL from the dashboard
4. Add to `.env`:
   ```
   SEPOLIA_RPC_URL=https://eth-sepolia.alchemyapi.io/v2/YOUR-API-KEY
   ```

**Option B: Using Infura**

1. Sign up at https://www.infura.io/ (free tier)
2. Create a new project, select Sepolia
3. Copy the HTTPS endpoint
4. Add to `.env`:
   ```
   SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR-PROJECT-ID
   ```

#### 2c. Ethereum Wallet (Private Key)

1. Use an existing wallet or create a new test wallet:
   - MetaMask: Create a new account (separate from your main wallet)
   - Or use: https://www.ethereumwallet.io/ (advanced users only)

2. Export private key (WITHOUT the `0x` prefix) and add to `.env`:
   ```
   PRIVATE_KEY=abc123def456789...
   ```

3. Get Sepolia test ETH from a faucet:
   - https://sepolia-faucet.pk910.de/ (no login needed)
   - https://www.alchemy.com/faucets/ethereum (free Alchemy account)
   - Paste your wallet address, get ~0.5 ETH for free

#### 2d. Deploy Verifier Smart Contract

The smart contract needs to be deployed first. Use one of these methods:

**Option 1: Remix (Easiest)**

1. Go to https://remix.ethereum.org/
2. Create a new file `Verifier.sol`
3. Copy the contents of `contracts/Verifier.sol` into Remix
4. In the left sidebar:
   - Click "Solidity Compiler" (compile with version 0.8.0 or higher)
   - Click "Deploy & Run Transactions"
   - Change the environment to "Injected Provider - MetaMask"
   - Select your Sepolia-connected wallet in MetaMask
   - Click "Deploy"
5. Copy the deployed contract address and add to `.env`:
   ```
   VERIFIER_CONTRACT_ADDRESS=0x1234567890123456789012345678901234567890
   ```

**Option 2: Hardhat (Advanced)**

1. Install Hardhat: `npm install --save-dev hardhat`
2. Create a Hardhat project and configure it for Sepolia
3. Deploy using a Hardhat script (see Hardhat docs)
4. Add the deployed address to `.env`

### 3. Prepare Test Image

1. Use a face photo of yourself that's already posted on your social media (Twitter, Instagram, LinkedIn, Facebook, Reddit, TikTok, or YouTube)
2. Download or save it as `input_face.jpg` in the project root
3. The face should be clearly visible and reasonably well-lit

**Why your own photo?** The reverse image search only finds real matches if the image already exists online. Using your own photo is both ethical (consenting) and guarantees a real test case.

### 4. Verify Configuration

Double-check your `.env` file has all required variables:

```bash
# Check which variables are set
cat .env

# Verify it has:
# - SERPAPI_KEY
# - SEPOLIA_RPC_URL
# - VERIFIER_CONTRACT_ADDRESS
# - PRIVATE_KEY
```

## Running the Pipeline

### Full Pipeline (All Stages)

```bash
# Run with default input image (input_face.jpg)
python main.py

# Run with custom image path
python main.py --image path/to/your/image.jpg

# Use local SQLite chain instead of Ethereum (for testing without blockchain)
python main.py --use-local-chain

# Skip Stage 3 (blockchain write) - useful for debugging
python main.py --skip-stage3
```

### Individual Stages (For Debugging)

```bash
# Stage 1: Face Detection
python stage1_face.py input_face.jpg

# Stage 2: Reverse Search
python stage2_search.py input_face.jpg

# Stage 3: Blockchain Write (requires matched_post.json from Stage 2)
python stage3_blockchain.py

# Stage 4: Verification
python verify.py
```

### Expected Output

```
======================================================================
  FACE IDENTIFICATION & BLOCKCHAIN VERIFICATION
======================================================================

[1/4] STAGE 1: Face Detection & Encoding
  → Processing image: input_face.jpg
  → Face detected at bounding box: (120, 150) size 200x250
  ✓ Face encoding saved to: output/face_encoding.json
  ✓ Embedding vector dimension: 512

[1/4] ✓ SUCCESS: Face detected and encoded

======================================================================
  [2/4] STAGE 2: Reverse Image Search
======================================================================

  → Sending request to SerpApi Google Lens...
  → Found 5 social media match(es)
  ✓ Matched post found:
    Title: My profile picture from last month
    URL: https://twitter.com/username/status/12345...
    Source: twitter.com
  ✓ Match saved to: output/matched_post.json

======================================================================
  [3/4] STAGE 3: Blockchain Verification
======================================================================

  → Computed hash of matched post: abc123def456...
  → Connecting to Sepolia RPC...
  → Using account: 0xYourWalletAddress
  → Target contract: 0xVerifierContractAddress
  → Building transaction...
  → Sending transaction...
  ✓ Transaction sent: 0x789def123abc...
  ✓ Transaction confirmed in block 5123456
  ✓ View on Etherscan: https://sepolia.etherscan.io/tx/0x789def123abc...

======================================================================
  [4/4] STAGE 4: Verification
======================================================================

============================================================
VERIFICATION SUMMARY
============================================================
Status: VERIFIED
Match: ✓ YES
Local hash:    abc123def456...
On-chain hash: abc123def456...
Transaction:   0x789def123abc...
Etherscan:     https://sepolia.etherscan.io/tx/0x789def123abc...
Post URL:      https://twitter.com/username/status/12345...
============================================================

✓✓✓ FULL PIPELINE SUCCESS ✓✓✓
```

## Real Example (Sepolia Testnet)

**Test Run Date**: [Your test date]
**Test Image**: [Your social media photo]
**Test Account**: [Your Ethereum address]

**Transaction Hash**: `0x789def123abc...`
**Contract Address**: `0x1234567890123456789012345678901234567890`
**Block Number**: `5123456`
**View on Etherscan**: https://sepolia.etherscan.io/tx/0x789def123abc...

(Update this section after your first successful test run)

## Error Handling & Troubleshooting

### Common Issues

#### "Image file not found: input_face.jpg"
- **Cause**: No input image in project root
- **Fix**: Add an image file named `input_face.jpg` or pass the path: `python main.py --image path/to/image.jpg`

#### "No face detected in image"
- **Cause**: DeepFace couldn't find a face in the image
- **Fix**: 
  - Make sure the face is clearly visible and not rotated
  - Image should be at least 100x100 pixels
  - Good lighting helps
  - Try a different photo

#### "SERPAPI_KEY environment variable not set"
- **Cause**: API key not in `.env` or not loaded
- **Fix**: 
  - Make sure `.env` exists (copy from `.env.example`)
  - Add your SerpApi key: `SERPAPI_KEY=your_key`
  - Restart your terminal after adding to `.env`

#### "No visual matches found from reverse image search"
- **Cause**: Image not indexed by Google/SerpApi reverse search engine yet
- **Fix**:
  - Use an image that's already posted on social media (not a fresh photo)
  - Wait 24-48 hours for Google to index newly posted images
  - Try a more popular image (e.g., profile picture that's been up for a while)
  - Different image quality/format may help

#### "Failed to connect to Sepolia RPC endpoint"
- **Cause**: Bad RPC URL or network issue
- **Fix**:
  - Verify `SEPOLIA_RPC_URL` in `.env` is correct
  - Check if your RPC provider (Alchemy/Infura) is reachable
  - Try a different RPC provider
  - Check your internet connection

#### "VERIFIER_CONTRACT_ADDRESS not set in environment"
- **Cause**: Smart contract not deployed or address not in `.env`
- **Fix**:
  - Deploy `contracts/Verifier.sol` using Remix or Hardhat (see Setup section)
  - Copy deployed address to `VERIFIER_CONTRACT_ADDRESS` in `.env`
  - Or use `--use-local-chain` flag for SQLite fallback

#### "Transaction failed or reverted"
- **Cause**: Insufficient gas, bad contract address, or contract issue
- **Fix**:
  - Verify contract address is correct (0x prefix + 40 hex chars)
  - Make sure wallet has Sepolia test ETH (get from faucet)
  - Increase gas limit in stage3_blockchain.py if needed
  - Check transaction on https://sepolia.etherscan.io

### Enable Debug Logging

Each stage prints detailed logs. For more information:

```bash
# Linux/Mac: Show full output including intermediate steps
python main.py 2>&1 | tee pipeline.log

# Windows PowerShell:
python main.py | Tee-Object -FilePath pipeline.log

# Then review: cat pipeline.log
```

## Known Limitations

1. **Reverse Image Search Accuracy**: The reverse image search depends entirely on:
   - The image already existing on the web (indexed by Google)
   - The social media site allowing it to be indexed
   - Image quality and recognizability
   - This is NOT biometric face recognition (like Apple FaceID or Windows Hello)

2. **Intended Use**: This demo is designed for:
   - Verifying one's own identity/content on social media
   - NOT for searching, identifying, or tracking unconsenting third parties
   - Use responsibly and ethically

3. **Blockchain Limitations**:
   - Sepolia is a testnet (not real ETH, for testing only)
   - Transactions take 10-30 seconds to confirm
   - Gas fees are minimal but not zero (even on testnet)
   - Data on blockchain is permanent (design feature, not a bug)

4. **API Rate Limits**:
   - SerpApi free tier: 100 requests/month
   - Ethereum RPC: Depends on provider, usually generous for free tier

5. **Privacy**: 
   - Image URL and matched post data are stored locally and on blockchain
   - The blockchain transaction is public (Etherscan)
   - Don't use this pipeline with sensitive photos

## Ethics & Consent

This project is explicitly designed around **consent**:

- It uses YOUR OWN face photo (from your social media)
- It only finds images already publicly indexed by Google
- It does NOT download or store images of non-consenting people
- It does NOT use facial recognition to identify strangers
- It does NOT scrape or expose private data

If you use this pipeline, you agree to:
- Only use it with photos of people who have consented
- Not use it to search for or identify unconsenting third parties
- Comply with all applicable laws and platform ToS
- Treat face data and blockchain records responsibly

## Project Checklist

See [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for a detailed checklist of:
- Setup steps and status
- Files and their purposes
- Known working state
- Things still to do
- Common errors and fixes

## Development & Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code with Black
black *.py

# Lint with Pylint (optional)
pylint *.py
```

### Deploy Your Own Verifier Contract

```bash
# Using Hardhat (requires Node.js)
npm install --save-dev hardhat
npx hardhat init
# Then create scripts/deploy.js (see Hardhat docs)
# And run: npx hardhat run scripts/deploy.js --network sepolia
```

## Future Enhancements

Potential ideas to extend this project:

- [ ] Add multiple face matching (compare multiple social media photos)
- [ ] Support other blockchains (Polygon, Arbitrum, etc.)
- [ ] Implement zero-knowledge proofs for privacy
- [ ] Add a frontend dashboard (React/Vue)
- [ ] Cache verified records for faster lookup
- [ ] Add signature verification (sign data with private key)
- [ ] Support NFT minting for verified identities
- [ ] Multi-signature support (multiple verifiers)

## License

[Add your license here - e.g., MIT, GPL, etc.]

## Support & Contact

For issues, questions, or contributions:
- Open an issue on GitHub
- Check [PROJECT_CONTEXT.md](PROJECT_CONTEXT.md) for troubleshooting
- Review the individual stage files for detailed documentation

---

**Happy Hacking! 🚀**
#   F a c e - B l o c k c h a i n - V e r i f y  
 