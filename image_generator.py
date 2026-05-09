"""
image_generator.py
Handles image generation using the OpenAI API.
Primary model: gpt-image-1
Fallback model: dall-e-3 (more widely available)
"""

import asyncio
import base64
import logging
import os
import tempfile
import uuid

import openai

logger = logging.getLogger(__name__)

# ── Read API key ──────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is missing!")

# Singleton OpenAI client
client = openai.OpenAI(api_key=OPENAI_API_KEY)


async def generate_image(prompt: str, size: str = "1024x1024") -> str:
    """
    Generate an image from a text prompt.
    Tries gpt-image-1 first, falls back to dall-e-3 if unavailable.

    Returns path to a temporary PNG file (caller must delete it).
    Raises Exception with a clear message if both models fail.
    """
    image_path = await asyncio.to_thread(_call_openai, prompt, size)
    return image_path


def _call_openai(prompt: str, size: str) -> str:
    """
    Synchronous OpenAI call — runs in a background thread.
    Tries gpt-image-1 then falls back to dall-e-3.
    """

    # dall-e-3 only supports 1024x1024, 1792x1024, 1024x1792
    # Map our size to dall-e-3 compatible size for fallback
    dalle3_size = "1792x1024" if size == "1536x1024" else "1024x1024"

    # Try gpt-image-1 first, then dall-e-3
    models_to_try = [
        ("gpt-image-1", size,        "b64_json"),
        ("dall-e-3",    dalle3_size,  "b64_json"),
    ]

    last_error = None

    for model, img_size, fmt in models_to_try:
        try:
            logger.info("Trying model=%s size=%s", model, img_size)

            response = client.images.generate(
                model=model,
                prompt=prompt,
                n=1,
                size=img_size,          # type: ignore[arg-type]
                response_format=fmt,    # type: ignore[arg-type]
            )

            # Decode the base64 image
            b64_data = response.data[0].b64_json
            image_bytes = base64.b64decode(b64_data)

            # Save to temp file
            tmp_path = os.path.join(
                tempfile.gettempdir(), f"slmas_{uuid.uuid4().hex}.png"
            )
            with open(tmp_path, "wb") as f:
                f.write(image_bytes)

            logger.info("✅ Image generated with %s → %s (%d bytes)", model, tmp_path, len(image_bytes))
            return tmp_path

        except openai.BadRequestError as e:
            # Content policy violation — no point retrying other models
            logger.warning("Content policy rejection (%s): %s", model, e)
            raise Exception(
                "⛔ Your prompt was rejected by OpenAI's content policy.\n"
                "Please rephrase it and try again."
            ) from e

        except openai.AuthenticationError as e:
            logger.error("Auth error (%s): %s", model, e)
            raise Exception(
                "🔑 Invalid OpenAI API key.\n"
                "Please check your OPENAI_API_KEY in Render's Environment settings."
            ) from e

        except openai.RateLimitError as e:
            logger.warning("Rate limit (%s): %s", model, e)
            raise Exception(
                "⏳ OpenAI rate limit reached. Please wait a moment and try again."
            ) from e

        except openai.PermissionDeniedError as e:
            # gpt-image-1 not available on this account → try next model
            logger.warning("Permission denied for %s (will try fallback): %s", model, e)
            last_error = e
            continue

        except openai.NotFoundError as e:
            # Model not found → try next model
            logger.warning("Model not found %s (will try fallback): %s", model, e)
            last_error = e
            continue

        except openai.APIConnectionError as e:
            logger.error("Connection error (%s): %s", model, e)
            raise Exception(
                "🌐 Could not connect to OpenAI. Please try again in a moment."
            ) from e

        except Exception as e:
            # Log the full real error so it appears in Render logs
            logger.error("Unexpected error with model %s: %s | type=%s", model, e, type(e).__name__)
            last_error = e
            continue

    # All models failed
    logger.error("All models failed. Last error: %s", last_error)
    raise Exception(
        f"❌ Image generation failed with all available models.\n"
        f"Last error: {type(last_error).__name__}: {last_error}\n\n"
        "Check Render logs for details, or verify your OPENAI_API_KEY has image generation access."
    )
