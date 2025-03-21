import logging
import asyncio
import random
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from config import TOKEN
from database import create_giveaway, get_expired_giveaways, delete_giveaway, get_participants, add_participant, get_giveaway_details
from giveaway import check_participation

# Konfigurasi logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Respon saat pengguna memulai bot."""
    await update.message.reply_text("Welcome! Use /newgiveaway to start a giveaway.")

async def new_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        args = context.args
        if len(args) < 6:
            await update.message.reply_text("Usage: /newgiveaway <prize_link> <duration> <num_winners> <organizer> <channel_id> <required_channels (comma separated)>")
            return
        
        title = args[0]
        duration = int(args[1])
        num_winners = int(args[2])
        organizer = args[3]
        channel_id = args[4]
        required_channels = args[5].split(',')

        giveaway_id = create_giveaway(title, duration, num_winners, organizer, channel_id, required_channels)
        end_time = datetime.now() + timedelta(minutes=duration)
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        required_channels_text = "\n".join([f"@{channel}" for channel in required_channels])

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
            chat_id=channel_id,
            text=message,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

        await update.message.reply_text("Giveaway has been created and posted to the channel!")
    except ValueError:
        await update.message.reply_text("Error: Number of winners and duration must be integers.")

async def join_giveaway(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        user_id = query.from_user.id
        username = query.from_user.username or f"user_{user_id}"
        data = query.data.split("_")
        
        if len(data) < 2 or not data[1].isdigit():
            await query.answer("❌ Invalid giveaway data!", show_alert=True)
            return
        
        giveaway_id = int(data[1])
        giveaway = get_giveaway_details(giveaway_id)
        
        if not giveaway:
            await query.answer("❌ Giveaway not found!", show_alert=True)
            return
        
        participants = get_participants(giveaway_id)
        if username in participants:
            await query.answer("✅ You have already joined this giveaway!", show_alert=True)
            return
        
        is_joined = await check_participation(user_id, giveaway_id)
        if is_joined:
            add_participant(giveaway_id, user_id, username)
            message = "✅ Successfully joined the giveaway!"
        else:
            message = "❌ You must join all required channels first!"

        await query.answer(message, show_alert=True)

    except Exception as e:
        print(f"Error in join_giveaway: {e}")
        await query.answer("⚠️ Error processing your request. Try again later!", show_alert=True)

async def check_giveaway_expiry(context: ContextTypes.DEFAULT_TYPE):
    expired_giveaways = get_expired_giveaways()
    for giveaway in expired_giveaways:
        participants = get_participants(giveaway["id"])
        total_participants = len(participants)
        
        if participants:
            winners = random.sample(participants, min(len(participants), giveaway["num_winners"]))
            winner_mentions = ", ".join([f"@{w}" for w in winners])
            message = (
                f"⏳ **Lucky Draw Ended!**\n\n"
                f"🎁 **Prize:** [Click Here]({giveaway['title']})\n"
                f"🏆 **Winners:** {winner_mentions}\n"
                f"👥 **Total Participants:** {total_participants}\n"
                f"👤 **Hosted By:** {giveaway['organizer']}\n\n"
                f"🎉 Congratulations! Stay tuned for more giveaways!"
            )
        else:
            message = (
                f"⏳ **Lucky Draw Ended!**\n\n"
                f"🎁 **Prize:** [Click Here]({giveaway['title']})\n"
                f"🏆 No participants joined 😢\n"
                f"👤 **Hosted By:** {giveaway['organizer']}\n\n"
                f"Better luck next time!"
            )

        await context.bot.send_message(
            chat_id=giveaway["channel_id"],
            text=message,
            parse_mode="Markdown"
        )

        delete_giveaway(giveaway["id"])

def main():
    app = Application.builder().token(TOKEN).pool_timeout(10).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("newgiveaway", new_giveaway))
    app.add_handler(CallbackQueryHandler(join_giveaway, pattern="^join_"))
    app.job_queue.run_repeating(check_giveaway_expiry, interval=60, first=10)
    logging.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
