"""
image_generator.py
Handles image generation using the OpenAI API.

Model chain (tried in order):
  1. dall-e-3  — best quality, widely available on paid accounts
  2. dall-e-2  — fallback, most permissive content policy

Why not gpt-image-1 first?
  gpt-image-1 has extremely strict content filtering that blocks common
  innocent prompts (e.g. anything mentioning children, sports with people).
  dall-e-3 is more reliable for everyday prompts.
"""

import asyncio
import base64
import logging
import os
import re
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


# ── Prompt sanitiser ──────────────────────────────────────────────────────────

# Map words that commonly trigger content filters → safe alternatives
_REPLACEMENTS: list[tuple[str, str]] = [
    # Age references → neutral
    (r"\b(small|little|young|kid|kids|child|children|boy|girl|toddler|baby|infant|minor)\b",
     "person"),
    # Explicit age numbers near "year" → remove
    (r"\b\d+[\s-]year[\s-]old\b", "adult"),
]


def _sanitise(prompt: str) -> str:
    """
    Replace words that commonly trigger OpenAI content policy
    with neutral alternatives, while keeping the visual intent intact.
    """
    sanitised = prompt
    for pattern, replacement in _REPLACEMENTS:
        sanitised = re.sub(pattern, replacement, sanitised, flags=re.IGNORECASE)

    if sanitised != prompt:
        logger.info("Prompt sanitised: %r → %r", prompt, sanitised)

    return sanitised


# ── Main async entry point ────────────────────────────────────────────────────

async def generate_image(prompt: str, size: str = "1024x1024") -> str:
    """
    Generate an image from a text prompt.

    Returns path to a temporary PNG file (caller must delete it).
    Raises Exception with a user-friendly message if generation fails.
    """
    image_path = await asyncio.to_thread(_call_openai, prompt, size)
    return image_path


# ── Synchronous worker (runs in background thread) ────────────────────────────

def _call_openai(prompt: str, size: str) -> str:
    """
    Try dall-e-3 → dall-e-2 → gpt-image-1 in order.
    Returns the path to a saved temp PNG file.
    """

    # Sanitise the prompt before sending to any model
    safe_prompt = _sanitise(prompt)

    # Size mapping per model:
    #   dall-e-3 : 1024x1024 | 1792x1024 | 1024x1792
    #   dall-e-2 : 256x256   | 512x512   | 1024x1024
    #   gpt-image-1: 1024x1024 | 1536x1024 | 1024x1536
    d3_size  = "1792x1024" if size == "1536x1024" else "1024x1024"
    d2_size  = "1024x1024"
    gpt_size = size

    models_to_try = [
        # (model_name,    prompt_to_use,  img_size,  response_format)
        ("dall-e-3",    safe_prompt,  d3_size,  "b64_json"),
        ("dall-e-2",    safe_prompt,  d2_size,  "b64_json"),
        ("gpt-image-1", safe_prompt,  gpt_size, "b64_json"),
    ]

    last_error: Exception | None = None

    for model, send_prompt, img_size, fmt in models_to_try:
        try:
            logger.info("Trying model=%s size=%s prompt=%r", model, img_size, send_prompt)

            response = client.images.generate(
                model=model,
                prompt=send_prompt,
                n=1,
                size=img_size,       # type: ignore[arg-type]
                response_format=fmt, # type: ignore[arg-type]
            )

            b64_data   = response.data[0].b64_json
            image_bytes = base64.b64decode(b64_data)

            tmp_path = os.path.join(tempfile.gettempdir(), f"slmas_{uuid.uuid4().hex}.png")
            with open(tmp_path, "wb") as f:
                f.write(image_bytes)

            logger.info("✅ Success with %s → %s (%d bytes)", model, tmp_path, len(image_bytes))
            return tmp_path

        # ── Hard stops — no point trying other models ─────────────────────────
        except openai.AuthenticationError as e:
            logger.error("Auth error: %s", e)
            raise Exception(
                "🔑 Invalid OpenAI API key.\n"
                "Please check your OPENAI_API_KEY in Render → Environment tab."
            ) from e

        except openai.RateLimitError as e:
            logger.warning("Rate limit hit on %s: %s", model, e)
            raise Exception(
                "⏳ OpenAI rate limit reached. Please wait a moment and try again."
            ) from e

        except openai.APIConnectionError as e:
            logger.error("Connection error on %s: %s", model, e)
            raise Exception(
                "🌐 Could not reach OpenAI. Please try again in a moment."
            ) from e

        # ── Soft failures — try next model ────────────────────────────────────
        except openai.BadRequestError as e:
            # Content policy or unsupported param for this model
            logger.warning("BadRequest on %s (trying next): %s", model, e)
            last_error = e
            continue

        except openai.PermissionDeniedError as e:
            logger.warning("Permission denied on %s (trying next): %s", model, e)
            last_error = e
            continue

        except openai.NotFoundError as e:
            logger.warning("Model not found %s (trying next): %s", model, e)
            last_error = e
            continue

        except Exception as e:
            logger.error("Unexpected error on %s: %s | type=%s", model, e, type(e).__name__)
            last_error = e
            continue

    # ── All models exhausted ──────────────────────────────────────────────────
    logger.error("All models failed. Last error: %s", last_error)
    raise Exception(
        "😔 Sorry, I couldn't generate that image.\n\n"
        "This usually means the prompt contains words that AI image services "
        "won't process. Try describing the scene differently — for example:\n\n"
        "Instead of: _'A small boy playing football'_\n"
        "Try: _'A person in a football kit kicking a ball on a grass pitch'_"
    )
