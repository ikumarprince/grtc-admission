import sqlite3
import json
import os
import hashlib
import uuid
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "admissions.db")

DEFAULT_SETTINGS = {
    "institution_name": "Gyanoday Rojgar Training Centre",
    "institution_tagline": "Approved by AICTE & UGC Recognized Institution",
    "institution_address": "Knowledge Park Campus, Education Hub, City - 400001",
    "institution_phone": "+91 98765 43210 / +91 12345 67890",
    "institution_email": "admissions@excellence.edu.in",
    "institution_website": "www.excellence.edu.in",
    "institution_code": "EIHE-2026",
    "academic_years": ["2026-2027", "2025-2026", "2024-2025"],
    "courses": [
        {
            "name": "Bachelor of Technology (B.Tech)",
            "duration": "4 Years",
            "branches": ["Computer Science & Engineering", "Information Technology", "Electronics & Comm.", "Mechanical Engg.", "Civil Engg."],
            "default_fee": 85000
        },
        {
            "name": "Bachelor of Computer Applications (BCA)",
            "duration": "3 Years",
            "branches": ["General", "Cloud & AI", "Data Science", "Cyber Security"],
            "default_fee": 55000
        },
        {
            "name": "Bachelor of Business Admin (BBA)",
            "duration": "3 Years",
            "branches": ["Finance", "Marketing", "Human Resources", "International Business"],
            "default_fee": 50000
        },
        {
            "name": "Bachelor of Science (B.Sc)",
            "duration": "3 Years",
            "branches": ["Computer Science", "Information Technology", "Physics", "Mathematics"],
            "default_fee": 45000
        },
        {
            "name": "Master of Business Admin (MBA)",
            "duration": "2 Years",
            "branches": ["Marketing & Sales", "Finance & Banking", "HR Management", "Business Analytics"],
            "default_fee": 95000
        },
        {
            "name": "Master of Computer Applications (MCA)",
            "duration": "2 Years",
            "branches": ["Software Engineering", "AI & ML", "Web & Mobile Dev"],
            "default_fee": 70000
        },
        {
            "name": "Diploma in Polytechnic",
            "duration": "3 Years",
            "branches": ["Computer Engineering", "Electrical Engg", "Civil Engg", "Mechanical Engg"],
            "default_fee": 35000
        }
    ]
}

