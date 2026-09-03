# PROJECT_CONTEXT.md

**Purpose**: Running checklist and reference file for the Face Blockchain Verify project. Open this first when resuming work.

**Last Updated**: [See "Known Working State" section below]

---

## Setup Checklist

Complete these steps in order before running the pipeline:

- [ ] **Python Environment**
  - [ ] Virtual environment created: `python -m venv venv`
  - [ ] Virtual environment activated: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
  - [ ] Dependencies installed: `pip install -r requirements.txt`
  - [ ] Verify installation: `python -c "import deepface, web3, serpapi; print('OK')"`

- [ ] **Environment Configuration (.env file)**
  - [ ] `.env.example` exists in project root
  - [ ] `.env` created (copy from `.env.example`): `cp .env.example .env`
  - [ ] Set `SERPAPI_KEY` in `.env`
    - [ ] Signed up at https://serpapi.com/
    - [ ] Copied API key from dashboard
  - [ ] Set `SEPOLIA_RPC_URL` in `.env`
    - [ ] Signed up at Alchemy or Infura
    - [ ] Created Sepolia testnet app
    - [ ] Copied HTTPS RPC endpoint
  - [ ] Set `VERIFIER_CONTRACT_ADDRESS` in `.env`
    - [ ] Deployed `contracts/Verifier.sol` to Sepolia
    - [ ] Copied deployed contract address (0x format)
  - [ ] Set `PRIVATE_KEY` in `.env`
    - [ ] Created or selected test wallet
    - [ ] Exported private key (WITHOUT 0x prefix)
    - [ ] Wallet has Sepolia test ETH (from faucet)

- [ ] **Test Image Setup**
  - [ ] Selected a face photo from your own social media (Twitter, Instagram, LinkedIn, etc.)
  - [ ] Downloaded image and saved as `input_face.jpg` in project root
  - [ ] Verified image file exists: `ls input_face.jpg` or `dir input_face.jpg`
  - [ ] Image shows a clear, visible face

- [ ] **Output Directory**
  - [ ] `output/` directory created (auto-created by pipeline, but can verify)
  - [ ] Directory is writable

---

## File Manifest & Purposes

| File | Purpose | Stage(s) | Status |
|------|---------|---------|--------|
| `main.py` | Orchestration script, runs all stages | All | ✓ Ready |
| `stage1_face.py` | Face detection & encoding | 1 | ✓ Ready |
| `stage2_search.py` | Reverse image search | 2 | ✓ Ready |
| `stage3_blockchain.py` | Write hash to blockchain | 3 | ✓ Ready |
| `verify.py` | Verification & comparison | 4 | ✓ Ready |
| `local_chain.py` | Fallback SQLite hash chain | 3 (alt) | ✓ Ready |
| `contracts/Verifier.sol` | Solidity smart contract | 3 | ✓ Ready |
| `.env.example` | Template for env vars | Setup | ✓ Ready |
| `.env` | Actual env vars (create from example) | Setup | ⚠ Needs creation & population |
| `requirements.txt` | Python dependencies | Setup | ✓ Ready |
| `README.md` | Full documentation | All | ✓ Ready |
| `PROJECT_CONTEXT.md` | This file | All | ✓ Ready |
| `output/face_encoding.json` | Output from Stage 1 | 1 | (Auto-generated) |
| `output/matched_post.json` | Output from Stage 2 | 2 | (Auto-generated) |
| `output/transaction_record.json` | Output from Stage 3 | 3 | (Auto-generated) |
| `output/local_chain.json` | Output from local chain (alt) | 3 (alt) | (Auto-generated) |
| `input_face.jpg` | Input image file | 1-4 | ⚠ Needs to be added |

---

## Known Working State

**Last Code Review**: 2026-01-24 - Initial Build Complete ✓

**Self-Test Results** (Code verification only, not runtime execution):
- [x] All Python files created with correct syntax
- [x] All imports verified (deepface, web3, requests, etc.)
- [x] File path consistency verified across all stages
- [x] Environment variable names match in code and .env.example
- [x] JSON data structures consistent at each handoff
- [x] Error handling implemented for all failure modes
- [x] os.makedirs() calls present before file writes
- [x] Smart contract ABI includes required storeRecord() function
- [x] All function signatures match how they're called in main.py
- [x] Docstrings and type hints present throughout
- [x] No unused imports (except defensive serpapi check which is OK)

**First Runtime Test**: [PENDING - Execute pipeline for first time]
- Test Image: [To be chosen by user]
- Test Date/Time: [Pending]
- Test Account: [Pending]
- Expected Results:
  - [ ] Stage 1: Face detected ✓
  - [ ] Stage 2: Post found ✓
  - [ ] Stage 3: Hash written to blockchain ✓
  - [ ] Stage 4: Verification passed ✓

