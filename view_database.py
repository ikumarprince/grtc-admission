import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "admissions.db")

def view_data():
    if not os.path.exists(DB_PATH):
        print("Database not found at:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 95)
    print("           CANDIDATE ADMISSION SYSTEM - BACKEND DATABASE VIEWER")
    print("=" * 95)
    print("Database File: " + DB_PATH + "\n")

    cursor.execute("SELECT COUNT(*) FROM candidates")
    total = cursor.fetchone()[0]
    print(f"Total Registered Candidates: {total}\n")

    if total == 0:
        print("No records found in database.")
        conn.close()
        return

    cursor.execute('''
        SELECT id, application_no, admission_date, full_name, gender, mobile_no, 
               course, stream_branch, fee_paid, fee_balance, admission_status 
        FROM candidates 
        ORDER BY id DESC
    ''')
    
    rows = cursor.fetchall()
    
    print("-" * 110)
    print(f"{'ID':<4} | {'App No':<14} | {'Name':<20} | {'Mobile':<12} | {'Course':<24} | {'Paid':<8} | {'Status':<10}")
    print("-" * 110)
    
    for r in rows:
        c_name = (r['course'] or '')[:23]
        f_name = (r['full_name'] or '')[:19]
        print(f"{r['id']:<4} | {r['application_no']:<14} | {f_name:<20} | {r['mobile_no']:<12} | {c_name:<24} | Rs.{int(r['fee_paid']):<5} | {r['admission_status']:<10}")
    
    print("-" * 110)
    print("\n[Tip] Excel/CSV format me download karne ke liye browser me open karein:")
    print("      http://127.0.0.1:8000/api/export/csv")
    print("=" * 95)
    conn.close()

if __name__ == "__main__":
    view_data()
    try:
        input("\nPress Enter to exit...")
    except:
        pass
