import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "admissions.db")

def start_sql_shell():
    if not os.path.exists(DB_PATH):
        print("Database file not found at:", DB_PATH)
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("=" * 80)
    print("           SQL QUERY RUNNER - CANDIDATE ADMISSION SYSTEM")
    print("=" * 80)
    print(f"Connected to: {DB_PATH}")
    print("Type your SQL query and press Enter. Type 'tables' to list tables, or 'exit' to quit.\n")

    while True:
        try:
            query = input("SQL> ").strip()
            if not query:
                continue
            if query.lower() in ["exit", "quit", "q"]:
                print("Exiting SQL Runner...")
                break
            if query.lower() == "tables":
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [r[0] for r in cursor.fetchall()]
                print("Available Tables:", ", ".join(tables), "\n")
                continue

            cursor.execute(query)
            
            if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("PRAGMA"):
                rows = cursor.fetchall()
                if not rows:
                    print("Query executed. (0 rows returned)\n")
                    continue

                cols = rows[0].keys()
                # Print header
                header = " | ".join(f"{str(c):<15}" for c in cols)
                print("-" * len(header))
                print(header)
                print("-" * len(header))

                # Print rows
                for r in rows:
                    row_str = " | ".join(f"{str(r[c] if r[c] is not None else 'NULL')[:14]:<15}" for c in cols)
                    print(row_str)
                print(f"\n({len(rows)} row(s) returned)\n")
            else:
                conn.commit()
                print(f"Query executed successfully. ({cursor.rowcount} row(s) affected)\n")

        except Exception as e:
            print("SQL Error:", e, "\n")

    conn.close()

if __name__ == "__main__":
    start_sql_shell()
