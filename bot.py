"""
SLMAs_bot — Telegram AI Image Generator
Uses python-telegram-bot v20+ with polling (no webhooks)
"""

import logging
import os

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from image_generator import generate_image

# ── Logging setup ─────────────────────────────────────────────────────────────
# This prints timestamped logs to Render's log viewer
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ── Read environment variables ────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing!")


# ── /start command ────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message when user types /start."""
    await update.message.reply_text(
        "👋 Welcome to SLMAs Bot!\n\n"
        "Send me any text prompt and I will generate an AI image for you 🎨\n\n"
        "Example:\n"
        "\"A futuristic city at sunset\"\n\n"
        "Type /help to learn more."
    )


# ── /help command ────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message when user types /help."""
    await update.message.reply_text(
        "🆘 *How to use SLMAs Bot:*\n\n"
        "1. Simply type any description of an image\n"
        "2. Wait a few seconds while I generate it\n"
        "3. Receive your AI-generated image!\n\n"
        "*Size options (add to end of prompt):*\n"
        "• `--landscape` → wide image (1536×1024)\n"
        "• `--square` → square image (1024×1024, default)\n\n"
        "*Examples:*\n"
        "• `A golden retriever on a beach`\n"
        "• `Cyberpunk street market at night --landscape`\n\n"
        "⚠️ Be descriptive for best results!",
        parse_mode="Markdown",
    )


# ── Text message handler (image generation) ───────────────────────────────────
async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Receive a text prompt, generate an image, and send it back."""
    prompt = (update.message.text or "").strip()

    # Ignore empty messages
    if not prompt:
        await update.message.reply_text("⚠️ Please send a text description to generate an image.")
        return

    # ── Parse optional size flag ──────────────────────────────────────────────
    size = "1024x1024"  # default

    if prompt.endswith("--landscape"):
        size = "1536x1024"
        prompt = prompt[: -len("--landscape")].strip()
    elif prompt.endswith("--square"):
        prompt = prompt[: -len("--square")].strip()

    if not prompt:
        await update.message.reply_text("⚠️ Please include a description with your size flag.")
        return

    # ── Send "processing" message ─────────────────────────────────────────────
    processing_msg = await update.message.reply_text("🎨 Generating your image... Please wait.")

    # Show upload indicator in chat
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.UPLOAD_PHOTO,
    )

    # ── Generate image ────────────────────────────────────────────────────────
    image_path = None
    try:
        logger.info("Generating image | size=%s | prompt=%r", size, prompt)
        image_path = await generate_image(prompt, size)

        with open(image_path, "rb") as img:
            await update.message.reply_photo(
                photo=img,
                caption=f"🎨 Here is your image!\n\n📝 _{prompt}_",
                parse_mode="Markdown",
            )

        logger.info("Image sent successfully to user %s", update.effective_user.id)

    except Exception as e:
        logger.error("Failed to generate image: %s | type=%s", e, type(e).__name__)
        # Show the real error so the user knows exactly what went wrong
        await update.message.reply_text(f"❌ {e}")

    finally:
        # Always delete the "Generating…" message
        try:
            await processing_msg.delete()
        except Exception:
            pass

        # Always clean up the temp file
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                pass


# ── Ignore non-text messages ──────────────────────────────────────────────────
async def ignore_non_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tell the user this bot only handles text prompts."""
    await update.message.reply_text(
        "ℹ️ I only accept text prompts. Please type a description to generate an image."
    )


# ── Main entry point ──────────────────────────────────────────────────────────
def main() -> None:
    logger.info("Starting SLMAs_bot...")

    # Build the Application
    app = Application.builder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_command))

    # Register text message handler (excludes commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))

    # Ignore photos, videos, stickers, documents, etc.
    app.add_handler(MessageHandler(~filters.TEXT, ignore_non_text))

    logger.info("Bot is running with polling...")

    # Start polling — this blocks forever (perfect for Render background worker)
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,   # ignore messages sent while bot was offline
    )


if __name__ == "__main__":
    main()
