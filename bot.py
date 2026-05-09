import os
import logging
import asyncio
from telegram import Update, constants
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from image_generator import generate_image

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Rate limiting dictionary
user_cooldowns = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 *Welcome to SLMAs_bot!*\n\n"
        "I am your AI artist. Send me a descriptive text prompt, "
        "and I will transform it into a unique image using OpenAI.\n\n"
        "✨ *How to use:* Just type what you want to see!\n"
        "Example: `A futuristic city in the clouds at sunset`"
    )
    await update.message.reply_text(welcome_text, parse_mode=constants.ParseMode.MARKDOWN)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎨 *SLMAs_bot Help*\n\n"
        "• Send a text message to generate an image.\n"
        "• Be descriptive for better results.\n"
        "• Size defaults to 1024x1024.\n\n"
        "⚠️ Please avoid generating sensitive or prohibited content."
    )
    await update.message.reply_text(help_text, parse_mode=constants.ParseMode.MARKDOWN)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    prompt = update.message.text

    # Validation
    if not prompt or len(prompt) < 5:
        await update.message.reply_text("❌ Please provide a longer, more descriptive prompt.")
        return

    # Basic Rate Limiting (10 second cooldown)
    current_time = asyncio.get_event_loop().time()
    if user_id in user_cooldowns and current_time - user_cooldowns[user_id] < 10:
        await update.message.reply_text("⏳ Please wait a moment before generating another image.")
        return
    
    user_cooldowns[user_id] = current_time

    # Processing Message
    status_msg = await update.message.reply_text("🎨 *Creating your image...* Please wait.", parse_mode=constants.ParseMode.MARKDOWN)

    try:
        # Generate Image
        image_url = await generate_image(prompt)

        if image_url:
            # Send the image
            await update.message.reply_photo(
                photo=image_url,
                caption=f"✅ *Your AI image is ready!*\n\n_Prompt: {prompt}_",
                parse_mode=constants.ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("❌ Sorry, I couldn't generate that image. The prompt might have triggered safety filters.")
    
    except Exception as e:
        logging.error(f"Error in handle_message: {e}")
        await update.message.reply_text("⚠️ An unexpected error occurred. Please try again later.")
    
    finally:
        # Remove the "Creating..." message
        await status_msg.delete()

if __name__ == '__main__':
    # Get tokens from Environment Variables
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN not found in environment variables.")
        exit(1)

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("SLMAs_bot is running...")
    application.run_polling()
