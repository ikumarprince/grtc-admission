import os
import json
import uuid
import re
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
IS_POSTGRES = DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://")

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor
else:
    import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "admissions.db")
os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)

DEFAULT_SETTINGS = {
    "institution_name": "Gyanoday Rojgar Training Centre",
    "institution_tagline": "Approved by NSDC and SSC Recognized Institution",
    "institution_address": "Khaspur Ramchandra pahalwan path near bajaj showroom patna 801503",
    "institution_phone": "+91 80021 43322",
    "institution_email": "",
    "institution_code": "GRTC-PATNA",
    "academic_years": ["2026-2027", "2025-2026", "2024-2025"],
    "courses": [
        {"name": "Computer", "duration": "6 Months", "branches": [], "default_fee": 400},
        {"name": "Hotel Management", "duration": "1 Year", "branches": [], "default_fee": 400},
        {"name": "GDA", "duration": "6 Months", "branches": [], "default_fee": 400}
    ],
    "upi_id": ""
}

class UniversalCursor:
    def __init__(self, raw_cursor, is_pg):
        self.cursor = raw_cursor
        self.is_pg = is_pg
        self.rowcount = 0

    def execute(self, sql, params=None):
        if self.is_pg:
            # Convert SQLite ? to Postgres %s
            pg_sql = sql.replace("?", "%s")
            if params is None:
                self.cursor.execute(pg_sql)
            else:
                self.cursor.execute(pg_sql, tuple(params))
        else:
            if params is None:
                self.cursor.execute(sql)
            else:
                self.cursor.execute(sql, tuple(params))
        self.rowcount = getattr(self.cursor, "rowcount", 0)
        return self

    def fetchone(self):
        row = self.cursor.fetchone()
        if row is None:
            return None
        if self.is_pg:
            return dict(row)
        return dict(row)

    def fetchall(self):
        rows = self.cursor.fetchall()
        if self.is_pg:
            return [dict(r) for r in rows]
        return [dict(r) for r in rows]

    def close(self):
        self.cursor.close()

class UniversalConnection:
    def __init__(self, raw_conn, is_pg):
        self.conn = raw_conn
        self.is_pg = is_pg

    def cursor(self):
        if self.is_pg:
            return UniversalCursor(self.conn.cursor(cursor_factory=RealDictCursor), True)
        return UniversalCursor(self.conn.cursor(), False)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()

