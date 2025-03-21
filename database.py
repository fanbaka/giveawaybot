from supabase import create_client
from datetime import datetime, timedelta

# Setup koneksi ke Supabase
SUPABASE_URL = "https://jskexleqowjcmzqdvjng.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impza2V4bGVxb3dqY216cWR2am5nIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDI1NDUzNjUsImV4cCI6MjA1ODEyMTM2NX0.Mx1YaEe-ewmQ0bsnlGnP9-ka94xuVJxG-UU7V9UGxJI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_giveaway(title, duration, num_winners, organizer, channel_id, required_channels, message_id):
    """Membuat giveaway baru di Supabase dan menyimpan message_id untuk bisa diedit nanti."""
    end_time = (datetime.now() + timedelta(minutes=duration)).strftime("%Y-%m-%d %H:%M:%S")
    
    data = {
        "title": title,
        "duration": duration,
        "num_winners": num_winners,
        "organizer": organizer,
        "end_time": end_time,
        "channel_id": channel_id,
        "required_channels": required_channels,
        "message_id": message_id
    }
    
    response = supabase.table("giveaways").insert(data).execute()
    if response.data:
        return response.data[0]["id"]
    return None

def get_expired_giveaways():
    """Mengambil daftar giveaway yang sudah berakhir."""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    response = supabase.table("giveaways").select("*").lte("end_time", current_time).execute()
    
    return response.data if response.data else []

def add_participant(giveaway_id, user_id, username):
    """Menambahkan peserta ke giveaway di Supabase."""
    data = {
        "giveaway_id": giveaway_id,
        "user_id": user_id,
        "username": username
    }
    
    supabase.table("participants").insert(data).execute()

def get_participants(giveaway_id):
    """Mengambil daftar peserta dari giveaway tertentu."""
    response = supabase.table("participants").select("username").eq("giveaway_id", giveaway_id).execute()
    
    return [row["username"] for row in response.data] if response.data else []

def delete_giveaway(giveaway_id):
    """Menghapus giveaway dari Supabase."""
    supabase.table("giveaways").delete().eq("id", giveaway_id).execute()

def get_giveaway_details(giveaway_id):
    """Mengambil detail giveaway berdasarkan ID."""
    response = supabase.table("giveaways").select("*").eq("id", giveaway_id).single().execute()
    return response.data if response.data else None