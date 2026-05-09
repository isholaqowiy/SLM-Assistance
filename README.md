# SLMAs_bot - AI Image Generator

A professional Telegram bot that generates high-quality AI images from text prompts using OpenAI's DALL-E.

## 🚀 Deployment on Render.com

Since this bot uses **Polling**, it must be deployed as a **Background Worker** on Render to ensure it stays online 24/7.

### Step 1: Prepare your Code
1. Create a private repository on **GitHub**.
2. Upload `bot.py`, `image_generator.py`, and `requirements.txt` to the repository.

### Step 2: Connect to Render
1. Log in to [Render.com](https://render.com).
2. Click **New +** and select **Background Worker**.
3. Connect your GitHub account and select the `SLMAs_bot` repository.

### Step 3: Configure Build & Start
*   **Runtime:** `Python 3`
*   **Build Command:** `pip install -r requirements.txt`
*   **Start Command:** `python bot.py`

### Step 4: Add Environment Variables
Navigate to the **Environment** tab in your Render dashboard and add:
1. `BOT_TOKEN`: Your Telegram Bot Token from @BotFather.
2. `OPENAI_API_KEY`: Your API key from OpenAI.

### Step 5: Deploy
Click **Create Background Worker**. Render will build the environment and start your bot automatically!

## 🛠 Features
- **Async Processing:** Fast responses and no crashes.
- **Error Handling:** Gracefully handles API failures and empty prompts.
- **Modern UI:** Uses Markdown for clean, readable Telegram messages.
