# 🤖 SLMAs_bot — AI Image Generator Telegram Bot

A production-ready Telegram bot that generates AI images from text prompts using OpenAI's `gpt-image-1` model.

---

## ✨ Features

- 🎨 AI image generation from any text description
- 📐 Two image sizes: Square (`1024×1024`) and Landscape (`1536×1024`)
- ⏱ Rate limiting (5 images per 60 seconds per user)
- 🧹 Automatic temp file cleanup
- 🛡 Graceful error handling for API failures and content policy violations
- 📋 `/start` and `/help` commands

---

## 📁 Project Structure

```
SLMAs_bot/
├── bot.py               # Main bot logic & handlers
├── image_generator.py   # OpenAI image generation module
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

---

## 🚀 Render.com Deployment Guide

### Step 1 — Prepare your GitHub Repository

1. Create a new repository on [github.com](https://github.com/new).
2. Name it something like `slmas-bot`.
3. Upload all four project files (`bot.py`, `image_generator.py`, `requirements.txt`, `README.md`) to the repository root.

   **Via GitHub web UI:**
   - Click **Add file → Upload files**
   - Drag and drop all four files
   - Click **Commit changes**

   **Via Git CLI:**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/<YOUR_USERNAME>/slmas-bot.git
   git push -u origin main
   ```

---

### Step 2 — Connect Repository to Render

1. Go to [render.com](https://render.com) and log in (or sign up — it's free).
2. Click **New +** → **Background Worker**.
3. Choose **Build and deploy from a Git repository** and click **Next**.
4. Click **Connect GitHub** and authorize Render.
5. Find and select your `slmas-bot` repository.
6. Click **Connect**.

---

### Step 3 — Configure the Background Worker

Fill in the following settings:

| Setting | Value |
|---|---|
| **Name** | `slmas-bot` _(or any name you like)_ |
| **Region** | Choose the region closest to you |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python bot.py` |
| **Instance Type** | `Free` _(or higher for production)_ |

---

### Step 4 — Add Environment Variables

In the **Environment Variables** section (still on the setup page, or later under your service's **Environment** tab), add these two variables:

| Key | Value |
|---|---|
| `BOT_TOKEN` | Your Telegram Bot token from [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | Your OpenAI API key from [platform.openai.com](https://platform.openai.com/api-keys) |

> ⚠️ **Never** commit your API keys to GitHub. Always use environment variables.

---

### Step 5 — Deploy

1. Click **Create Background Worker**.
2. Render will automatically:
   - Clone your repository
   - Install dependencies from `requirements.txt`
   - Start the bot with `python bot.py`
3. Watch the **Logs** tab — you should see:
   ```
   Starting SLMAs_bot…
   Bot is polling for updates…
   ```
4. Open Telegram, find your bot by username, and send `/start`. 🎉

---

## 🔑 Getting Your Credentials

### Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the prompts to name your bot `SLMAs_bot`
4. Copy the token BotFather gives you — it looks like:
   ```
   123456789:ABCDefGhIJKlmNoPQRsTUVwxyZ
   ```

### OpenAI API Key
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key**
3. Copy the key — it looks like:
   ```
   sk-proj-...
   ```
   > Note: OpenAI's `gpt-image-1` model requires a paid account with sufficient credits.

---

## 💬 Bot Usage

| Action | How |
|---|---|
| Generate a square image | Just type your prompt and send |
| Generate a landscape image | Add `--landscape` or `-l` at the end |
| Generate a square explicitly | Add `--square` or `-s` at the end |
| Get help | Send `/help` |

**Examples:**
```
A futuristic city at sunset with neon lights
A mountain landscape at dawn --landscape
Portrait of a wise old wizard -s
```

---

## ⚙️ Local Development

```bash
# Clone the repo
git clone https://github.com/<YOUR_USERNAME>/slmas-bot.git
cd slmas-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export BOT_TOKEN="your_telegram_token"
export OPENAI_API_KEY="your_openai_key"

# Run
python bot.py
```

---

## 🔒 Rate Limits

- **5 images per 60 seconds** per user (configurable in `bot.py`)
- Users receive a friendly message when they hit the limit

---

## 📜 License

MIT — use freely, deploy responsibly.
