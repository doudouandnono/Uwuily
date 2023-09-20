from io import BytesIO

import aiofiles
import discord
from PIL import Image

image_cache = {}


async def open_image(image_path: str) -> Image.Image:
    async with aiofiles.open(image_path, mode="rb") as f:
        data = await f.read()
        image = Image.open(BytesIO(data))
    return image


async def get_image(image_path: str) -> Image.Image:
    if image_path not in image_cache:
        image_cache[image_path] = await open_image(image_path)
    return image_cache[image_path].copy()


def buffer_bytes(image: Image.Image) -> discord.File:
    buffer = BytesIO()
    image.save(fp=buffer, format="webp")
    buffer.seek(0)
    image_file = discord.File(fp=buffer, filename="image.webp")
    return image_file
