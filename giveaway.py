from telegram import Bot
from config import TOKEN, REQUIRED_CHANNELS
import asyncio
import random

async def check_single_channel(bot, channel, user_id):
    """Cek apakah user sudah join channel tertentu."""
    try:
        await asyncio.sleep(random.uniform(0.5, 1.5))  # Tambahkan delay acak supaya tidak membanjiri API
        member = await bot.get_chat_member(channel, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        print(f"❌ Error checking {channel}: {e}")
        return False  # Jika gagal, anggap user belum join

async def check_participation(user_id):
    """Cek apakah user sudah join semua channel yang diwajibkan."""
    try:
        bot = Bot(token=TOKEN)
        semaphore = asyncio.Semaphore(5)  # Batasi maksimal 5 request sekaligus
        
        async def limited_check(channel):
            async with semaphore:
                return await check_single_channel(bot, channel, user_id)

        tasks = [limited_check(channel) for channel in REQUIRED_CHANNELS]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        if any(isinstance(res, Exception) for res in results):
            print(f"⚠️ Error in check_participation: {results}")
            return False  # Kalau ada error, anggap user belum join

        return all(results)  # Pastikan semua channel statusnya True
    except Exception as e:
        print(f"🔥 Fatal error in check_participation: {e}")
        return False  # Kalau error besar, anggap user belum join
