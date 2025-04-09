import logging
import asyncio
import random
import os
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from database import set_post_channel, add_required_channel, remove_required_channel, get_required_channels, get_post_channel
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from database import create_giveaway, get_expired_giveaways, delete_giveaway, get_participants, add_participant
from giveaway import check_participation

TOKEN = os.environ.get("BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respon saat pengguna memulai bot."""
    await update.message.reply_text("Welcome! Use /newgiveaway to start a giveaway.")

async def new_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 4:
            await update.message.reply_text("Usage: /newgiveaway <prize_link> <duration (minutes)> <num_winners> <organizer>")
            return
        
        title = args[0]  # Link hadiah
        duration = int(args[-3])
        num_winners = int(args[-2])
        organizer = args[-1]
        giveaway_id = create_giveaway(title, duration, num_winners, organizer)

        end_time = datetime.now() + timedelta(minutes=duration)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")  # Format: YYYY-MM-DD HH:MM:SS

        required_channels_text = "\n".join([f"{channel}" for channel in get_required_channels()])

        buttons = [[InlineKeyboardButton("✅ Join & Participate", callback_data=f"join_{giveaway_id}")]]
        keyboard = InlineKeyboardMarkup(buttons)

        message = (
            f"📢 **Grab Your Goodies!**\n\n"
            f"🎁 **Prize:** [Click Here]({title})\n"
            f"⏳ **Ends At:** {end_time_str} WIB\n"
            f"🏆 **Winners:** {num_winners}\n"
            f"👤 **Hosted By:** {organizer}\n\n"
            f"📌 **Join these channels first:**\n{required_channels_text}\n\n"
            "Then, click the button below to join the giveaway!"
        )

        await context.bot.send_message(
            chat_id=get_post_channel(),
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await update.message.reply_text("Giveaway has been created and posted to the channel!")
    except ValueError:
        await update.message.reply_text("Error: Number of winners and duration must be integers.")


async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani pengguna yang ingin join giveaway tanpa menghapus tombol dan tanpa mengirim pesan baru."""
    query = update.callback_query

    try:
        user_id = query.from_user.id
        username = query.from_user.username or f"user_{user_id}"
        data = query.data.split("_")

        # Validasi giveaway_id
        if len(data) < 2 or not data[1].isdigit():
            await query.answer("❌ Invalid giveaway data!", show_alert=True)
            return

        giveaway_id = int(data[1])

        # Cek apakah user sudah join sebelumnya
        participants = get_participants(giveaway_id)
        if user_id in participants:
            await query.answer("✅ You have already joined this giveaway!", show_alert=True)
            return

        # Cek keanggotaan channel
        is_joined = await check_participation(user_id)
        if is_joined:
            add_participant(giveaway_id, user_id, username)
            message = "✅ Successfully joined the giveaway!"
        else:
            message = "❌ You must join all required channels first!"

        # Notif di tengah layar
        await query.answer(message, show_alert=True)

    except Exception as e:
        print(f"Error in join_giveaway: {e}")
        await query.answer("⚠️ Error processing your request. Try again later!", show_alert=True)



async def check_giveaway_expiry(context: ContextTypes.DEFAULT_TYPE):
    expired_giveaways = get_expired_giveaways()
    for giveaway in expired_giveaways:
        participants = get_participants(giveaway["id"])
        total_participants = len(participants)  # Hitung jumlah peserta
        
        end_time_str = giveaway["end_time"]  # Ambil dari database

        if participants:
            winners = random.sample(participants, min(len(participants), giveaway["num_winners"]))
            winner_mentions = ", ".join([f"@{w}" for w in winners])
            message = (
                f"⏳ **Lucky Draw Ended!**\n\n"
                f"🎁 **Prize:** [Click Here]({giveaway['title']})\n"
                f"📆 **Ended At:** {end_time_str} WIB\n"
                f"🏆 **Winners:** {winner_mentions}\n"
                f"👥 **Total Participants:** {total_participants}\n"
                f"👤 **Hosted By:** {giveaway['organizer']}\n\n"
                f"🎉 Congratulations! Stay tuned for more giveaways!"
            )
        else:
            message = (
                f"⏳ **Lucky Draw Ended!**\n\n"
                f"🎁 **Prize:** [Click Here]({giveaway['title']})\n"
                f"📆 **Ended At:** {end_time_str} WIB\n"
                f"🏆 No participants joined 😢\n"
                f"👥 **Total Participants:** {total_participants}\n"
                f"👤 **Hosted By:** {giveaway['organizer']}\n\n"
                f"Better luck next time!"
            )

        await context.bot.send_message(
            chat_id=get_post_channel(),
            text=message,
            parse_mode="Markdown",
            disable_web_page_preview=False
        )

        print(f"[INFO] Deleting giveaway ID: {giveaway['id']}")
        delete_giveaway(giveaway["id"])

async def set_post_channel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /setpostchannel @channelname")
        return
    channel = context.args[0]
    set_post_channel(channel)
    await update.message.reply_text(f"✅ Post channel set to: {channel}")

async def add_required_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addrequired @channelname")
        return
    channel = context.args[0]
    add_required_channel(channel)
    await update.message.reply_text(f"✅ Added required channel: {channel}")

async def remove_required_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /removerequired @channelname")
        return
    channel = context.args[0]
    remove_required_channel(channel)
    await update.message.reply_text(f"✅ Removed required channel: {channel}")

async def view_settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post_channel = get_post_channel()
    required = get_required_channels()
    await update.message.reply_text(
        f"📦 Current Settings:\nPost Channel: {post_channel}\nRequired Channels:\n" +
        "\n".join(required)
    )


def main():
    """Menjalankan bot."""
    app = Application.builder().token(TOKEN).pool_timeout(10).build()

    # Menambahkan handler untuk perintah dan callback
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgiveaway", new_giveaway))
    app.add_handler(CallbackQueryHandler(join_giveaway, pattern="^join_"))
    app.add_handler(CommandHandler("setpostchannel", set_post_channel_cmd))
    app.add_handler(CommandHandler("addrequired", add_required_cmd))
    app.add_handler(CommandHandler("removerequired", remove_required_cmd))
    app.add_handler(CommandHandler("viewsettings", view_settings_cmd))

    # Menjalankan pengecekan giveaway yang berakhir setiap 1 jam
    app.job_queue.run_repeating(check_giveaway_expiry, interval=60, first=10)

    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