def get_db_connection():
    if IS_POSTGRES:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        
        # Ensure SSL mode if connecting to Supabase
        if "sslmode=" not in url and ("supabase.co" in url or "supabase.com" in url):
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}sslmode=require"
            
        conn = psycopg2.connect(url, cursor_factory=RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def password_to_ascii(password: str) -> str:
    if not password:
        return ""
    p_str = str(password)
    return " ".join(str(ord(ch)) for ch in p_str)

def ascii_to_password(ascii_str: str) -> str:
    if not ascii_str:
        return ""
    try:
        parts = str(ascii_str).strip().split()
        return "".join(chr(int(p)) for p in parts if p.isdigit())
    except Exception:
        return str(ascii_str)

def is_already_ascii_format(val: str) -> bool:
    if not val:
        return False
    s_val = str(val).strip()
    if not re.match(r"^\d{1,3}(\s+\d{1,3})*$", s_val):
        return False
    try:
        codes = [int(x) for x in s_val.split()]
        return all(0 <= c <= 1114111 for c in codes)
    except Exception:
        return False

def validate_password(password: str) -> str:
    p_str = str(password or "")
    if len(p_str) < 6:
        raise ValueError("Password must be at least 6 characters long.")
    if len(p_str) > 12:
        raise ValueError("Password must not exceed 12 characters.")
    return p_str

def hash_password(password: str) -> str:
    if not password:
        return ""
    return str(password).strip()

def password_to_ascii(password: str) -> str:
    return str(password).strip()

def password_to_ascii(password: str) -> str:
    return str(password).strip()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        # PostgreSQL Schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            mobile VARCHAR(50),
            email VARCHAR(255),
            role VARCHAR(50) NOT NULL,
            center_name VARCHAR(255) DEFAULT 'Main Campus',
            candidate_id INTEGER,
            status VARCHAR(50) DEFAULT 'active',
            profile_picture TEXT,
            plain_password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS plain_password TEXT;")
        except Exception:
            pass

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            center_name VARCHAR(255) DEFAULT 'Main Campus',
            application_no VARCHAR(100) UNIQUE NOT NULL,
            academic_year VARCHAR(50) DEFAULT '2026-2027',
            course VARCHAR(100) NOT NULL,
            stream_branch VARCHAR(100),
            admission_status VARCHAR(50) DEFAULT 'Pending',
            full_name VARCHAR(255) NOT NULL,
            gender VARCHAR(50),
            dob VARCHAR(50),
            category VARCHAR(50),
            blood_group VARCHAR(20),
            aadhaar_no VARCHAR(50),
            nationality VARCHAR(50) DEFAULT 'Indian',
            religion VARCHAR(50),
            mother_tongue VARCHAR(50),
            mobile_no VARCHAR(50) NOT NULL,
            email VARCHAR(255),
            current_address TEXT,
            current_city VARCHAR(100),
            current_state VARCHAR(100),
            current_pincode VARCHAR(20),
            permanent_address TEXT,
            permanent_city VARCHAR(100),
            permanent_state VARCHAR(100),
            permanent_pincode VARCHAR(20),
            father_name VARCHAR(255),
            father_occupation VARCHAR(100),
            father_mobile VARCHAR(50),
            mother_name VARCHAR(255),
            mother_occupation VARCHAR(100),
            annual_income REAL DEFAULT 0,
            prev_qualification VARCHAR(100),
            prev_school_college TEXT,
            prev_board_university TEXT,
            prev_passing_year VARCHAR(50),
            prev_roll_no VARCHAR(50),
            prev_max_marks REAL DEFAULT 0,
            prev_marks_obtained REAL DEFAULT 0,
            prev_percentage REAL DEFAULT 0,
            total_course_fee REAL DEFAULT 0,
            fee_paid REAL DEFAULT 0,
            fee_balance REAL DEFAULT 0,
            payment_mode VARCHAR(100) DEFAULT 'Cash',
            payment_ref VARCHAR(255),
            payment_date VARCHAR(50),
            remarks TEXT,
            photo_url TEXT,
            signature_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id SERIAL PRIMARY KEY,
            batch_code VARCHAR(100) UNIQUE NOT NULL,
            batch_name VARCHAR(255) NOT NULL,
            course VARCHAR(100) NOT NULL,
            stream_branch VARCHAR(100),
            start_date VARCHAR(50),
            end_date VARCHAR(50),
            timing VARCHAR(100),
            days VARCHAR(100),
            instructor VARCHAR(255),
            room_no VARCHAR(100),
            max_capacity INTEGER DEFAULT 40,
            status VARCHAR(50) DEFAULT 'Running',
            center_name VARCHAR(255) DEFAULT 'Main Campus',
            created_by VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_enrollments (
            id SERIAL PRIMARY KEY,
            batch_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            enrollment_date VARCHAR(50) NOT NULL,
            roll_number VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Active',
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(batch_id, candidate_id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            token VARCHAR(255) PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id SERIAL PRIMARY KEY,
            full_name VARCHAR(255) NOT NULL,
            mobile VARCHAR(50) NOT NULL,
            course VARCHAR(255) NOT NULL,
            district VARCHAR(100),
            status VARCHAR(50) DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id SERIAL PRIMARY KEY,
            config_data TEXT NOT NULL
        );
        """)

    else:
        # SQLite Schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            mobile TEXT,
            email TEXT,
            role TEXT NOT NULL,
            center_name TEXT DEFAULT 'Main Campus',
            candidate_id INTEGER,
            status TEXT DEFAULT 'active',
            profile_picture TEXT,
            plain_password TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN plain_password TEXT;")
        except Exception:
            pass

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            center_name TEXT DEFAULT 'Main Campus',
            application_no TEXT UNIQUE NOT NULL,
            academic_year TEXT DEFAULT '2026-2027',
            course TEXT NOT NULL,
            stream_branch TEXT,
            admission_status TEXT DEFAULT 'Pending',
            full_name TEXT NOT NULL,
            gender TEXT,
            dob TEXT,
            category TEXT,
            blood_group TEXT,
            aadhaar_no TEXT,
            nationality TEXT DEFAULT 'Indian',
            religion TEXT,
            mother_tongue TEXT,
            mobile_no TEXT NOT NULL,
            email TEXT,
            current_address TEXT,
            current_city TEXT,
            current_state TEXT,
            current_pincode TEXT,
            permanent_address TEXT,
            permanent_city TEXT,
            permanent_state TEXT,
            permanent_pincode TEXT,
            father_name TEXT,
            father_occupation TEXT,
            father_mobile TEXT,
            mother_name TEXT,
            mother_occupation TEXT,
            annual_income REAL DEFAULT 0,
            prev_qualification TEXT,
            prev_school_college TEXT,
            prev_board_university TEXT,
            prev_passing_year TEXT,
            prev_roll_no TEXT,
            prev_max_marks REAL DEFAULT 0,
            prev_marks_obtained REAL DEFAULT 0,
            prev_percentage REAL DEFAULT 0,
            total_course_fee REAL DEFAULT 0,
            fee_paid REAL DEFAULT 0,
            fee_balance REAL DEFAULT 0,
            payment_mode TEXT DEFAULT 'Cash',
            payment_ref TEXT,
            payment_date TEXT,
            remarks TEXT,
            photo_url TEXT,
            signature_url TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_code TEXT UNIQUE NOT NULL,
            batch_name TEXT NOT NULL,
            course TEXT NOT NULL,
            stream_branch TEXT,
            start_date TEXT,
            end_date TEXT,
            timing TEXT,
            days TEXT,
            instructor TEXT,
            room_no TEXT,
            max_capacity INTEGER DEFAULT 40,
            status TEXT DEFAULT 'Running',
            center_name TEXT DEFAULT 'Main Campus',
            created_by TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS batch_enrollments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_id INTEGER NOT NULL,
            candidate_id INTEGER NOT NULL,
            enrollment_date TEXT NOT NULL,
            roll_number TEXT,
            status TEXT DEFAULT 'Active',
            remarks TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(batch_id, candidate_id)
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS enquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            mobile TEXT NOT NULL,
            course TEXT NOT NULL,
            district TEXT,
            status TEXT DEFAULT 'Pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            config_data TEXT NOT NULL
        );
        """)

    # Universal Demo Accounts Seeding for BOTH PostgreSQL & SQLite
    demo_accounts = [
        ("superadmin", hash_password("superadminpassword"), "Master SuperAdmin", "8002143322", "superadmin@grtc.in", "superadmin", "Main Campus", "superadminpassword"),
        ("director", hash_password("directorpassword"), "Executive Director", "9304474574", "director@grtc.in", "director", "Main Campus", "directorpassword"),
        ("admin", hash_password("adminpassword"), "Patna Center Manager", "9876543210", "admin@grtc.in", "admin", "Main Campus", "adminpassword"),
        ("staff", hash_password("staffpassword"), "Front Desk Staff Executive", "9123456789", "staff@grtc.in", "staff", "Main Campus", "staffpassword"),
        ("student", hash_password("grtc@123"), "Demo Student Trainee", "9988776655", "student@grtc.in", "student", "Main Campus", "grtc@123")
    ]

    for un, pw_h, fn, mob, em, rl, cn, pl_pw in demo_accounts:
        try:
            if IS_POSTGRES:
                cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(%s)", (un,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, plain_password)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (un, pw_h, fn, mob, em, rl, cn, pl_pw))
            else:
                cursor.execute("SELECT id FROM users WHERE LOWER(username) = LOWER(?)", (un,))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, plain_password)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (un, pw_h, fn, mob, em, rl, cn, pl_pw))
        except Exception as seed_err:
            print(f"Seed info: {seed_err}")

    conn.commit()
    conn.close()

