"""
image_generator.py
Handles image generation using the OpenAI API (gpt-image-1).
Returns the path to a temporary PNG file.
"""

import asyncio
import base64
import logging
import os
import tempfile
import uuid

import openai

logger = logging.getLogger(__name__)

# Read the OpenAI API key from environment
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY environment variable is missing!")

# Create the OpenAI client once (reused for all requests)
client = openai.OpenAI(api_key=OPENAI_API_KEY)


async def generate_image(prompt: str, size: str = "1024x1024") -> str:
    """
    Generate an image from a text prompt using OpenAI's gpt-image-1 model.

    Parameters
    ----------
    prompt : str  — what to generate
    size   : str  — '1024x1024' or '1536x1024'

    Returns
    -------
    str — path to a temporary PNG file (caller must delete it)

    Raises
    ------
    Exception — if generation fails (caller handles this)
    """

    # Run the blocking OpenAI call in a thread so the async bot stays responsive
    image_path = await asyncio.to_thread(_call_openai, prompt, size)
    return image_path


def _call_openai(prompt: str, size: str) -> str:
    """
    Synchronous OpenAI API call — runs in a background thread via asyncio.to_thread.
    Returns path to temp PNG file.
    """
    logger.info("Calling OpenAI API | model=gpt-image-1 | size=%s", size)

    try:
        response = client.images.generate(
            model="gpt-image-1",
            prompt=prompt,
            n=1,
            size=size,                 # type: ignore[arg-type]
            response_format="b64_json",
        )
    except openai.BadRequestError as e:
        logger.warning("OpenAI rejected prompt: %s", e)
        raise Exception(
            "Your prompt was rejected by the content policy. "
            "Please try a different description."
        ) from e
    except openai.RateLimitError as e:
        logger.warning("OpenAI rate limit: %s", e)
        raise Exception("The image service is busy right now. Please try again in a moment.") from e
    except openai.AuthenticationError as e:
        logger.error("OpenAI auth failed: %s", e)
        raise Exception("API key error. Please contact the bot admin.") from e
    except openai.APIConnectionError as e:
        logger.error("OpenAI connection error: %s", e)
        raise Exception("Could not connect to the image service. Please try again.") from e
    except Exception as e:
        logger.error("Unexpected OpenAI error: %s", e)
        raise Exception("Image generation failed. Please try again.") from e

    # Decode the base64 image data
    try:
        b64_data = response.data[0].b64_json
        image_bytes = base64.b64decode(b64_data)
    except Exception as e:
        logger.error("Failed to decode image response: %s", e)
        raise Exception("Received an invalid response from the image service.") from e

    # Save to a temp file — caller is responsible for deleting it
    tmp_path = os.path.join(tempfile.gettempdir(), f"slmas_{uuid.uuid4().hex}.png")
    with open(tmp_path, "wb") as f:
        f.write(image_bytes)

    logger.info("Image saved to %s (%d bytes)", tmp_path, len(image_bytes))
    return tmp_path
