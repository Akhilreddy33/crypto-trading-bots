# 📋 PHASE 1: COMPLETE SETUP GUIDE
## ⏱️ Time: 20-30 minutes | Day 1

This guide walks you through everything needed before building any bots.

---

## ✅ Step 1: Create Groq AI Account (5 mins)

Groq provides FREE AI API for trading signals.

**DO THIS:**
1. Go to https://console.groq.com
2. Click "Sign Up"
3. Use any email (Gmail recommended)
4. Verify your email
5. Go to API Keys section
6. Create new API key
7. Copy the full key

**YOU'LL GET:** `gsk_xxxxxxxxxxxxxxxxxxxxxxxx`

✅ **DONE!** Save this key somewhere safe.

---

## ✅ Step 2: Create Binance Testnet Account (5 mins)

Binance Testnet = Practice trading with fake money (SAFE!)

**DO THIS:**
1. Go to https://testnet.binance.vision
2. Click "Testnet Login" 
3. Use any email
4. Set password
5. Go to "API Management"
6. Click "Create API"
7. Label: "CryptoBot"
8. Copy **API Key** AND **Secret Key**

**YOU'LL GET:**
- `BINANCE_TESTNET_API_KEY=xxxxxxxx...`
- `BINANCE_TESTNET_API_SECRET=yyyyy...`

✅ **DONE!** Save both keys.

---

## ✅ Step 3: Create Reddit App (5 mins)

Reddit = News source for Bot 7 (News Bot)

**DO THIS:**
1. Go to https://reddit.com/prefs/apps
2. Click "are you a developer? create an app"
3. Fill form:
   - **Name:** CryptoBot
   - **App type:** Script
   - **Description:** Crypto trading news bot
   - **Redirect URI:** http://localhost:8080
4. Click "Create app"
5. Copy:
   - **Client ID** (under app name)
   - **Client Secret** (next to it)

**YOU'LL GET:**
- `REDDIT_CLIENT_ID=xxxxxxxx...`
- `REDDIT_CLIENT_SECRET=yyyyyy...`

✅ **DONE!** Save both.

---

## ✅ Step 4: Install Python 3.10+ (5 mins)

**Check if already installed:**
```bash
python --version
```

If you see `3.10` or higher → **Skip to Step 5**

**If NOT installed:**
1. Go to https://www.python.org/downloads/
2. Download **Python 3.10 or higher**
3. Run installer
4. ⚠️ **CHECK THIS BOX:** "Add Python to PATH"
5. Click "Install Now"
6. Wait for finish

**Verify it worked:**
```bash
python --version
# Should show: Python 3.10.x or higher
```

✅ **DONE!**

---

## ✅ Step 5: Install VS Code (5 mins)

VS Code = Text editor where you'll see the code.

**Check if already installed:**
- Windows: Look in Start Menu
- Mac: Look in Applications
- Linux: Run `code --version`

**If NOT installed:**
1. Go to https://code.visualstudio.com
2. Click big blue "Download" button
3. Run installer
4. Click "Install"

✅ **DONE!**

---

## ✅ Step 6: Clone This Repository (2 mins)

**In your terminal/command prompt:**

```bash
# Go to a folder where you want the project
cd Desktop  # or any folder you choose

# Clone the repo
git clone https://github.com/Akhilreddy33/crypto-trading-bots.git

# Go into the folder
cd crypto-trading-bots
```

✅ **DONE!** You now have all the code files.

---

## ✅ Step 7: Create Python Virtual Environment (2 mins)

Virtual environment = Isolated Python space (IMPORTANT!)

**DO THIS:**
```bash
# You should be in crypto-trading-bots folder

# Create virtual environment
python -m venv venv

# Activate it:
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate
```

**How to know it worked:** Terminal shows `(venv)` at the start

```bash
(venv) C:\Users\YourName\Desktop\crypto-trading-bots>
```

✅ **DONE!**

---

## ✅ Step 8: Install All Dependencies (3 mins)

Dependencies = All the Python libraries needed.