def create_user_session(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    token = uuid.uuid4().hex
    cursor.execute("INSERT INTO user_sessions (token, user_id) VALUES (?, ?)", (token, user_id))
    conn.commit()
    conn.close()
    return token

def get_user_id_from_session(token):
    if not token:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM user_sessions WHERE token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["user_id"] if isinstance(row, dict) else row[0]
    return None

def delete_user_session(token):
    if not token:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def get_user_by_id(uid):
    if not uid:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, username, full_name, mobile, email, role, center_name, candidate_id, status, profile_picture, created_at 
    FROM users 
    WHERE id = ?
    """, (uid,))
    row = cursor.fetchone()
    conn.close()
    return row

def authenticate_user(login_id, password):
    if not login_id or not password:
        return None
    conn = get_db_connection()
    cursor = conn.cursor()
    p_clean = str(password).strip()
    clean_id = str(login_id).strip().lower()
    clean_raw_id = str(login_id).strip()
    
    try:
        cursor.execute("""
        SELECT * FROM users 
        WHERE (LOWER(username) = LOWER(?) OR mobile = ? OR LOWER(email) = LOWER(?)) 
          AND (password_hash = ? OR plain_password = ?)
          AND (status = 'active' OR status IS NULL OR status = '')
        """, (clean_id, clean_raw_id, clean_id, p_clean, p_clean))
            
        row = cursor.fetchone()
        conn.close()
        
        if row:
            if isinstance(row, dict):
                return row
            return {
                "id": row[0],
                "username": row[1],
                "password_hash": row[2],
                "full_name": row[3],
                "mobile": row[4] if len(row) > 4 else "",
                "email": row[5] if len(row) > 5 else "",
                "role": row[6] if len(row) > 6 else "student",
                "center_name": row[7] if len(row) > 7 else "Main Campus",
                "candidate_id": row[8] if len(row) > 8 else None,
                "plain_password": p_clean
            }

        return None
    except Exception as e:
        print(f"Auth Exception: {e}")
        try: conn.close()
        except Exception: pass
        return None

def register_user(username=None, password="grtc@123", full_name="", mobile="", email="", role="student", center_name="Main Campus", candidate_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_mob = (mobile or "").strip()
    clean_email = (email or "").strip().lower()
    uname = (username or clean_mob or clean_email).strip().lower()
    
    # Check duplicate
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ? OR mobile = ? OR (email != '' AND LOWER(email) = ?)", (uname, clean_mob, clean_email))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise ValueError("User with this mobile/username/email already exists.")
        
    p_raw = str(password or "grtc@123").strip()
    validate_password(p_raw)
    p_store = password_to_ascii(p_raw)
    
    if IS_POSTGRES:
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, candidate_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active') RETURNING id
        """, (uname, p_store, full_name, clean_mob, clean_email, role, center_name, candidate_id))
        uid = cursor.fetchone()["id"]
    else:
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, candidate_id, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
        """, (uname, p_store, full_name, clean_mob, clean_email, role, center_name, candidate_id))
        uid = cursor.cursor.lastrowid

    conn.commit()
    cursor.execute("SELECT * FROM users WHERE id = ?", (uid,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users(role=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if role:
        cursor.execute("SELECT id, username, full_name, mobile, email, role, center_name, status, created_at FROM users WHERE role = ? ORDER BY id DESC", (role,))
    else:
        cursor.execute("SELECT id, username, full_name, mobile, email, role, center_name, status, created_at FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_user(uid, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    allowed = ["full_name", "mobile", "email", "role", "center_name", "status", "profile_picture"]
    for k in allowed:
        if k in data:
            fields.append(f"{k} = ?")
            values.append(data[k])
            
    if "password" in data and data["password"]:
        fields.append("password_hash = ?")
        p_raw = str(data["password"]).strip()
        validate_password(p_raw)
        values.append(password_to_ascii(p_raw))
        
    if not fields:
        conn.close()
        return None
        
    values.append(uid)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    
    cursor.execute("SELECT id, username, full_name, mobile, email, role, center_name, status, created_at FROM users WHERE id = ?", (uid,))
    user = cursor.fetchone()
    conn.close()
    return user

def delete_user(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (uid,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ================= SETTINGS =================

def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT config_data FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        val = row["config_data"] if isinstance(row, dict) else row[0]
        return json.loads(val)
    return DEFAULT_SETTINGS

def update_settings(new_config: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE settings SET config_data = ? WHERE id = 1", (json.dumps(new_config),))
    conn.commit()
    conn.close()
    return new_config

# ================= CANDIDATES & ADMISSIONS =================

def generate_application_no():
    year = datetime.now().year
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as cnt FROM candidates")
    row = cursor.fetchone()
    count = (row["cnt"] if isinstance(row, dict) else row[0]) + 1
    conn.close()
    return f"GRTC-{year}-{count:04d}"

def check_mobile_registered(mobile_no):
    clean_mob = re.sub(r'[^0-9]', '', str(mobile_no or ''))
    if len(clean_mob) < 10:
        return {"registered": False}
    clean_mob = clean_mob[-10:]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, application_no, full_name, mobile_no, course, admission_status, created_at 
    FROM candidates 
    WHERE mobile_no = ? OR mobile_no LIKE ?
    """, (clean_mob, f"%{clean_mob}"))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "registered": True,
            "candidate": row
        }
    return {"registered": False}

