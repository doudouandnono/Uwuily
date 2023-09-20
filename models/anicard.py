from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from PIL import Image, ImageDraw, ImageFont

import helpers.pillow as pillow

if t.TYPE_CHECKING:
    from datetime import datetime


@dataclass
class Anicard:
    """Anicard model."""

    anicard_id: int | None = None
    user_id: int | None = None
    minion_id: int | None = None
    tag: str | None = None
    image_ver: int | None = None
    frame: str | None = None
    obtained_ts: datetime | None = None
    is_shattered: bool | None = None
    tier: int | None = None
    aniclass: str | None = None
    codex: int | None = None
    xp: int | None = None
    spiritfuse_total: int | None = None
    is_summoned: bool | None = None
    hitpoint: int | None = None
    location: str | None = None
    activity: str | None = None
    activity_start_ts: datetime | None = None
    character: str | None = None
    anime: str | None = None
    original_aniclass: str | None = None
    current_codex: int | None = None
    ability: str | None = None
    inventory: list = field(default_factory=list)

    async def draw_anicard(self) -> Image.Image:
        def write_text_on_anicard(
            anicard_draw: ImageDraw.ImageDraw,
            text: str,
            position: tuple[int, int],
            font: ImageFont.FreeTypeFont,
            fill: tuple[int, int, int],
            stroke_width: int,
            stroke_fill: str,
        ) -> None:
            width, _ = font.getsize(text)  # type: ignore
            pos_x, pos_y = position
            text_position = (pos_x - width // 2, pos_y)
            anicard_draw.text(
                text_position,
                text,
                font=font,
                fill=fill,
                stroke_width=stroke_width,
                stroke_fill=stroke_fill,
            )

        anicard_path = f"assets/anicard/character/{self.character}_v{self.image_ver}.png"
        anicard_image: Image.Image = await pillow.get_image(image_path=anicard_path)

        if self.is_shattered:
            shattered_path = "assets/anicard/shattered.png"
            shattered_image: Image.Image = await pillow.get_image(image_path=shattered_path)
            anicard_image.paste(shattered_image, mask=shattered_image)

        frame_path = f"assets/anicard/frame/{self.frame}.png"
        frame_image: Image.Image = await pillow.get_image(image_path=frame_path)
        anicard_image.paste(frame_image, mask=frame_image)

        anicard_draw = ImageDraw.Draw(anicard_image)

        if self.character:
            minion_name_pos = (226, 495)
            minion_name_font = ImageFont.truetype("assets/font/Insanibc.TTF", 55)
            minion_name_color = (255, 255, 255)
            minion_name_stroke_width = 5
            minion_name_stroke_color = "black"
            write_text_on_anicard(
                anicard_draw=anicard_draw,
                text=self.character,
                position=minion_name_pos,
                font=minion_name_font,
                fill=minion_name_color,
                stroke_width=minion_name_stroke_width,
                stroke_fill=minion_name_stroke_color,
            )

        if self.anime:
            anime_name_pos = (226, 555)
            anime_name_font = ImageFont.truetype("assets/font/Insanibc.TTF", 35)
            anime_name_color = (255, 255, 102)
            anime_name_stroke_width = 5
            anime_name_stroke_color = "black"
            write_text_on_anicard(
                anicard_draw=anicard_draw,
                text=self.anime,
                position=anime_name_pos,
                font=anime_name_font,
                fill=anime_name_color,
                stroke_width=anime_name_stroke_width,
                stroke_fill=anime_name_stroke_color,
            )

        if self.tag:
            tag_pos = (226, 622)
            tag_font = ImageFont.truetype("assets/font/Insanibc.TTF", 35)
            tag_color = (255, 255, 255)
            tag_stroke_width = 2
            tag_stroke_color = "black"
            write_text_on_anicard(
                anicard_draw=anicard_draw,
                text=self.tag,
                position=tag_pos,
                font=tag_font,
                fill=tag_color,
                stroke_width=tag_stroke_width,
                stroke_fill=tag_stroke_color,
            )

        if self.aniclass and self.codex:
            aniclass_font = ImageFont.truetype("assets/font/Emoji.TTF", 25)
            codex_font = ImageFont.truetype("assets/font/Insanibc.TTF", 25)
            left, top, right, bottom = codex_font.getbbox(str(self.codex))
            width, _ = right - left, bottom - top
            aniclass_text_position = (452 - width) / 2 - 20, 25
            aniclass_text_color = (255, 255, 255)
            aniclass_stroke_width = 3
            aniclass_stroke_fill = "black"
            anicard_draw.text(
                aniclass_text_position,
                self.aniclass,
                aniclass_text_color,
                font=aniclass_font,
                stroke_width=aniclass_stroke_width,
                stroke_fill=aniclass_stroke_fill,
            )
            codex_text_position = (452 - width) / 2 + 10, 25
            codex_text_color = (255, 255, 255)
            codex_stroke_width = 2
            codex_stroke_fill = "black"
            anicard_draw.text(
                codex_text_position,
                str(self.codex),
                codex_text_color,
                font=codex_font,
                stroke_width=codex_stroke_width,
                stroke_fill=codex_stroke_fill,
            )

        return anicard_image
