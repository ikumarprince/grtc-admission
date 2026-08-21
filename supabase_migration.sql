-- ==============================================================================
-- GRTC SUPABASE (POSTGRESQL) SCHEMA & DEMO DATA MIGRATION SCRIPT
-- Copy and paste this script directly into Supabase SQL Editor & click Run!
-- ==============================================================================

-- 1. Create Enquiries Table
CREATE TABLE IF NOT EXISTS enquiries (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    mobile VARCHAR(50) NOT NULL,
    course VARCHAR(255) NOT NULL,
    district VARCHAR(100),
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Insert Enquiries Demo Leads
INSERT INTO enquiries (full_name, mobile, course, district, status, created_at)
VALUES
  ('Rahul Kumar Sharma', '9876543210', 'Computer IT & Office Automation', 'Patna', 'Pending', NOW()),
  ('Priya Singh', '9304474574', 'Hotel Management & F&B Services', 'Nalanda', 'Contacted', NOW()),
  ('Amit Kumar Verma', '8002143322', 'General Duty Assistant (GDA Nursing)', 'Gaya', 'Pending', NOW()),
  ('Suman Kumari', '9123456789', 'Computer IT & Office Automation', 'Muzaffarpur', 'Admitted', NOW()),
  ('Vikash Roy', '9988776655', 'Hotel Management & F&B Services', 'Darbhanga', 'Pending', NOW())
ON CONFLICT DO NOTHING;

-- 3. Update candidates fee table default constraints
ALTER TABLE candidates ALTER COLUMN total_course_fee SET DEFAULT 400;