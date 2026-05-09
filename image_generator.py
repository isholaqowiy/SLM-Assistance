"""
image_generator.py
Handles all OpenAI image generation logic for SLMAs_bot.
"""

import base64
import logging
import os
import tempfile
import uuid

from openai import OpenAI, APIError, APIConnectionError, RateLimitError, APIStatusError

logger = logging.getLogger(__name__)

# ─── OpenAI client (singleton) ────────────────────────────────────────────────
_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY environment variable is not set.")
        _client = OpenAI(api_key=api_key)
    return _client


# ─── Custom exception ─────────────────────────────────────────────────────────

class ImageGenerationError(Exception):
    """Raised when image generation fails in a known, handleable way."""


# ─── Supported sizes ──────────────────────────────────────────────────────────

SUPPORTED_SIZES = {"1024x1024", "1536x1024"}

DEFAULT_SIZE = "1024x1024"


# ─── Core function ────────────────────────────────────────────────────────────

def generate_image(prompt: str, size: str = DEFAULT_SIZE) -> str:
    """
    Generate an image from *prompt* using OpenAI's gpt-image-1 model.

    Parameters
    ----------
    prompt : str
        The text description of the image to create.
    size : str
        One of the SUPPORTED_SIZES. Defaults to '1024x1024'.

    Returns
    -------
    str
        Absolute path to a temporary PNG file containing the image.
        The caller is responsible for deleting it after use.

    Raises
    ------
    ImageGenerationError
        For known, user-facing errors (bad prompt, content policy, quota, etc.)
    """

    if not prompt or not prompt.strip():
        raise ImageGenerationError("Prompt cannot be empty.")

    if size not in SUPPORTED_SIZES:
        logger.warning("Unsupported size %r — falling back to %s", size, DEFAULT_SIZE)
        size = DEFAULT_SIZE

    client = _get_client()

    logger.info("Calling OpenAI image API | model=gpt-image-1 | size=%s", size)

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt.strip(),
            n=1,
            size=size,              # type: ignore[arg-type]
            response_format="b64_json",
        )

    except RateLimitError as exc:
        logger.warning("OpenAI rate limit hit: %s", exc)
        raise ImageGenerationError(
            "🚦 The image service is currently busy. Please wait a moment and try again."
        ) from exc

    except APIConnectionError as exc:
        logger.error("OpenAI connection error: %s", exc)
        raise ImageGenerationError(
            "🌐 Could not reach the image generation service. Check your connection and try again."
        ) from exc

    except APIStatusError as exc:
        logger.error("OpenAI API status error %d: %s", exc.status_code, exc.message)
        if exc.status_code == 400:
            raise ImageGenerationError(
                "⛔ Your prompt was rejected by the content policy. "
                "Please rephrase it and try again."
            ) from exc
        if exc.status_code in (401, 403):
            raise ImageGenerationError(
                "🔑 Authentication failed. Please contact the bot administrator."
            ) from exc
        raise ImageGenerationError(
            f"The image service returned an error (HTTP {exc.status_code}). "
            "Please try again later."
        ) from exc

    except APIError as exc:
        logger.error("Generic OpenAI API error: %s", exc)
        raise ImageGenerationError(
            "⚠️ An error occurred with the image service. Please try again later."
        ) from exc

    # ── Decode and save to temp file ──────────────────────────────────────────
    try:
        image_data = response.data[0].b64_json
        if not image_data:
            raise ImageGenerationError("Received an empty image response from OpenAI.")

        image_bytes = base64.b64decode(image_data)
    except (IndexError, KeyError, ValueError) as exc:
        logger.error("Failed to decode OpenAI response: %s", exc)
        raise ImageGenerationError(
            "Received an unexpected response format from the image service."
        ) from exc

    # Write to a uniquely-named temp file (caller must delete)
    suffix = f"_{uuid.uuid4().hex}.png"
    tmp_dir = tempfile.gettempdir()
    tmp_path = os.path.join(tmp_dir, f"slmas{suffix}")

    try:
        with open(tmp_path, "wb") as f:
            f.write(image_bytes)
    except OSError as exc:
        logger.error("Failed to write temp image file: %s", exc)
        raise ImageGenerationError(
            "Could not save the generated image temporarily. Please try again."
        ) from exc

    logger.info("Image saved to temp file: %s (%d bytes)", tmp_path, len(image_bytes))
    return tmp_path
