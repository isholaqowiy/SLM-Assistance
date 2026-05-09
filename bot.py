"""
SLMAs_bot — Telegram AI Image Generation Bot
Main bot entry point using python-telegram-bot v20+
"""

import asyncio
import logging
import os
import time
from collections import defaultdict

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from image_generator import generate_image, ImageGenerationError

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Rate limiting: max requests per user per window
RATE_LIMIT_REQUESTS = 5          # max images
RATE_LIMIT_WINDOW   = 60         # seconds

# Simple in-memory rate-limit store  {user_id: [timestamp, ...]}
_rate_store: dict[int, list[float]] = defaultdict(list)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _check_rate_limit(user_id: int) -> tuple[bool, int]:
    """Return (allowed, seconds_until_reset)."""
    now = time.monotonic()
    window_start = now - RATE_LIMIT_WINDOW
    timestamps = [t for t in _rate_store[user_id] if t > window_start]
    _rate_store[user_id] = timestamps

    if len(timestamps) >= RATE_LIMIT_REQUESTS:
        reset_in = int(RATE_LIMIT_WINDOW - (now - timestamps[0])) + 1
        return False, reset_in

    _rate_store[user_id].append(now)
    return True, 0


# ─── Command Handlers ─────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send welcome message."""
    user_first = update.effective_user.first_name or "there"
    await update.message.reply_text(
        f"👋 Hello, {user_first}!\n\n"
        "Welcome to *SLMAs_bot* — your personal AI image generator.\n\n"
        "✨ *What I can do:*\n"
        "Simply send me any text description and I'll turn it into a stunning AI-generated image in seconds.\n\n"
        "📐 *Supported sizes:*\n"
        "• `1024x1024` — Square _(default)_\n"
        "• `1536x1024` — Landscape\n\n"
        "🖼 *Try something like:*\n"
        "_\"A futuristic city at sunset with neon reflections on wet streets\"_\n\n"
        "Type /help for full usage instructions.\n"
        "Ready when you are — just send your prompt! 🚀",
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send help message."""
    await update.message.reply_text(
        "📖 *How to use SLMAs_bot*\n\n"
        "*Basic usage:*\n"
        "Just type any text description and send it. The bot will generate an image.\n\n"
        "*Choosing image size:*\n"
        "Add a size flag at the end of your prompt:\n"
        "• `--square` or `-s` → 1024×1024 _(default)_\n"
        "• `--landscape` or `-l` → 1536×1024\n\n"
        "*Examples:*\n"
        "• `A golden retriever surfing on a wave`\n"
        "• `Medieval castle in the mountains --landscape`\n"
        "• `Abstract watercolor painting of jazz musicians -s`\n\n"
        "*Rate limit:*\n"
        f"• Up to {RATE_LIMIT_REQUESTS} images per {RATE_LIMIT_WINDOW} seconds per user.\n\n"
        "*Commands:*\n"
        "/start — Welcome message\n"
        "/help — This help page\n\n"
        "💡 _Tip: The more detailed your prompt, the better the result!_",
        parse_mode="Markdown",
    )


# ─── Image Generation Handler ─────────────────────────────────────────────────

async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user text prompts and generate images."""
    user    = update.effective_user
    message = update.message
    text    = (message.text or "").strip()

    # Guard: empty prompt
    if not text:
        await message.reply_text(
            "⚠️ Please send a non-empty text prompt so I can generate an image for you."
        )
        return

    # ── Parse size flag ──────────────────────────────────────────────────────
    size = "1024x1024"  # default

    if text.endswith(("--landscape", "-l")):
        size = "1536x1024"
        text = text.rsplit(None, 1)[0].strip()
    elif text.endswith(("--square", "-s")):
        size = "1024x1024"
        text = text.rsplit(None, 1)[0].strip()

    # Guard: prompt became empty after stripping flags
    if not text:
        await message.reply_text(
            "⚠️ Your prompt is empty after removing the size flag. "
            "Please describe what you'd like me to generate."
        )
        return

    # ── Rate limiting ─────────────────────────────────────────────────────────
    allowed, reset_in = _check_rate_limit(user.id)
    if not allowed:
        await message.reply_text(
            f"⏳ *Slow down!* You've reached the limit of {RATE_LIMIT_REQUESTS} images "
            f"per {RATE_LIMIT_WINDOW} seconds.\n\n"
            f"Please try again in *{reset_in} seconds*.",
            parse_mode="Markdown",
        )
        return

    # ── Processing message ────────────────────────────────────────────────────
    logger.info("User %s (%d) requested image | size=%s | prompt=%r", user.username, user.id, size, text)
    processing_msg = await message.reply_text(
        "🎨 *Creating your image…* Please wait a moment.",
        parse_mode="Markdown",
    )

    # Show typing indicator while we work
    await context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.UPLOAD_PHOTO)

    # ── Generate image ────────────────────────────────────────────────────────
    image_path: str | None = None
    try:
        image_path = await asyncio.to_thread(generate_image, text, size)

        with open(image_path, "rb") as img_file:
            await message.reply_photo(
                photo=img_file,
                caption=(
                    "🎨 *Your AI image is ready!*\n\n"
                    f"📝 Prompt: _{text}_\n"
                    f"📐 Size: `{size}`"
                ),
                parse_mode="Markdown",
            )

        logger.info("Image delivered to user %d", user.id)

    except ImageGenerationError as exc:
        logger.warning("ImageGenerationError for user %d: %s", user.id, exc)
        await message.reply_text(
            f"❌ *Image generation failed.*\n\n{exc}\n\n"
            "Please try rephrasing your prompt or try again later.",
            parse_mode="Markdown",
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception("Unexpected error for user %d: %s", user.id, exc)
        await message.reply_text(
            "⚠️ An unexpected error occurred while generating your image. "
            "Please try again in a moment.",
        )

    finally:
        # Delete the "processing…" message
        try:
            await processing_msg.delete()
        except Exception:
            pass

        # Clean up temp file
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
                logger.debug("Removed temp file: %s", image_path)
            except OSError as exc:
                logger.warning("Could not remove temp file %s: %s", image_path, exc)


# ─── Error Handler ────────────────────────────────────────────────────────────

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Unhandled exception", exc_info=context.error)


# ─── Entry Point ──────────────────────────────────────────────────────────────

def main() -> None:
    logger.info("Starting SLMAs_bot…")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help",  help_command))

    # Text prompts (exclude commands)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_prompt))

    # Global error handler
    app.add_error_handler(error_handler)

    logger.info("Bot is polling for updates…")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
