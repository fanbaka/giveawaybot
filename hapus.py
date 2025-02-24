import os

if os.path.exists("giveaway.db"):
    os.remove("giveaway.db")
    print("🗑️ Database lama dihapus!")
