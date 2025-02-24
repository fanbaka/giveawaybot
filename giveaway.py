from telegram import Bot
from config import TOKEN, REQUIRED_CHANNELS
import asyncio

async def check_single_channel(bot, channel, user_id):
    try:
        member = await bot.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"Error checking {channel}: {e}")
        return False

async def check_participation(user_id):
    bot = Bot(token=TOKEN)
    tasks = [check_single_channel(bot, channel, user_id) for channel in REQUIRED_CHANNELS]
    results = await asyncio.gather(*tasks)  # Mengeksekusi semua pengecekan secara paralel
    return all(results)