**DO THIS:**
```bash
# Should have (venv) showing in terminal

pip install -r requirements.txt

# This downloads and installs everything
# Wait 2-3 minutes...
# You'll see lots of text downloading packages
```

**When done, you'll see:** `Successfully installed xxxxxx packages`

✅ **DONE!**

---

## ✅ Step 9: Create .env File (2 mins)

`.env` = Your secret file with all API keys (DON'T SHARE!)

**DO THIS:**

1. In VS Code, open the `crypto-trading-bots` folder
2. Right-click in file explorer
3. Click "New File"
4. Name it: `.env` (exactly)
5. Copy-paste this:

```env
# ============================================
# CRYPTO TRADING BOTS - YOUR CREDENTIALS
# ============================================

# From Step 1 (Groq)
GROQ_API_KEY=your_groq_key_here_gsk_xxxxx

# From Step 2 (Binance Testnet)
BINANCE_TESTNET_API_KEY=your_binance_api_key_here
BINANCE_TESTNET_API_SECRET=your_binance_api_secret_here

# From Step 3 (Reddit)
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=CryptoBot/1.0

# Bot Settings
TRADING_MODE=testnet
STARTING_BALANCE=1000
TRADE_SIZE=100

# Coins to Trade
COINS=BTC,ETH,SOL,BNB,ADA,DOGE,MATIC,AVAX,DOT,LINK
```

**Now REPLACE with your actual keys:**
- Replace `your_groq_key_here_gsk_xxxxx` with your actual Groq key
- Replace `your_binance_api_key_here` with your Binance Testnet API Key
- Replace `your_binance_api_secret_here` with your Binance Testnet Secret
- Replace `your_reddit_client_id_here` with your Reddit Client ID
- Replace `your_reddit_client_secret_here` with your Reddit Client Secret

**Example (FAKE VALUES):**
```env
GROQ_API_KEY=gsk_c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9
BINANCE_TESTNET_API_KEY=abcd1234efgh5678ijkl9012mnop3456
BINANCE_TESTNET_API_SECRET=zyxw9876vuts5432rqpo1234mlkj8765
REDDIT_CLIENT_ID=aBcDeFgHiJkLmNoP
REDDIT_CLIENT_SECRET=qRsTuVwXyZ_123456789_ABCDEFGH
REDDIT_USER_AGENT=CryptoBot/1.0
TRADING_MODE=testnet
STARTING_BALANCE=1000
TRADE_SIZE=100
COINS=BTC,ETH,SOL,BNB,ADA,DOGE,MATIC,AVAX,DOT,LINK
```

✅ **DONE!** Save the file (Ctrl+S)

---

## ✅ Step 10: Test Everything Works (2 mins)

**In terminal, run:**

```bash
# You should still have (venv) showing

python -c "import dotenv; import groq; import binance; print('✅ All imports work!')"
```

**If you see:** `✅ All imports work!`
→ **PHASE 1 IS COMPLETE!** 🎉

**If you see errors:**
- Make sure `.env` is in the right folder
- Make sure all packages installed (check Step 8)
- Try: `pip install -r requirements.txt` again

---

## 🎉 PHASE 1 COMPLETE!

You now have:
✅ All API keys
✅ Python installed
✅ Virtual environment
✅ All packages installed
✅ `.env` configured
✅ Project ready to go

---

## 🚀 NEXT: PHASE 2

Once you see this message: `✅ All imports work!`

**Tell me and I'll build Bot 1!** 🤖

The first bot will:
- Fetch live BTC/ETH prices
- Calculate technical indicators (RSI, MACD, EMA)
- Ask Groq AI if signal is real
- Place test trades on Binance Testnet

---

## 💡 Pro Tips

1. **Keep `.env` SECRET** - Never upload to GitHub!
2. **Use testnet first** - Practice with fake money!
3. **Start small** - Only $50 real money first!
4. **Track everything** - Logs show every decision!

---

**Ready? Let me know when you're done with all 10 steps!** ✨🚀