def hash_password(password: str) -> str:
    return password.strip()

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        mobile TEXT,
        email TEXT,
        role TEXT NOT NULL DEFAULT 'student',
        center_name TEXT DEFAULT 'Main Campus',
        candidate_id INTEGER,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 2. Candidates Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        application_no TEXT UNIQUE NOT NULL,
        admission_date TEXT NOT NULL,
        academic_year TEXT NOT NULL,
        course TEXT NOT NULL,
        stream_branch TEXT,
        semester_year TEXT DEFAULT '1st Semester / 1st Year',
        admission_category TEXT DEFAULT 'General',
        admission_status TEXT DEFAULT 'Pending',
        center_name TEXT DEFAULT 'Main Campus',
        full_name TEXT NOT NULL,
        gender TEXT NOT NULL,
        dob TEXT NOT NULL,
        blood_group TEXT,
        aadhaar_no TEXT,
        nationality TEXT DEFAULT 'Indian',
        religion TEXT,
        mother_tongue TEXT,
        marital_status TEXT DEFAULT 'Single',
        mobile_no TEXT NOT NULL,
        alt_mobile_no TEXT,
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
        mother_mobile TEXT,
        guardian_name TEXT,
        guardian_relation TEXT,
        guardian_mobile TEXT,
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
    )
    """)

    # Check for missing columns in existing database
    cursor.execute("PRAGMA table_info(candidates)")
    cols = [r[1] for r in cursor.fetchall()]
    if "user_id" not in cols:
        cursor.execute("ALTER TABLE candidates ADD COLUMN user_id INTEGER")
    if "center_name" not in cols:
        cursor.execute("ALTER TABLE candidates ADD COLUMN center_name TEXT DEFAULT 'Main Campus'")

    # 3. Batches Table
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
    )
    """)

    # 4. Batch Enrollments Table
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
    )
    """)

    # 5. User Sessions Table (Persistent Auth)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY,
        config_data TEXT NOT NULL
    )
    """)

    cursor.execute("SELECT id FROM settings WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO settings (id, config_data) VALUES (1, ?)",
            (json.dumps(DEFAULT_SETTINGS),)
        )

    # Insert default SuperAdmin user if not exists
    cursor.execute("SELECT id FROM users WHERE role = 'superadmin'")
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "pkpnrj99@gmail.com",
            hash_password("pkpnrj99"),
            "SuperAdmin",
            "9999999999",
            "pkpnrj99@gmail.com",
            "superadmin",
            "Headquarters",
            "active"
        ))

    # Insert default Center Manager if not exists
    cursor.execute("SELECT id FROM users WHERE username = 'manager1'")
    if not cursor.fetchone():
        cursor.execute("""
        INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "manager1",
            hash_password("manager123"),
            "Center Manager - Main",
            "9876543200",
            "manager1@excellence.edu.in",
            "admin",
            "Main Campus",
            "active"
        ))

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
    return row[0] if row else None

def delete_user_session(token):
    if not token:
        return
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()

def authenticate_user(login_id, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    p_hash = hash_password(password.strip())
    clean_id = login_id.strip().lower()
    
    cursor.execute("""
    SELECT * FROM users 
    WHERE (LOWER(username) = ? OR mobile = ? OR LOWER(email) = ?) 
      AND password_hash = ? 
      AND status = 'active'
    """, (clean_id, login_id.strip(), clean_id, p_hash))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def register_user(username=None, password="grtc@123", full_name="", mobile="", email="", role="student", center_name="Main Campus", candidate_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_mob = (mobile or "").strip()
    clean_email = (email or "").strip().lower()
    clean_user = (username or "").strip().lower()
    
    # If no username provided, use mobile or email as login ID
    if not clean_user:
        clean_user = clean_mob if clean_mob else clean_email

    if not clean_mob and not clean_email and not clean_user:
        conn.close()
        raise ValueError("Mobile number or Email address is required for registration.")
        
    cursor.execute('''
    SELECT id FROM users 
    WHERE (LOWER(username) = ? AND ? != '') 
       OR (mobile = ? AND ? != '') 
       OR (LOWER(email) = ? AND ? != '')
    ''', (clean_user, clean_user, clean_mob, clean_mob, clean_email, clean_email))
    
    if cursor.fetchone():
        conn.close()
        raise ValueError("This Mobile number or Email is already registered. Please login with your password.")
        
    p_hash = hash_password(password)
    cursor.execute('''
    INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, candidate_id, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'active')
    ''', (clean_user, p_hash, full_name.strip(), clean_mob, email.strip(), role, center_name, candidate_id))
    
    uid = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_user_by_id(uid)

def get_user_by_id(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, full_name, mobile, email, role, center_name, candidate_id, status, created_at FROM users WHERE id = ?", (uid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users(role=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if role:
        cursor.execute("SELECT id, username, full_name, mobile, email, role, center_name, status, created_at FROM users WHERE role = ? ORDER BY id DESC", (role,))
    else:
        cursor.execute("SELECT id, username, full_name, mobile, email, role, center_name, status, created_at FROM users ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_user(uid, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fields = []
    values = []
    
    if "full_name" in data:
        fields.append("full_name = ?")
        values.append(data["full_name"].strip())
    if "username" in data and data["username"]:
        fields.append("username = ?")
        values.append(data["username"].strip().lower())
    if "mobile" in data:
        fields.append("mobile = ?")
        values.append(data["mobile"].strip())
    if "email" in data:
        fields.append("email = ?")
        values.append(data["email"].strip().lower())
    if "role" in data:
        fields.append("role = ?")
        values.append(data["role"].strip())
    if "center_name" in data:
        fields.append("center_name = ?")
        values.append(data["center_name"].strip())
    if "password" in data and data["password"].strip():
        fields.append("password_hash = ?")
        values.append(data["password"].strip())
    if "status" in data:
        fields.append("status = ?")
        values.append(data["status"].strip())
        
    if not fields:
        conn.close()
        return get_user_by_id(uid)
        
    values.append(uid)
    cursor.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
    conn.commit()
    conn.close()
    return get_user_by_id(uid)

def delete_user(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM user_sessions WHERE user_id = ?", (uid,))
    cursor.execute("DELETE FROM users WHERE id = ? AND role != 'superadmin'", (uid,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

# ================= BATCHES & ENROLLMENT =================

def create_batch(data):
    conn = get_db_connection()
    cursor = conn.cursor()
    code = data.get("batch_code")
    if not code:
        count = cursor.execute("SELECT COUNT(*) FROM batches").fetchone()[0] + 1
        code = f"BAT-{datetime.now().year}-{count:03d}"
    
    cursor.execute("""
    INSERT INTO batches (
        batch_code, batch_name, course, stream_branch, start_date, end_date,
        timing, days, instructor, room_no, max_capacity, status, center_name, created_by
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        code,
        data.get("batch_name", ""),
        data.get("course", ""),
        data.get("stream_branch", ""),
        data.get("start_date", ""),
        data.get("end_date", ""),
        data.get("timing", "09:00 AM - 05:00 PM"),
        data.get("days", "Daily"),
        data.get("instructor", ""),
        data.get("room_no", ""),
        int(data.get("max_capacity") or 40),
        data.get("status", "Running"),
        data.get("center_name", "Main Campus"),
        data.get("created_by", "Admin")
    ))
    
    bid = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_batch_by_id(bid)

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
    
    query += " ORDER BY CAST(REPLACE(REPLACE(b.batch_name, 'Batch ', ''), 'BAT-', '') AS INTEGER) ASC, b.id ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_batch_by_id(bid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.*, (SELECT COUNT(*) FROM batch_enrollments be WHERE be.batch_id = b.id AND be.status = 'Active') as enrolled_count 
    FROM batches b WHERE b.id = ? OR b.batch_code = ?
    """, (bid, bid))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_batch(bid, data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE batches SET
        batch_name = ?, course = ?, stream_branch = ?, start_date = ?, end_date = ?,
        timing = ?, days = ?, instructor = ?, room_no = ?, max_capacity = ?, status = ?, center_name = ?
    WHERE id = ?
    """, (
        data.get("batch_name"), data.get("course"), data.get("stream_branch"),
        data.get("start_date"), data.get("end_date"), data.get("timing"),
        data.get("days"), data.get("instructor"), data.get("room_no"),
        int(data.get("max_capacity") or 40), data.get("status"), data.get("center_name"),
        bid
    ))
    conn.commit()
    conn.close()
    return get_batch_by_id(bid)

