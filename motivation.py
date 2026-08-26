import asyncio
import logging
import os
import random

from aiogram.types import FSInputFile

import db
from motivation_data import MOTIVATIONS

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets", "motivation")

INTERVAL_SECONDS = 3 * 60 * 60  # every 3 hours


async def _send_one(bot, item):
    employees = await db.get_employees()
    photo_path = os.path.join(ASSETS_DIR, item["photo"])
    has_photo = os.path.isfile(photo_path)

    for user_id, _ in employees:
        try:
            if has_photo:
                await bot.send_photo(user_id, FSInputFile(photo_path), caption=item["text"])
            else:
                await bot.send_message(user_id, item["text"])
        except Exception:
            logging.exception("Failed to send motivation to %s", user_id)


async def motivation_scheduler(bot):
    order = list(range(len(MOTIVATIONS)))
    random.shuffle(order)
    pos = 0

    while True:
        if pos >= len(order):
            random.shuffle(order)
            pos = 0

        await _send_one(bot, MOTIVATIONS[order[pos]])
        pos += 1

        await asyncio.sleep(INTERVAL_SECONDS)
