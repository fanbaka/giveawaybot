import sqlite3
import os
from config import TOKEN
from datetime import datetime, timedelta
from telegram.ext import ApplicationBuilder, CallbackContext

def init_db():
    db_path = "giveaway.db"

    # Cek apakah database ada, jika tidak, buat baru
    if not os.path.exists(db_path):
        print("⚠️ Database tidak ditemukan, membuat database baru...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ✅ Buat tabel giveaways
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS giveaways (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            duration INTEGER,
            num_winners INTEGER,
            organizer TEXT,
            end_time TEXT
        )''')

    # ✅ Buat tabel participants
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            giveaway_id INTEGER,
            user_id INTEGER UNIQUE,
            username TEXT,
            FOREIGN KEY (giveaway_id) REFERENCES giveaways(id)
        )''')

    conn.commit()
    conn.close()

    print("✅ Database berhasil dibuat dengan tabel giveaways dan participants!")

def create_giveaway(title, duration, num_winners, organizer):
    conn = sqlite3.connect("giveaway.db")
    cursor = conn.cursor()
    end_time = (datetime.now() + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO giveaways (title, duration, num_winners, organizer, end_time) VALUES (?, ?, ?, ?, ?)", 
                   (title, duration, num_winners, organizer, end_time))
    giveaway_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return giveaway_id

def get_expired_giveaways():
    conn = sqlite3.connect("giveaway.db")
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("SELECT id, title, num_winners, organizer, end_time FROM giveaways WHERE end_time <= ?", (current_time,))
    expired_giveaways = cursor.fetchall()
    conn.close()
    return [{"id": row[0], "title": row[1], "num_winners": row[2], "organizer": row[3], "end_time": row[4]} for row in expired_giveaways]

# ✅ Tambahkan fungsi check_giveaway_expiry langsung di database.py agar tidak ada circular import
async def check_giveaway_expiry(context: CallbackContext):
    expired_giveaways = get_expired_giveaways()
    for giveaway in expired_giveaways:
        message = f"🎉 Giveaway '{giveaway['title']}' telah berakhir! Pemenang akan diumumkan oleh {giveaway['organizer']}."
        await context.bot.send_message(chat_id="YOUR_CHANNEL_ID", text=message)

def add_participant(giveaway_id, user_id, username):
    conn = sqlite3.connect("giveaway.db", isolation_level=None)  
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO participants (giveaway_id, user_id, username) VALUES (?, ?, ?)", (giveaway_id, user_id, username))
    except sqlite3.IntegrityError:
        pass  # Jika user sudah ada, tidak perlu error

    conn.commit()
    conn.close()


def get_participants(giveaway_id):
    conn = sqlite3.connect("giveaway.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM participants WHERE giveaway_id = ?", (giveaway_id,))
    participants = [row[0] for row in cursor.fetchall()]
    conn.close()
    return participants

def delete_giveaway(giveaway_id):
    conn = sqlite3.connect("giveaway.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM giveaways WHERE id = ?", (giveaway_id,))
    conn.commit()
    conn.close()

def main():
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    job_queue = app.job_queue
    job_queue.run_repeating(check_giveaway_expiry, interval=60, first=10)
    app.run_polling()

if __name__ == "__main__":
    main()
