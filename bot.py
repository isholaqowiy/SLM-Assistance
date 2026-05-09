import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update, constants
from telegram.ext import (
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    MessageHandler, 
    filters
)
from image_generator import generate_image

# Load environment variables (Critical for Render/Local dev)
load_dotenv()

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Simple in-memory rate limiting
user_cooldowns = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a professional welcome message."""
    welcome_text = (
        "🎨 *Welcome to SLMAs_bot!*\n\n"
        "I am a high-performance AI image generator. Send me a descriptive "
        "text prompt, and I will create an image for you using OpenAI.\n\n"
        "✨ *Quick Start:* Just type a prompt like:\n"
        "`A cyberpunk samurai in neon-lit Tokyo`"
    )
    await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Explains how to use the bot."""
    help_text = (
        "📖 *How to use SLMAs_bot*\n\n"
        "1️⃣ Send any descriptive text prompt.\n"
        "2️⃣ Wait about 10-15 seconds for AI generation.\n"
        "3️⃣ Receive your high-resolution image.\n\n"
        "💡 *Tips:* More details lead to better images. Mention lighting, "
        "art style (e.g., 'oil painting', '3D render'), and colors."
    )
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles text prompts and triggers image generation."""
    user = update.effective_user
    prompt = update.message.text

    # 1. Validation: Prevent empty or very short prompts
    if not prompt or len(prompt) < 3:
        await update.message.reply_text("⚠️ Your prompt is too short. Please describe the image you want in more detail.")
        return

    # 2. Rate Limiting: 10-second cooldown per user
    current_time = asyncio.get_event_loop().time()
    if user.id in user_cooldowns:
        elapsed = current_time - user_cooldowns[user.id]
        if elapsed < 10:
            await update.message.reply_text(f"⏳ Slow down! Please wait {int(10 - elapsed)}s.")
            return
    
    user_cooldowns[user.id] = current_time

    # 3. Send Processing Message
    status_msg = await update.message.reply_text("🎨 *Creating your image...* Please wait.", parse_mode=constants.ParseMode.MARKDOWN)

    try:
        # 4. Generate the Image via OpenAI
        image_url = await generate_image(prompt)

        if image_url:
            # 5. Send the Image back
            await update.message.reply_photo(
                photo=image_url,
                caption=f"✨ *Your AI image is ready!*\n\n_Prompt: {prompt}_",
                parse_mode=constants.ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Failed to generate image. This usually happens if the prompt violates safety policies or the API key is invalid.")
    
    except Exception as e:
        logger.error(f"Error for user {user.id}: {e}")
        await update.message.reply_text("⚠️ An error occurred during generation. Please try again later.")
    
    finally:
        # 6. Cleanup: Delete the "Creating..." status message
        try:
            await status_msg.delete()
        except:
            pass

if __name__ == '__main__':
    # Retrieve tokens from Environment
    TOKEN = os.getenv("BOT_TOKEN")
    
    if not TOKEN:
        logger.error("CRITICAL: BOT_TOKEN environment variable is missing!")
        exit(1)

    # Build the Application
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Register Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    # Startup log message
    print("--------------------------")
    print("SLMAs_bot is now ONLINE")
    print("Press Ctrl+C to stop")
    print("--------------------------")
    
    # Run the bot using Polling
    application.run_polling()
