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
    "institution_phone": "",
    "institution_email": "",
    "institution_code": "GRTC-PATNA",
    "academic_years": ["2026-2027", "2025-2026", "2024-2025"],
    "courses": [
        {"name": "Computer", "duration": "6 Months", "branches": [], "default_fee": 4000},
        {"name": "Hotel Management", "duration": "1 Year", "branches": [], "default_fee": 4000},
        {"name": "GDA", "duration": "6 Months", "branches": [], "default_fee": 4000}
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
        try:
            conn = psycopg2.connect(DATABASE_URL)
        except Exception:
            if "sslmode=" not in DATABASE_URL:
                sep = "&" if "?" in DATABASE_URL else "?"
                conn = psycopg2.connect(f"{DATABASE_URL}{sep}sslmode=require")
            else:
                raise
        return UniversalConnection(conn, True)
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return UniversalConnection(conn, False)

def hash_password(password: str) -> str:
    return str(password or "").strip()

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if IS_POSTGRES:
        # PostgreSQL Schema
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            mobile VARCHAR(50),
            email VARCHAR(255),
            role VARCHAR(50) NOT NULL,
            center_name VARCHAR(255) DEFAULT 'Main Campus',
            candidate_id INTEGER,
            status VARCHAR(50) DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

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
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

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
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            config_data TEXT NOT NULL
        );
        """)

    conn.commit()

    # Seed Default Settings
    cursor.execute("SELECT id FROM settings WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO settings (id, config_data) VALUES (1, ?)",
            (json.dumps(DEFAULT_SETTINGS),)
        )

    # Seed Default SuperAdmin
    cursor.execute("SELECT id FROM users WHERE username = 'pkpnrj99@gmail.com' OR email = 'pkpnrj99@gmail.com'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, status)
        VALUES ('pkpnrj99@gmail.com', 'pkpnrj99', 'SuperAdmin', '9999999999', 'pkpnrj99@gmail.com', 'superadmin', 'Main Campus', 'active')
        """)

    # Seed Default Director
    cursor.execute("SELECT id FROM users WHERE username = 'director' OR role = 'director'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, status)
        VALUES ('director', 'director123', 'Director - GRTC', '9800000001', 'director@grtc.edu.in', 'director', 'Main Campus', 'active')
        """)

    # Seed Default Manager
    cursor.execute("SELECT id FROM users WHERE username = 'manager1'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, status)
        VALUES ('manager1', 'manager123', 'Center Manager - Main Campus', '9876543200', 'manager1@excellence.edu.in', 'admin', 'Main Campus', 'active')
        """)

    # Seed Batches 1 to 40 if not exist
    cursor.execute("SELECT COUNT(*) as cnt FROM batches")
    row = cursor.fetchone()
    b_count = row["cnt"] if isinstance(row, dict) else row[0]
    
    if b_count == 0:
        for num in range(1, 41):
            b_name = f"Batch {num}"
            b_code = f"BAT-2026-{num:03d}"
            room = f"Lab {((num % 4) + 1)}"
            timing = "09:00 AM - 05:00 PM"
            days = "Mon to Sat"
            cap = 40
            
            if num <= 28:
                status = "Completed"
                sdate = ""
                edate = ""
            elif num <= 31:
                status = "Running"
                sdate = "2026-08-18" if num == 31 else ("2026-01-01" if num == 29 else "2026-04-01")
                edate = ""
            else:
                status = "Upcoming"
                sdate = ""
                edate = ""

            cursor.execute("""
            INSERT INTO batches (batch_code, batch_name, course, stream_branch, start_date, end_date, timing, days, instructor, room_no, max_capacity, status, center_name, created_by)
            VALUES (?, ?, 'Computer', '', ?, ?, ?, ?, 'Faculty', ?, ?, ?, 'Main Campus', 'SuperAdmin')
            """, (b_code, b_name, sdate, edate, timing, days, room, cap, status))

    conn.commit()
    conn.close()

# ================= SESSIONS & AUTH =================

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
    SELECT id, username, full_name, mobile, email, role, center_name, candidate_id, status 
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
    p_raw = str(password).strip()
    clean_id = str(login_id).strip().lower()
    clean_raw_id = str(login_id).strip()
    
    cursor.execute("""
    SELECT * FROM users 
    WHERE (LOWER(username) = ? OR mobile = ? OR LOWER(email) = ?) 
      AND password_hash = ? 
      AND (status = 'active' OR status IS NULL OR status = '')
    """, (clean_id, clean_raw_id, clean_id, p_raw))
    
    row = cursor.fetchone()
    conn.close()
    return row

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
        
    p_store = str(password or "grtc@123").strip()
    
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
    
    allowed = ["full_name", "mobile", "email", "role", "center_name", "status"]
    for k in allowed:
        if k in data:
            fields.append(f"{k} = ?")
            values.append(data[k])
            
    if "password" in data and data["password"]:
        fields.append("password_hash = ?")
        values.append(str(data["password"]).strip())
        
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
    total_fee = float(data.get("total_course_fee", 4000) or 4000)
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
