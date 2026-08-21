-- ==============================================================================
-- GRTC SUPABASE (POSTGRESQL) SCHEMA & ALL 5 USER ROLES DEMO ACCOUNTS
-- Copy and paste this script directly into Supabase SQL Editor & click RUN!
-- ==============================================================================

-- 1. Create Users Table in Supabase PostgreSQL
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

-- Ensure plain_password column exists
ALTER TABLE users ADD COLUMN IF NOT EXISTS plain_password TEXT;

-- 2. Insert Demo Accounts for ALL 5 User Roles into Supabase
INSERT INTO users (username, password_hash, full_name, mobile, email, role, center_name, plain_password)
VALUES
  ('superadmin', '74a6b2edeead0b25e791223e7f457e5d26305a415a772f4f2c5e5095368a5a40', 'Master SuperAdmin', '8002143322', 'superadmin@grtc.in', 'superadmin', 'Main Campus', 'superadminpassword'),
  ('director', 'd710ee9d34208a0d0a0b68636b060d4b971a1c3d1f3f4c6e9a6b1c4e7f2a1b0c', 'Executive Director', '9304474574', 'director@grtc.in', 'director', 'Main Campus', 'directorpassword'),
  ('admin', 'f1df30e8c89b33a08eb675c97d6d538e12d1b827e8a939f72740263f350c37ad', 'Patna Center Manager', '9876543210', 'admin@grtc.in', 'admin', 'Main Campus', 'adminpassword'),
  ('staff', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'Front Desk Staff Executive', '9123456789', 'staff@grtc.in', 'staff', 'Main Campus', 'staffpassword'),
  ('student', 'd8c3a936a718b5387b920ef1e8932ef2f05b0c96c429c6934c9c1ef34a1a3b5c', 'Demo Student Trainee', '9988776655', 'student@grtc.in', 'student', 'Main Campus', 'grtc@123')
ON CONFLICT (username) DO UPDATE 
SET password_hash = EXCLUDED.password_hash, plain_password = EXCLUDED.plain_password;

-- 3. Create Enquiries Table in Supabase
CREATE TABLE IF NOT EXISTS enquiries (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    mobile VARCHAR(50) NOT NULL,
    course VARCHAR(255) NOT NULL,
    district VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Insert Enquiries Demo Leads
INSERT INTO enquiries (full_name, mobile, course, district, status, created_at)
VALUES
  ('Rahul Kumar Sharma', '9876543210', 'Computer IT & Office Automation', 'Patna', 'Pending', NOW()),
  ('Priya Singh', '9304474574', 'Hotel Management & F&B Services', 'Nalanda', 'Contacted', NOW()),
  ('Amit Kumar Verma', '8002143322', 'General Duty Assistant (GDA Nursing)', 'Gaya', 'Pending', NOW()),
  ('Suman Kumari', '9123456789', 'Computer IT & Office Automation', 'Muzaffarpur', 'Admitted', NOW()),
  ('Vikash Roy', '9988776655', 'Hotel Management & F&B Services', 'Darbhanga', 'Pending', NOW())
ON CONFLICT DO NOTHING;