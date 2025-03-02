from database import get_participants

giveaway_id = 1  # Ganti dengan ID giveaway yang mau dicek
participants = get_participants(giveaway_id)

print(f"Jumlah peserta saat ini: {len(participants)}")
print(f"List peserta: {participants}")
