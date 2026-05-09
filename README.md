# 🤖 SLMAs_bot — AI Image Generator

A Telegram bot that turns any text prompt into an AI-generated image using OpenAI's `gpt-image-1` model.

---

## 📁 Project Files

```
SLMAs_bot/
├── bot.py               # Main bot (handlers, polling)
├── image_generator.py   # OpenAI image generation
├── requirements.txt     # Dependencies
├── runtime.txt          # Python version for Render
└── README.md            # This file
```

---

## 🚀 Render Deployment — Step by Step

### Step 1 — Upload to GitHub

1. Go to [github.com](https://github.com) → **New repository**
2. Name it `slmas-bot`, set it to **Public**, click **Create repository**
3. Upload all 5 files (`bot.py`, `image_generator.py`, `requirements.txt`, `runtime.txt`, `README.md`):
   - Click **Add file → Upload files**
   - Drag and drop all files
   - Click **Commit changes**

---

### Step 2 — Create a Background Worker on Render

1. Go to [render.com](https://render.com) → Log in → Click **New +**
2. Select **Background Worker**
3. Click **Connect a repository** → authorize GitHub if prompted
4. Select your `slmas-bot` repository → click **Connect**

---

### Step 3 — Configure the Worker

| Field | Value |
|---|---|
| **Name** | `slmas-bot` |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Instance Type** | `Free` |

---

### Step 4 — Add Environment Variables

Still on the setup page, scroll to **Environment Variables** and add:

| Key | Value |
|---|---|
| `BOT_TOKEN` | Your token from [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | Your key from [platform.openai.com](https://platform.openai.com/api-keys) |

> ⚠️ Never put your keys directly in code or commit them to GitHub.

---

### Step 5 — Deploy

Click **Create Background Worker**.

Render will install dependencies and start the bot. In the **Logs** tab you should see:

```
Starting SLMAs_bot...
Bot is running with polling...
```

Open Telegram, find your bot, and send `/start`. It should respond immediately. ✅

---

## 💬 How to Use the Bot

| Action | How |
|---|---|
| Generate a square image | Just type your prompt and send |
| Generate a landscape image | Add `--landscape` at the end |
| Get help | Send `/help` |

**Examples:**
```
A dragon flying over a volcano
A cozy coffee shop in Paris --landscape
Portrait of an astronaut on Mars
```

---

## 🔑 Getting Your Credentials

### Telegram Bot Token
1. Open [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the steps
3. Copy the token (looks like `123456789:ABCdef...`)

### OpenAI API Key
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key**
3. Copy the key (looks like `sk-proj-...`)

> Note: `gpt-image-1` requires a paid OpenAI account with available credits.

---

## 🛠 Local Development

```bash
# Clone your repo
git clone https://github.com/YOUR_USERNAME/slmas-bot.git
cd slmas-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN="your_telegram_token"
export OPENAI_API_KEY="your_openai_key"

# Run
python bot.py
```

---

## ❓ Troubleshooting

| Problem | Fix |
|---|---|
| Bot doesn't respond | Check `BOT_TOKEN` is correct in Render → Environment tab |
| "API key error" message | Check `OPENAI_API_KEY` is set and valid |
| Image generation fails | Rephrase your prompt; avoid policy-violating content |
| Build fails | Check Render logs; make sure `runtime.txt` says `python-3.11.9` |
| Bot was working, now stopped | Check Render free plan sleep — redeploy if needed |

Check Render's **Logs** tab first — errors are always shown there.
