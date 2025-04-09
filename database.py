from datetime import datetime, timedelta, timezone
from config import SUPABASE_URL, SUPABASE_KEY
from supabase import create_client

# Inisialisasi Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def create_giveaway(title, duration, num_winners, organizer):
    end_time = (datetime.now(timezone.utc) + timedelta(minutes=duration)).isoformat()
    data = {
        "title": title,
        "duration": duration,
        "num_winners": num_winners,
        "organizer": organizer,
        "end_time": end_time
    }
    result = supabase.table("giveaways").insert(data).execute()
    return result.data[0]["id"]

def get_expired_giveaways():
    now = datetime.now(timezone.utc).isoformat()
    result = supabase.table("giveaways").select("*").lte("end_time", now).execute()
    return result.data

def add_participant(giveaway_id, user_id, username):
    try:
        supabase.table("participants").insert({
            "giveaway_id": giveaway_id,
            "user_id": user_id,
            "username": username
        }).execute()
    except Exception:
        pass  # user mungkin sudah ada

def get_participants(giveaway_id):
    result = supabase.table("participants").select("username").eq("giveaway_id", giveaway_id).execute()
    return [row["username"] for row in result.data]

def delete_giveaway(giveaway_id):
    giveaway_id = int(giveaway_id)  # pastikan integer

    # Hapus semua peserta terlebih dahulu
    participants_res = supabase.table("participants").delete().eq("giveaway_id", giveaway_id).execute()
    print(f"[DEBUG] Deleted participants for giveaway ID {giveaway_id}: {participants_res}")

    # Baru hapus giveaway-nya
    giveaway_res = supabase.table("giveaways").delete().eq("id", giveaway_id).execute()
    print(f"[DEBUG] Deleted giveaway ID {giveaway_id}: {giveaway_res}")

def set_post_channel(channel):
    supabase.table("settings").update({"post_channel": channel}).eq("id", 1).execute()

def get_post_channel():
    result = supabase.table("settings").select("post_channel").eq("id", 1).execute()
    return result.data[0]["post_channel"]

def add_required_channel(channel):
    current = get_required_channels()
    if channel not in current:
        current.append(channel)
        supabase.table("settings").update({"required_channels": current}).eq("id", 1).execute()

def remove_required_channel(channel):
    current = get_required_channels()
    if channel in current:
        current.remove(channel)
        supabase.table("settings").update({"required_channels": current}).eq("id", 1).execute()

def get_required_channels():
    result = supabase.table("settings").select("required_channels").eq("id", 1).execute()
    return result.data[0]["required_channels"]

