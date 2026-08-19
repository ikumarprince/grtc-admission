import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "admissions.db")

def show_users():
    if not os.path.exists(DB_PATH):
        print("Database not found at:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 105)
    print("             USER ACCOUNTS & AUTHENTICATION DATABASE VIEWER")
    print("=" * 105)
    print("Database File: " + DB_PATH + "\n")

    cursor.execute("SELECT id, username, password_hash as raw_password, full_name, role, center_name, mobile, email, status, created_at FROM users ORDER BY id ASC")
    users = cursor.fetchall()

    print(f"Total Users Registered: {len(users)}\n")

    print("-" * 120)
    print(f"{'ID':<4} | {'Role':<12} | {'Login Username / ID':<26} | {'Password (Plain)':<18} | {'Full Name':<20} | {'Mobile':<12}")
    print("-" * 120)

    for u in users:
        role_badge = f"[{u['role'].upper()}]"
        pwd = u['raw_password'] or ''
        print(f"{u['id']:<4} | {role_badge:<12} | {u['username'][:25]:<26} | {pwd:<18} | {u['full_name'][:19]:<20} | {u['mobile'] or 'N/A':<12}")

    print("-" * 120)
    print("\n[Note] Passwords are now stored in Plain Text (No Encryption/Hash).")
    print("=" * 105)
    conn.close()

if __name__ == "__main__":
    show_users()
    try:
        input("\nPress Enter to exit...")
    except:
        pass