def create_candidate(data, user_id=None):
    clean_mob = re.sub(r'[^0-9]', '', str(data.get("mobile_no", "") or ""))
    if len(clean_mob) >= 10:
        clean_mob = clean_mob[-10:]
        mob_check = check_mobile_registered(clean_mob)
        if mob_check.get("registered"):
            c = mob_check["candidate"]
            raise ValueError(f"Mobile number {clean_mob} is already registered with student '{c.get('full_name')}' (Application No: {c.get('application_no')}). Duplicate registration not allowed.")

    app_no = generate_application_no()
    total_fee = float(data.get("total_course_fee", 400) or 400)
    fee_paid = float(data.get("fee_paid", 0) or 0)
    balance = max(0, total_fee - fee_paid)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = [
        "user_id", "center_name", "application_no", "academic_year", "course", "stream_branch",
        "admission_status", "full_name", "gender", "dob", "category", "blood_group",
        "aadhaar_no", "nationality", "religion", "mother_tongue", "mobile_no", "email",
        "current_address", "current_city", "current_state", "current_pincode",
        "permanent_address", "permanent_city", "permanent_state", "permanent_pincode",
        "father_name", "father_occupation", "father_mobile", "mother_name", "mother_occupation",
        "annual_income", "prev_qualification", "prev_school_college", "prev_board_university",
        "prev_passing_year", "prev_roll_no", "prev_max_marks", "prev_marks_obtained", "prev_percentage",
        "total_course_fee", "fee_paid", "fee_balance", "payment_mode", "payment_ref", "payment_date",
        "remarks", "photo_url", "signature_url"
    ]
    
    values = [
        user_id, data.get("center_name", "Main Campus"), app_no, data.get("academic_year", "2026-2027"),
        data.get("course", "Computer"), data.get("stream_branch", ""), data.get("admission_status", "Pending"),
        data.get("full_name", ""), data.get("gender", ""), data.get("dob", ""),
        data.get("category", "General"), data.get("blood_group", ""), data.get("aadhaar_no", ""),
        data.get("nationality", "Indian"), data.get("religion", ""), data.get("mother_tongue", ""),
        clean_mob or data.get("mobile_no", ""), data.get("email", ""), data.get("current_address", ""),
        data.get("current_city", ""), data.get("current_state", ""), data.get("current_pincode", ""),
        data.get("permanent_address", ""), data.get("permanent_city", ""), data.get("permanent_state", ""),
        data.get("permanent_pincode", ""), data.get("father_name", ""), data.get("father_occupation", ""),
        data.get("father_mobile", ""), data.get("mother_name", ""), data.get("mother_occupation", ""),
        float(data.get("annual_income", 0) or 0), data.get("prev_qualification", ""), data.get("prev_school_college", ""),
        data.get("prev_board_university", ""), data.get("prev_passing_year", ""), data.get("prev_roll_no", ""),
        float(data.get("prev_max_marks", 0) or 0), float(data.get("prev_marks_obtained", 0) or 0),
        float(data.get("prev_percentage", 0) or 0), total_fee, fee_paid, balance,
        data.get("payment_mode", "Cash"), data.get("payment_ref", ""), data.get("payment_date", ""),
        data.get("remarks", ""), data.get("photo_url", ""), data.get("signature_url", "")
    ]
    
    placeholders = ", ".join(["?"] * len(fields))
    columns = ", ".join(fields)
    
    if IS_POSTGRES:
        cursor.execute(f"INSERT INTO candidates ({columns}) VALUES ({placeholders}) RETURNING id", values)
        cid = cursor.fetchone()["id"]
    else:
        cursor.execute(f"INSERT INTO candidates ({columns}) VALUES ({placeholders})", values)
        cid = cursor.cursor.lastrowid
        
    conn.commit()
    cursor.execute("SELECT * FROM candidates WHERE id = ?", (cid,))
    candidate = cursor.fetchone()
    conn.close()
    return candidate