def delete_batch(bid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_enrollments WHERE batch_id = ?", (bid,))
    cursor.execute("DELETE FROM batches WHERE id = ?", (bid,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def enroll_candidate_in_batch(batch_id, candidate_id, roll_number=None, remarks=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM batch_enrollments WHERE batch_id = ? AND candidate_id = ?", (batch_id, candidate_id))
    if cursor.fetchone():
        cursor.execute("UPDATE batch_enrollments SET status = 'Active', remarks = ? WHERE batch_id = ? AND candidate_id = ?", (remarks, batch_id, candidate_id))
    else:
        now_date = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
        INSERT INTO batch_enrollments (batch_id, candidate_id, enrollment_date, roll_number, status, remarks)
        VALUES (?, ?, ?, ?, 'Active', ?)
        """, (batch_id, candidate_id, now_date, roll_number, remarks))
        
    cursor.execute("UPDATE candidates SET admission_status = 'Enrolled' WHERE id = ?", (candidate_id,))
    conn.commit()
    conn.close()
    return True

def remove_candidate_from_batch(batch_id, candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_enrollments WHERE batch_id = ? AND candidate_id = ?", (batch_id, candidate_id))
    conn.commit()
    conn.close()
    return True

def get_batch_candidates(batch_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, be.enrollment_date, be.roll_number as batch_roll_no, be.status as enrollment_status
    FROM batch_enrollments be
    JOIN candidates c ON be.candidate_id = c.id
    WHERE be.batch_id = ?
    ORDER BY c.full_name ASC
    """, (batch_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_candidate_batch(candidate_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT b.*, be.enrollment_date, be.roll_number as student_roll, be.status as enrollment_status
    FROM batch_enrollments be
    JOIN batches b ON be.batch_id = b.id
    WHERE be.candidate_id = ? AND be.status = 'Active'
    LIMIT 1
    """, (candidate_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ================= CANDIDATES CRUD =================

def generate_application_no():
    year = datetime.now().year
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM candidates")
    count = cursor.fetchone()[0] + 1
    conn.close()
    return f"ADM-{year}-{count:04d}"

def get_settings():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT config_data FROM settings WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return DEFAULT_SETTINGS

def update_settings(new_settings):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE settings SET config_data = ? WHERE id = 1",
        (json.dumps(new_settings),)
    )
    conn.commit()
    conn.close()
    return True

def create_candidate(data, user_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()

    app_no = data.get("application_no")
    if not app_no or str(app_no).strip() == "":
        app_no = generate_application_no()

    total_fee = float(data.get("total_course_fee") or 0)
    paid = float(data.get("fee_paid") or 0)
    balance = float(data.get("fee_balance", total_fee - paid) or (total_fee - paid))

    max_m = float(data.get("prev_max_marks") or 0)
    obt_m = float(data.get("prev_marks_obtained") or 0)
    if max_m > 0 and obt_m > 0:
        percentage = round((obt_m / max_m) * 100, 2)
    else:
        percentage = float(data.get("prev_percentage") or 0)

    aadhaar_front_url = data.get("aadhaar_front_url", "")
    aadhaar_back_url = data.get("aadhaar_back_url", "")
    marksheet_10th_url = data.get("marksheet_10th_url", "")
    marksheet_12th_url = data.get("marksheet_12th_url", "")
    caste_cert_url = data.get("caste_cert_url", "")
    other_docs = data.get("other_documents_json", "[]")
    if isinstance(other_docs, (list, dict)):
        other_docs = json.dumps(other_docs)

    cursor.execute('''
    INSERT INTO candidates (
        user_id, application_no, admission_date, academic_year, course, stream_branch, semester_year,
        admission_category, admission_status, center_name, full_name, gender, dob, blood_group,
        aadhaar_no, nationality, religion, mother_tongue, marital_status, mobile_no,
        alt_mobile_no, email, current_address, current_city, current_state, current_pincode,
        permanent_address, permanent_city, permanent_state, permanent_pincode,
        father_name, father_occupation, father_mobile, mother_name, mother_occupation,
        mother_mobile, guardian_name, guardian_relation, guardian_mobile, annual_income,
        prev_qualification, prev_school_college, prev_board_university, prev_passing_year,
        prev_roll_no, prev_max_marks, prev_marks_obtained, prev_percentage,
        total_course_fee, fee_paid, fee_balance, payment_mode, payment_ref, payment_date,
        remarks, photo_url, signature_url,
        aadhaar_front_url, aadhaar_back_url, marksheet_10th_url, marksheet_12th_url,
        caste_cert_url, other_documents_json
    ) VALUES (
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
        ?, ?, ?, ?, ?, ?
    )
    ''', (
        user_id,
        app_no,
        data.get("admission_date") or datetime.now().strftime("%Y-%m-%d"),
        data.get("academic_year", "2026-2027"),
        data.get("course", ""),
        data.get("stream_branch", ""),
        data.get("semester_year", "1st Semester / 1st Year"),
        data.get("admission_category", "General"),
        data.get("admission_status", "Pending"),
        data.get("center_name", "Main Campus"),
        data.get("full_name", "").strip(),
        data.get("gender", ""),
        data.get("dob", ""),
        data.get("blood_group", ""),
        data.get("aadhaar_no", "").strip(),
        data.get("nationality", "Indian"),
        data.get("religion", ""),
        data.get("mother_tongue", ""),
        data.get("marital_status", "Single"),
        data.get("mobile_no", "").strip(),
        data.get("alt_mobile_no", "").strip(),
        data.get("email", "").strip(),
        data.get("current_address", ""),
        data.get("current_city", ""),
        data.get("current_state", ""),
        data.get("current_pincode", ""),
        data.get("permanent_address", ""),
        data.get("permanent_city", ""),
        data.get("permanent_state", ""),
        data.get("permanent_pincode", ""),
        data.get("father_name", ""),
        data.get("father_occupation", ""),
        data.get("father_mobile", ""),
        data.get("mother_name", ""),
        data.get("mother_occupation", ""),
        data.get("mother_mobile", ""),
        data.get("guardian_name", ""),
        data.get("guardian_relation", ""),
        data.get("guardian_mobile", ""),
        float(data.get("annual_income") or 0),
        data.get("prev_qualification", ""),
        data.get("prev_school_college", ""),
        data.get("prev_board_university", ""),
        data.get("prev_passing_year", ""),
        data.get("prev_roll_no", ""),
        max_m,
        obt_m,
        percentage,
        total_fee,
        paid,
        balance,
        data.get("payment_mode", "Cash"),
        data.get("payment_ref", ""),
        data.get("payment_date") or datetime.now().strftime("%Y-%m-%d"),
        data.get("remarks", ""),
        data.get("photo_url", ""),
        data.get("signature_url", ""),
        aadhaar_front_url,
        aadhaar_back_url,
        marksheet_10th_url,
        marksheet_12th_url,
        caste_cert_url,
        other_docs
    ))

    cid = cursor.lastrowid
    if user_id:
        cursor.execute("UPDATE users SET candidate_id = ? WHERE id = ?", (cid, user_id))
        
    conn.commit()
    conn.close()
    return get_candidate_by_id(cid)

def get_candidates(search="", course="", academic_year="", status="", center="", limit=500, offset=0):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT c.*, (SELECT b.batch_name FROM batch_enrollments be JOIN batches b ON be.batch_id = b.id WHERE be.candidate_id = c.id AND be.status = 'Active' LIMIT 1) as assigned_batch FROM candidates c WHERE 1=1"
    params = []

    if search:
        query += " AND (c.full_name LIKE ? OR c.application_no LIKE ? OR c.mobile_no LIKE ? OR c.email LIKE ? OR c.aadhaar_no LIKE ?)"
        s = f"%{search}%"
        params.extend([s, s, s, s, s])

    if course:
        query += " AND c.course = ?"
        params.append(course)

    if academic_year:
        query += " AND c.academic_year = ?"
        params.append(academic_year)

    if status:
        query += " AND c.admission_status = ?"
        params.append(status)

    if center:
        query += " AND c.center_name = ?"
        params.append(center)

    query += " ORDER BY c.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    count_query = "SELECT COUNT(*) FROM candidates WHERE 1=1"
    count_params = []
    if search:
        count_query += " AND (full_name LIKE ? OR application_no LIKE ? OR mobile_no LIKE ? OR email LIKE ? OR aadhaar_no LIKE ?)"
        s = f"%{search}%"
        count_params.extend([s, s, s, s, s])
    if course:
        count_query += " AND course = ?"
        count_params.append(course)
    if academic_year:
        count_query += " AND academic_year = ?"
        count_params.append(academic_year)
    if status:
        count_query += " AND admission_status = ?"
        count_params.append(status)
    if center:
        count_query += " AND center_name = ?"
        count_params.append(center)

    cursor.execute(count_query, count_params)
    total_count = cursor.fetchone()[0]

    conn.close()
    return [dict(r) for r in rows], total_count

def get_candidate_by_id(cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, (SELECT b.batch_name FROM batch_enrollments be JOIN batches b ON be.batch_id = b.id WHERE be.candidate_id = c.id AND be.status = 'Active' LIMIT 1) as assigned_batch 
    FROM candidates c 
    WHERE c.id = ? OR c.application_no = ?
    """, (cid, cid))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_candidate_by_user_id(uid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.*, (SELECT b.batch_name FROM batch_enrollments be JOIN batches b ON be.batch_id = b.id WHERE be.candidate_id = c.id AND be.status = 'Active' LIMIT 1) as assigned_batch 
    FROM candidates c 
    WHERE c.user_id = ?
    """, (uid,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_candidate(cid, data):
    conn = get_db_connection()
    cursor = conn.cursor()

    total_fee = float(data.get("total_course_fee") or 0)
    paid = float(data.get("fee_paid") or 0)
    balance = float(data.get("fee_balance", total_fee - paid) or (total_fee - paid))

    max_m = float(data.get("prev_max_marks") or 0)
    obt_m = float(data.get("prev_marks_obtained") or 0)
    if max_m > 0 and obt_m > 0:
        percentage = round((obt_m / max_m) * 100, 2)
    else:
        percentage = float(data.get("prev_percentage") or 0)

    cursor.execute("""
    UPDATE candidates SET
        admission_date = COALESCE(?, admission_date),
        academic_year = COALESCE(?, academic_year),
        course = COALESCE(?, course),
        stream_branch = COALESCE(?, stream_branch),
        semester_year = COALESCE(?, semester_year),
        admission_category = COALESCE(?, admission_category),
        admission_status = COALESCE(?, admission_status),
        center_name = COALESCE(?, center_name),
        full_name = COALESCE(?, full_name),
        gender = COALESCE(?, gender),
        dob = COALESCE(?, dob),
        blood_group = COALESCE(?, blood_group),
        aadhaar_no = COALESCE(?, aadhaar_no),
        nationality = COALESCE(?, nationality),
        religion = COALESCE(?, religion),
        mother_tongue = COALESCE(?, mother_tongue),
        marital_status = COALESCE(?, marital_status),
        mobile_no = COALESCE(?, mobile_no),
        alt_mobile_no = COALESCE(?, alt_mobile_no),
        email = COALESCE(?, email),
        current_address = COALESCE(?, current_address),
        current_city = COALESCE(?, current_city),
        current_state = COALESCE(?, current_state),
        current_pincode = COALESCE(?, current_pincode),
        permanent_address = COALESCE(?, permanent_address),
        permanent_city = COALESCE(?, permanent_city),
        permanent_state = COALESCE(?, permanent_state),
        permanent_pincode = COALESCE(?, permanent_pincode),
        father_name = COALESCE(?, father_name),
        father_occupation = COALESCE(?, father_occupation),
        father_mobile = COALESCE(?, father_mobile),
        mother_name = COALESCE(?, mother_name),
        mother_occupation = COALESCE(?, mother_occupation),
        mother_mobile = COALESCE(?, mother_mobile),
        guardian_name = COALESCE(?, guardian_name),
        guardian_relation = COALESCE(?, guardian_relation),
        guardian_mobile = COALESCE(?, guardian_mobile),
        annual_income = COALESCE(?, annual_income),
        prev_qualification = COALESCE(?, prev_qualification),
        prev_school_college = COALESCE(?, prev_school_college),
        prev_board_university = COALESCE(?, prev_board_university),
        prev_passing_year = COALESCE(?, prev_passing_year),
        prev_roll_no = COALESCE(?, prev_roll_no),
        prev_max_marks = ?,
        prev_marks_obtained = ?,
        prev_percentage = ?,
        total_course_fee = ?,
        fee_paid = ?,
        fee_balance = ?,
        payment_mode = COALESCE(?, payment_mode),
        payment_ref = COALESCE(?, payment_ref),
        payment_date = COALESCE(?, payment_date),
        remarks = COALESCE(?, remarks),
        photo_url = COALESCE(?, photo_url),
        signature_url = COALESCE(?, signature_url),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (
        data.get("admission_date"),
        data.get("academic_year"),
        data.get("course"),
        data.get("stream_branch"),
        data.get("semester_year"),
        data.get("admission_category"),
        data.get("admission_status"),
        data.get("center_name"),
        data.get("full_name"),
        data.get("gender"),
        data.get("dob"),
        data.get("blood_group"),
        data.get("aadhaar_no"),
        data.get("nationality"),
        data.get("religion"),
        data.get("mother_tongue"),
        data.get("marital_status"),
        data.get("mobile_no"),
        data.get("alt_mobile_no"),
        data.get("email"),
        data.get("current_address"),
        data.get("current_city"),
        data.get("current_state"),
        data.get("current_pincode"),
        data.get("permanent_address"),
        data.get("permanent_city"),
        data.get("permanent_state"),
        data.get("permanent_pincode"),
        data.get("father_name"),
        data.get("father_occupation"),
        data.get("father_mobile"),
        data.get("mother_name"),
        data.get("mother_occupation"),
        data.get("mother_mobile"),
        data.get("guardian_name"),
        data.get("guardian_relation"),
        data.get("guardian_mobile"),
        float(data.get("annual_income") or 0),
        data.get("prev_qualification"),
        data.get("prev_school_college"),
        data.get("prev_board_university"),
        data.get("prev_passing_year"),
        data.get("prev_roll_no"),
        max_m,
        obt_m,
        percentage,
        total_fee,
        paid,
        balance,
        data.get("payment_mode"),
        data.get("payment_ref"),
        data.get("payment_date"),
        data.get("remarks"),
        data.get("photo_url"),
        data.get("signature_url"),
        cid
    ))
    conn.commit()
    conn.close()
    return get_candidate_by_id(cid)

def delete_candidate(cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM batch_enrollments WHERE candidate_id = ?", (cid,))
    cursor.execute("DELETE FROM candidates WHERE id = ?", (cid,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_stats(center=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    where_center = " WHERE center_name = ?" if center else ""
    params = [center] if center else []
    
    cursor.execute(f"SELECT COUNT(*) FROM candidates {where_center}", params)
    total_candidates = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM candidates WHERE admission_status = 'Enrolled' {'AND center_name = ?' if center else ''}", params)
    enrolled_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM candidates WHERE admission_status = 'Pending' {'AND center_name = ?' if center else ''}", params)
    pending_count = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM batches {'WHERE center_name = ?' if center else ''}", params)
    total_batches = cursor.fetchone()[0]

    cursor.execute(f"SELECT SUM(fee_paid), SUM(total_course_fee), SUM(fee_balance) FROM candidates {where_center}", params)
    fee_row = cursor.fetchone()
    total_fee_collected = fee_row[0] or 0.0
    total_course_fees = fee_row[1] or 0.0
    total_fee_pending = fee_row[2] or 0.0

    cursor.execute(f"""
        SELECT course, COUNT(*) as count 
        FROM candidates {where_center}
        GROUP BY course 
        ORDER BY count DESC
    """, params)
    course_stats = [dict(r) for r in cursor.fetchall()]

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