**Real Blockchain Test** (after contract deployment):
- Transaction Hash: `[To be filled after first test]`
- Contract Address: `[From environment]`
- Block Number: `[From receipt]`
- Etherscan Link: `[To be filled after first test]`
- Test Date: `[To be filled after first test]`

---

## Things You Still Need To Do

### Before First Run

1. **Create `.env` file**
   ```bash
   cp .env.example .env
   # Then edit .env with your actual API keys
   ```

2. **Get API Keys**
   - [ ] SerpApi key (https://serpapi.com/) → Add to `SERPAPI_KEY`
   - [ ] Alchemy/Infura RPC URL (Sepolia) → Add to `SEPOLIA_RPC_URL`
   - [ ] Private key from test wallet → Add to `PRIVATE_KEY` (without 0x)

3. **Deploy Smart Contract**
   - [ ] Go to https://remix.ethereum.org/
   - [ ] Copy `contracts/Verifier.sol` into Remix
   - [ ] Set Solidity version to 0.8.0+
   - [ ] Connect MetaMask to Sepolia testnet
   - [ ] Click "Deploy"
   - [ ] Copy deployed address → Add to `VERIFIER_CONTRACT_ADDRESS`

4. **Get Sepolia Test ETH**
   - [ ] Go to https://sepolia-faucet.pk910.de/
   - [ ] Paste your wallet address
   - [ ] Receive ~0.5 Sepolia ETH
   - [ ] Verify in MetaMask or on Etherscan

5. **Prepare Test Image**
   - [ ] Download a photo of yourself from social media
   - [ ] Save as `input_face.jpg` in project root
   - [ ] Verify it's a clear face photo

### First Test Run

1. **Run Full Pipeline**
   ```bash
   python main.py --image input_face.jpg
   ```

2. **Check Each Stage Output**
   - [ ] `output/face_encoding.json` - Contains embedding vector
   - [ ] `output/matched_post.json` - Contains matched social post URL
   - [ ] `output/transaction_record.json` - Contains blockchain transaction
   - [ ] Final verification should print `MATCH: VERIFIED`

3. **Verify on Blockchain**
   - [ ] Copy transaction hash from output
   - [ ] Go to https://sepolia.etherscan.io/
   - [ ] Paste transaction hash to view on-chain record
   - [ ] Confirm your wallet address is the sender
   - [ ] Confirm transaction was successful

4. **Update "Known Working State" Section**
   - [ ] Fill in test date, image, and account
   - [ ] Copy transaction hash and block number
   - [ ] Update Etherscan link
   - [ ] Mark as "First test: PASSED"

### Ongoing

- [ ] Run pipeline monthly or after code changes to verify still works
- [ ] Keep Sepolia test ETH in wallet (~0.5 ETH is enough for many transactions)
- [ ] Monitor SerpApi usage (free tier = 100/month)
- [ ] Update this file whenever you make changes

---

## Common Errors & Fixes

### Setup/Installation Errors

**Error**: `ModuleNotFoundError: No module named 'deepface'`
```
Fix: pip install -r requirements.txt
     (Make sure virtual environment is activated)
```

**Error**: `FileNotFoundError: .env file not found`
```
Fix: cp .env.example .env
     Then edit .env with your API keys
```

**Error**: `ModuleNotFoundError: No module named 'dotenv'`
```
Fix: pip install python-dotenv
```

### Stage 1: Face Detection Errors

**Error**: `No face detected in image`
```
Cause: Face not clearly visible or image quality too low
Fix:   - Use a high-quality photo with clear face
       - Make sure face is front-facing or near front-facing
       - Good lighting helps
       - Image should be at least 100x100 pixels
       - Try a different image
```

**Error**: `tensorflow not installed` or `keras errors`
```
Cause: DeepFace dependencies not installed
Fix:   pip install tensorflow keras
       # May take a while on first install
```

### Stage 2: Reverse Search Errors

**Error**: `SERPAPI_KEY environment variable not set`
```
Fix: 1. Sign up at https://serpapi.com/
     2. Copy API key from dashboard
     3. Add to .env: SERPAPI_KEY=your_key
     4. Restart terminal or reload .env
```

**Error**: `No visual matches found from reverse image search`
```
Cause: Image not indexed by Google yet, or too new/rare
Fix:   - Use image already posted on social media weeks ago
       - Popular images (profile pics) more likely to be indexed
       - Wait 24-48 hours if you just posted it
       - Try a different image
       - SerpApi free tier limited to 100/month
```

**Error**: `API key invalid or request failed`
```
Fix: 1. Verify SERPAPI_KEY in .env is correct
     2. Check SerpApi dashboard - key still active?
     3. Verify internet connection
     4. Try staging2_search.py directly to see full error
```

### Stage 3: Blockchain Errors

**Error**: `SEPOLIA_RPC_URL environment variable not set`
```
Fix: 1. Sign up at https://www.alchemy.com/ or https://www.infura.io/
     2. Create new app, select Ethereum + Sepolia
     3. Copy HTTPS endpoint
     4. Add to .env: SEPOLIA_RPC_URL=https://eth-sepolia.alchemyapi.io/v2/YOUR-KEY
```

**Error**: `Failed to connect to Sepolia RPC endpoint`
```
Cause: Bad RPC URL, network issue, or provider down
Fix:   - Verify SEPOLIA_RPC_URL in .env is correct (full HTTPS URL)
       - Check your internet connection
       - Try Infura instead of Alchemy (or vice versa)
       - Verify RPC endpoint works: curl your_rpc_url
```

**Error**: `VERIFIER_CONTRACT_ADDRESS not set in environment`
```
Cause: Smart contract not deployed yet
Fix:   1. Go to https://remix.ethereum.org/
        2. Create new file: Verifier.sol
        3. Copy contents from contracts/Verifier.sol
        4. Compile (Solidity Compiler, version 0.8.0+)
        5. Deploy (Deploy & Run Transactions tab)
        6. Copy deployed address (0x...)
        7. Add to .env: VERIFIER_CONTRACT_ADDRESS=0x...
```

**Error**: `PRIVATE_KEY environment variable not set`
```
Fix: 1. Use MetaMask or create test wallet
     2. Export private key (Settings → Account Details → Export)
     3. Copy without the 0x prefix
     4. Add to .env: PRIVATE_KEY=abc123def456...
     WARNING: Never commit .env to version control!
```

**Error**: `Insufficient funds for gas`
```
Cause: Wallet doesn't have enough Sepolia ETH
Fix:   1. Go to https://sepolia-faucet.pk910.de/
        2. Paste wallet address
        3. Get ~0.5 Sepolia ETH
        4. Wait 1-2 minutes for it to arrive
        5. Verify in MetaMask or Etherscan
```

**Error**: `Transaction failed` or `Transaction reverted`
```
Cause: Bad contract address, contract issues, or gas limit too low
Fix:   - Verify contract address is correct format (0x + 40 hex chars)
       - Verify contract address has working Verifier.sol deployed
       - Increase gas limit in stage3_blockchain.py (line: "gas": 100000)
       - Check Etherscan: search tx hash, see error message
```

### Stage 4: Verification Errors

**Error**: `MATCH: FAILED` (hashes don't match)
```
Cause: Data changed between Stage 2 and 3, or blockchain issue
Fix:   - Verify matched_post.json wasn't manually edited
       - Check transaction on Etherscan - is it confirmed?
       - Re-run pipeline from fresh (all files get overwritten)
```

**Error**: `Verification timeout or RPC call failed`
```
Cause: Network issue or RPC endpoint slow
Fix:   - Verify internet connection
       - Try different RPC endpoint
       - Wait a minute and retry
```

### General Troubleshooting

**Error**: `Code works but pipeline seems to hang`
```
Possible causes:
- API call waiting for response (normal, can take 10-30 sec)
- RPC connection slow or RPC endpoint rate-limited
- Large image processing in Stage 1

Fix:   - Wait 1-2 minutes
       - Check console for any error messages
       - Run individual stage to isolate issue: python stage2_search.py
       - Increase timeout values if needed
```

**Error**: `Terminal/Command not found`
```
Fix: Make sure virtual environment is activated:
     Windows: venv\Scripts\activate
     Mac/Linux: source venv/bin/activate
     
     Then try: python main.py
```

---

## Quick Reference Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate  # Windows, or: source venv/bin/activate
pip install -r requirements.txt

# Create .env from template
cp .env.example .env
# Edit .env with your API keys

# Run pipeline
python main.py
python main.py --image input_face.jpg
python main.py --use-local-chain  # No blockchain needed
python main.py --skip-stage3       # Skip blockchain for testing

# Test individual stages
python stage1_face.py input_face.jpg
python stage2_search.py input_face.jpg
python stage3_blockchain.py
python verify.py

# Check environment
echo %SERPAPI_KEY%  # Windows, or: echo $SERPAPI_KEY on Mac/Linux
```

---

## Notes for Future Self

When resuming this project:

1. **First thing**: Open this file and check "Known Working State" section
2. **Second thing**: Verify `.env` file has all variables set (don't commit to git)
3. **Before running**: Activate venv and verify dependencies: `pip list | grep -E "deepface|web3|requests"`
4. **After changes**: Update this file with new date/status
5. **When troubleshooting**: Check "Common Errors" section first

---

## Session Log

Track important events and changes:

- **[Initial Build]**: Created all project files, scripts, and documentation
  - All 7 Python files created
  - Smart contract created
  - README and docs completed
  - Ready for first test run
  
- **[Pending: First Test]**: To be filled after running pipeline for first time
  
- **[Pending: Deployment]**: Track any contract redeployments or major updates

---

**End of PROJECT_CONTEXT.md**