def get_candidates(search="", course="", academic_year="", status="", center="", limit=500, offset=0):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT c.*, 
           b.batch_name, b.batch_code, be.roll_number 
    FROM candidates c
    LEFT JOIN batch_enrollments be ON be.candidate_id = c.id AND be.status = 'Active'
    LEFT JOIN batches b ON b.id = be.batch_id
    WHERE 1=1
    """
    params = []
    
    if search:
        s = f"%{search}%"
        query += " AND (c.full_name ILIKE ? OR c.mobile_no ILIKE ? OR c.application_no ILIKE ? OR c.aadhaar_no ILIKE ?)" if IS_POSTGRES else " AND (c.full_name LIKE ? OR c.mobile_no LIKE ? OR c.application_no LIKE ? OR c.aadhaar_no LIKE ?)"
        params.extend([s, s, s, s])
        
    if course and course != "All":
        query += " AND c.course = ?"
        params.append(course)

    if academic_year and academic_year != "All":
        query += " AND c.academic_year = ?"
        params.append(academic_year)

    if status and status != "All":
        query += " AND c.admission_status = ?"
        params.append(status)

    if center and center != "All":
        query += " AND c.center_name = ?"
        params.append(center)
        
    cursor.execute("SELECT COUNT(*) as total FROM candidates")
    tot_row = cursor.fetchone()
    total = (tot_row["total"] if isinstance(tot_row, dict) else tot_row[0]) if tot_row else 0

    query += " ORDER BY c.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows, total

def get_candidate_by_id(cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, b.batch_name, b.batch_code, be.roll_number 
    FROM candidates c
    LEFT JOIN batch_enrollments be ON be.candidate_id = c.id AND be.status = 'Active'
    LEFT JOIN batches b ON b.id = be.batch_id
    WHERE c.id = ?
    """, (cid,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_candidate_by_user_id(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, b.batch_name, b.batch_code, be.roll_number 
    FROM candidates c
    LEFT JOIN batch_enrollments be ON be.candidate_id = c.id AND be.status = 'Active'
    LEFT JOIN batches b ON b.id = be.batch_id
    WHERE c.user_id = ?
    """, (uid,))
    row = cursor.fetchone()
    conn.close()
    return row

def update_candidate(cid, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for k, v in data.items():
        if k not in ["id", "application_no", "created_at"]:
            fields.append(f"{k} = ?")
            values.append(v)
            
    if not fields:
        conn.close()
        return None
        
    values.append(cid)
    cursor.execute(f"UPDATE candidates SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    
    cursor.execute("SELECT * FROM candidates WHERE id = ?", (cid,))
    candidate = cursor.fetchone()
    conn.close()
    return candidate

def delete_candidate(cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_enrollments WHERE candidate_id = ?", (cid,))
    cursor.execute("DELETE FROM candidates WHERE id = ?", (cid,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ================= BATCHES & ENROLLMENT =================

def get_batches(course="", center="", status=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = """
    SELECT b.*, 
           (SELECT COUNT(*) FROM batch_enrollments be WHERE be.batch_id = b.id AND be.status = 'Active') as enrolled_count 
    FROM batches b 
    WHERE 1=1
    """
    params = []
    if course:
        query += " AND b.course = ?"
        params.append(course)
    if status:
        query += " AND LOWER(b.status) = LOWER(?)"
        params.append(status.strip())
    
    if IS_POSTGRES:
        query += " ORDER BY b.id ASC"
    else:
        query += " ORDER BY CAST(REPLACE(REPLACE(b.batch_name, 'Batch ', ''), 'BAT-', '') AS INTEGER) ASC, b.id ASC"
        
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def create_batch(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    b_code = data.get("batch_code") or f"BAT-2026-{uuid.uuid4().hex[:4].upper()}"
    
    fields = ["batch_code", "batch_name", "course", "stream_branch", "start_date", "end_date", "timing", "days", "instructor", "room_no", "max_capacity", "status", "center_name", "created_by"]
    values = [
        b_code, data.get("batch_name", "New Batch"), data.get("course", "Computer"),
        data.get("stream_branch", ""), data.get("start_date", ""), data.get("end_date", ""),
        data.get("timing", "09:00 AM - 05:00 PM"), data.get("days", "Mon to Sat"),
        data.get("instructor", "Faculty"), data.get("room_no", "Lab 1"),
        int(data.get("max_capacity", 40)), data.get("status", "Running"),
        data.get("center_name", "Main Campus"), data.get("created_by", "Admin")
    ]
    
    placeholders = ", ".join(["?"] * len(fields))
    
    if IS_POSTGRES:
        cursor.execute(f"INSERT INTO batches ({', '.join(fields)}) VALUES ({placeholders}) RETURNING id", values)
        bid = cursor.fetchone()["id"]
    else:
        cursor.execute(f"INSERT INTO batches ({', '.join(fields)}) VALUES ({placeholders})", values)
        bid = cursor.cursor.lastrowid
        
    conn.commit()
    cursor.execute("SELECT * FROM batches WHERE id = ?", (bid,))
    batch = cursor.fetchone()
    conn.close()
    return batch

def update_batch(bid, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for k in ["batch_name", "course", "stream_branch", "start_date", "end_date", "timing", "days", "instructor", "room_no", "max_capacity", "status", "center_name"]:
        if k in data:
            fields.append(f"{k} = ?")
            values.append(data[k])
            
    if not fields:
        conn.close()
        return None
        
    values.append(bid)
    cursor.execute(f"UPDATE batches SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    
    cursor.execute("SELECT * FROM batches WHERE id = ?", (bid,))
    batch = cursor.fetchone()
    conn.close()
    return batch

def delete_batch(bid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_enrollments WHERE batch_id = ?", (bid,))
    cursor.execute("DELETE FROM batches WHERE id = ?", (bid,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_batch_candidates(bid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, be.roll_number, be.enrollment_date, be.status as enrollment_status 
    FROM batch_enrollments be 
    JOIN candidates c ON c.id = be.candidate_id 
    WHERE be.batch_id = ? AND be.status = 'Active' 
    ORDER BY be.id ASC
    """, (bid,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_candidate_batch(cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.*, be.roll_number, be.enrollment_date 
    FROM batch_enrollments be 
    JOIN batches b ON b.id = be.batch_id 
    WHERE be.candidate_id = ? AND be.status = 'Active'
    """, (cid,))
    row = cursor.fetchone()
    conn.close()
    return row

def enroll_candidate_in_batch(bid, cid, roll_number=None, remarks=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if not roll_number:
        cursor.execute("SELECT COUNT(*) as cnt FROM batch_enrollments WHERE batch_id = ?", (bid,))
        row = cursor.fetchone()
        cnt = (row["cnt"] if isinstance(row, dict) else row[0]) + 1
        roll_number = f"B{bid:02d}-{cnt:02d}"
        
    date_now = datetime.now().strftime("%Y-%m-%d")
    
    if IS_POSTGRES:
        cursor.execute("""
        INSERT INTO batch_enrollments (batch_id, candidate_id, enrollment_date, roll_number, status, remarks)
        VALUES (?, ?, ?, ?, 'Active', ?)
        ON CONFLICT (batch_id, candidate_id) DO UPDATE 
        SET status = 'Active', roll_number = EXCLUDED.roll_number, enrollment_date = EXCLUDED.enrollment_date
        """, (bid, cid, date_now, roll_number, remarks))
    else:
        cursor.execute("""
        INSERT OR REPLACE INTO batch_enrollments (batch_id, candidate_id, enrollment_date, roll_number, status, remarks)
        VALUES (?, ?, ?, ?, 'Active', ?)
        """, (bid, cid, date_now, roll_number, remarks))
        
    cursor.execute("UPDATE candidates SET admission_status = 'Enrolled' WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return True

def unenroll_candidate_from_batch(bid, cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_enrollments WHERE batch_id = ? AND candidate_id = ?", (bid, cid))
    cursor.execute("UPDATE candidates SET admission_status = 'Pending' WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    return True

def get_stats(center=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as cnt FROM candidates")
    r1 = cursor.fetchone()
    total_candidates = r1["cnt"] if isinstance(r1, dict) else r1[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM candidates WHERE admission_status = 'Enrolled'")
    r2 = cursor.fetchone()
    enrolled_count = r2["cnt"] if isinstance(r2, dict) else r2[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM candidates WHERE admission_status = 'Pending'")
    r3 = cursor.fetchone()
    pending_count = r3["cnt"] if isinstance(r3, dict) else r3[0]

    cursor.execute("SELECT COUNT(*) as cnt FROM batches")
    r4 = cursor.fetchone()
    total_batches = r4["cnt"] if isinstance(r4, dict) else r4[0]

    cursor.execute("SELECT SUM(fee_paid) as paid, SUM(total_course_fee) as tot, SUM(fee_balance) as bal FROM candidates")
    fee_row = cursor.fetchone()
    total_fee_collected = (fee_row.get("paid") if isinstance(fee_row, dict) else fee_row[0]) or 0.0
    total_course_fees = (fee_row.get("tot") if isinstance(fee_row, dict) else fee_row[1]) or 0.0
    total_fee_pending = (fee_row.get("bal") if isinstance(fee_row, dict) else fee_row[2]) or 0.0

    cursor.execute("""
        SELECT course, COUNT(*) as count 
        FROM candidates 
        GROUP BY course 
        ORDER BY count DESC
    """)
    course_stats = cursor.fetchall()

    conn.close()
    return {
        "total_candidates": total_candidates,
        "enrolled_count": enrolled_count,
        "pending_count": pending_count,
        "total_batches": total_batches,
        "total_fee_collected": total_fee_collected,
        "total_course_fees": total_course_fees,
        "total_fee_pending": total_fee_pending,
        "course_stats": course_stats
    }


def migrate_passwords_to_ascii():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash FROM users")
    rows = cursor.fetchall()
    
    total = len(rows)
    migrated = 0
    already_ascii = 0
    skipped = []
    
    for r in rows:
        uid = r["id"] if isinstance(r, dict) else r[0]
        uname = r["username"] if isinstance(r, dict) else r[1]
        p_val = r["password_hash"] if isinstance(r, dict) else r[2]
        
        if is_already_ascii_format(p_val):
            already_ascii += 1
        elif p_val:
            new_ascii = password_to_ascii(p_val)
            cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_ascii, uid))
            migrated += 1
        else:
            skipped.append(f"User ID {uid} ({uname}): empty password")
            
    conn.commit()
    conn.close()
    return {
        "total": total,
        "migrated": migrated,
        "already_ascii": already_ascii,
        "skipped": skipped
    }

def create_enquiry(full_name: str, mobile: str, course: str, district: str) -> dict:
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = parse_placeholder(cursor)
    query = f"INSERT INTO enquiries (full_name, mobile, course, district) VALUES ({ph}, {ph}, {ph}, {ph})"
    cursor.execute(query, (full_name, mobile, course, district))
    eid = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"id": eid, "full_name": full_name, "mobile": mobile, "course": course, "district": district, "status": "Pending"}

def get_all_enquiries() -> list:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, full_name, mobile, course, district, status, created_at FROM enquiries ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    enquiries = []
    for r in rows:
        if isinstance(r, dict):
            enquiries.append({
                "id": r.get("id"),
                "full_name": r.get("full_name") or "Applicant",
                "mobile": r.get("mobile") or "",
                "course": r.get("course") or "Skill Training",
                "district": r.get("district") or "-",
                "status": r.get("status") or "Pending",
                "created_at": str(r.get("created_at") or "Recently")
            })
        else:
            enquiries.append({
                "id": r[0],
                "full_name": r[1] or "Applicant",
                "mobile": r[2] or "",
                "course": r[3] or "Skill Training",
                "district": r[4] or "-",
                "status": r[5] or "Pending",
                "created_at": str(r[6] or "Recently")
            })
    return enquiries

def update_enquiry_status(eid: int, status: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = parse_placeholder(cursor)
    cursor.execute(f"UPDATE enquiries SET status = {ph} WHERE id = {ph}", (status, eid))
    conn.commit()
    conn.close()

def delete_enquiry(eid: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    ph = parse_placeholder(cursor)
    cursor.execute(f"DELETE FROM enquiries WHERE id = {ph}", (eid,))
    conn.commit()
    conn.close()

def get_all_users_for_superadmin():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, role, mobile, email, center_name, plain_password, status, created_at FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    
    users_list = []
    for r in rows:
        if isinstance(r, dict):
            users_list.append({
                "id": r.get("id"),
                "username": r.get("username"),
                "full_name": r.get("full_name"),
                "role": r.get("role"),
                "mobile": r.get("mobile") or "-",
                "email": r.get("email") or "-",
                "center_name": r.get("center_name") or "Main Campus",
                "plain_password": r.get("plain_password") or "••••••••",
                "status": r.get("status") or "active",
                "created_at": str(r.get("created_at") or "Recently")
            })
        else:
            users_list.append({
                "id": r[0],
                "username": r[1],
                "full_name": r[2],
                "role": r[3],
                "mobile": r[4] or "-",
                "email": r[5] or "-",
                "center_name": r[6] or "Main Campus",
                "plain_password": r[7] or "••••••••",
                "status": r[8] or "active",
                "created_at": str(r[9] or "Recently")
            })
    return users_list

def create_user_by_superadmin(data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    username = data.get("username").strip().lower()
    plain_pw = data.get("password", "grtc@123").strip()
    pw_hash = hash_password(plain_pw)
    role = data.get("role", "staff").strip().lower()
    full_name = data.get("full_name", "").strip()
    mobile = data.get("mobile", "").strip()
    email = data.get("email", "").strip()
    center_name = data.get("center_name", "Main Campus").strip()
    
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        raise Exception("Username already exists. Please choose another username.")
        
    cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, plain_password)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, pw_hash, full_name, mobile, email, role, center_name, plain_pw))
    
    conn.commit()
    conn.close()
    return True

def change_user_password_by_superadmin(user_id: int, new_password: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    pw_hash = hash_password(new_password)
    
    cursor.execute("UPDATE users SET password_hash = ?, plain_password = ? WHERE id = ?", (pw_hash, new_password, user_id))
    conn.commit()
    conn.close()
    return True

def delete_user_by_superadmin(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True