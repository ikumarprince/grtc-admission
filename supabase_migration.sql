-- ==============================================================================
-- GRTC SUPABASE (POSTGRESQL) FULL DATABASE RESET & RE-CREATION SCRIPT
-- Copy and paste this ENTIRE script directly into Supabase SQL Editor & click RUN!
-- ==============================================================================

-- STEP 1: ERASE / DROP ALL EXISTING TABLES & CONSTRAINTS IN SUPABASE
DROP TABLE IF EXISTS batch_enrollments CASCADE;
DROP TABLE IF EXISTS batches CASCADE;
DROP TABLE IF EXISTS candidates CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;
DROP TABLE IF EXISTS enquiries CASCADE;
DROP TABLE IF EXISTS settings CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- STEP 2: RE-CREATE ALL TABLES WITH CLEAN POSTGRESQL SCHEMAS

-- 1. Users Table (Plaintext Passwords)
CREATE TABLE users (
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

-- 2. Candidates Table
CREATE TABLE candidates (
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

-- 3. Batches Table
CREATE TABLE batches (
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

-- 4. Batch Enrollments Table
CREATE TABLE batch_enrollments (
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

-- 5. User Sessions Table
CREATE TABLE user_sessions (
    token VARCHAR(255) PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Website Admission Enquiries Table
CREATE TABLE enquiries (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    mobile VARCHAR(50) NOT NULL,
    course VARCHAR(255) NOT NULL,
    district VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Settings Table
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    config_data TEXT NOT NULL
);

-- STEP 3: SEED CLEAN DEMO USER ACCOUNTS WITH PLAINTEXT PASSWORDS (NO HASHING)

INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, plain_password)
VALUES
  ('superadmin', 'superadminpassword', 'Master SuperAdmin', '8002143322', 'superadmin@grtc.in', 'superadmin', 'Main Campus', 'superadminpassword'),
  ('director', 'directorpassword', 'Executive Director', '9304474574', 'director@grtc.in', 'director', 'Main Campus', 'directorpassword'),
  ('admin', 'adminpassword', 'Patna Center Manager', '9876543210', 'admin@grtc.in', 'admin', 'Main Campus', 'adminpassword'),
  ('staff', 'staffpassword', 'Front Desk Staff Executive', '9123456789', 'staff@grtc.in', 'staff', 'Main Campus', 'staffpassword'),
  ('student', 'grtc@123', 'Demo Student Trainee', '9988776655', 'student@grtc.in', 'student', 'Main Campus', 'grtc@123');

-- STEP 4: SEED DEMO ADMISSION ENQUIRY LEADS

INSERT INTO enquiries (full_name, mobile, course, district, status, created_at)
VALUES
  ('Rahul Kumar Sharma', '9876543210', 'Computer IT & Office Automation', 'Patna', 'Pending', NOW()),
  ('Priya Singh', '9304474574', 'Hotel Management & F&B Services', 'Nalanda', 'Contacted', NOW()),
  ('Amit Kumar Verma', '8002143322', 'General Duty Assistant (GDA Nursing)', 'Gaya', 'Pending', NOW()),
  ('Suman Kumari', '9123456789', 'Computer IT & Office Automation', 'Muzaffarpur', 'Admitted', NOW()),
  ('Vikash Roy', '9988776655', 'Hotel Management & F&B Services', 'Darbhanga', 'Pending', NOW());