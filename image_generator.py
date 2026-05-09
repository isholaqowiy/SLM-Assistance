import os
from openai import AsyncOpenAI
import logging

# Initialize OpenAI Client
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def generate_image(prompt: str, size: str = "1024x1024"):
    """
    Generates an image using OpenAI DALL-E model.
    """
    try:
        response = await client.images.generate(
            model="dall-e-3", # Latest high-quality model
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        # Returns the URL of the generated image
        return response.data[0].url
    except Exception as e:
        logging.error(f"OpenAI API Error: {e}")
        return None
