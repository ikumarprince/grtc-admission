import os
import io
import csv
import base64
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Body, Header
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import database

app = FastAPI(title="Multi-Role Candidate Admission & Batch Management System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")

os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

database.init_db()

def get_current_user_from_token(auth_token: str):
    if not auth_token:
        return None
    uid = database.get_user_id_from_session(auth_token)
    if not uid:
        return None
    return database.get_user_by_id(uid)

# ================= USER PROFILE & SECURITY APIS =================

@app.post("/api/user/change-password")
async def api_change_user_password(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    
    current_p = payload.get("current_password", "").strip()
    new_p = payload.get("new_password", "").strip()
    confirm_p = payload.get("confirm_password", "").strip()
    
    if not current_p or not new_p or not confirm_p:
        raise HTTPException(status_code=400, detail="All password fields are required.")
        
    if new_p != confirm_p:
        raise HTTPException(status_code=400, detail="New password and confirmation password do not match.")
        
    if current_p == new_p:
        raise HTTPException(status_code=400, detail="New password must be different from current password.")
        
    # Verify current password server-side
    auth_check = database.authenticate_user(user["username"], current_p)
    if not auth_check:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
        
    # Validate length rules (6-12 chars) BEFORE ASCII conversion
    try:
        database.validate_password(new_p)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
        
    # Convert & Update
    database.update_user(user["id"], {"password": new_p})
    return {"status": "success", "message": "Password changed successfully."}

@app.post("/api/user/avatar")
async def api_upload_user_avatar(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
        
    try:
        raw_url = payload.get("profile_picture") or payload.get("photo_url") or ""
        if not raw_url:
            raise HTTPException(status_code=400, detail="Invalid photo data.")
            
        if raw_url.startswith("data:image/"):
            header, base64_str = raw_url.split(",", 1)
            ext = ".jpg"
            if "png" in header: ext = ".png"
            elif "webp" in header: ext = ".webp"
            elif "jpeg" in header or "jpg" in header: ext = ".jpg"
            
            img_data = base64.b64decode(base64_str)
            if len(img_data) > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 5MB.")
                
            safe_fname = f"avatar_user_{user['id']}_{uuid.uuid4().hex[:8]}{ext}"
            save_path = os.path.join(UPLOADS_DIR, safe_fname)
            with open(save_path, "wb") as f:
                f.write(img_data)
            avatar_url = f"/static/uploads/{safe_fname}"
        else:
            avatar_url = raw_url

        updated = database.update_user(user["id"], {"profile_picture": avatar_url})
        return {"status": "success", "profile_picture": avatar_url, "user": updated}
    except HTTPException as he:
        raise he
    except Exception as err:
        return JSONResponse(status_code=500, content={"detail": f"Upload processing error: {str(err)}"})
    except HTTPException as he:
        raise he
    except Exception as err:
        return JSONResponse(status_code=500, content={"detail": f"Upload processing error: {str(err)}"})

# ================= PAGES & NAVIGATION =================

@app.head("/")
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    with open(os.path.join(TEMPLATES_DIR, "home.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/home", response_class=HTMLResponse)
async def serve_home_alias():
    with open(os.path.join(TEMPLATES_DIR, "home.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.head("/healthz")
@app.get("/healthz")
async def health_check():
    return {"status": "healthy"}

@app.get("/login", response_class=HTMLResponse)
async def serve_login():
    with open(os.path.join(TEMPLATES_DIR, "login.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/register", response_class=HTMLResponse)
async def serve_register():
    with open(os.path.join(TEMPLATES_DIR, "register.html"), "r", encoding="utf-8") as f:
        return f.read()

@app.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard():
    with open(os.path.join(TEMPLATES_DIR, "index.html"), "r", encoding="utf-8") as f:
        return f.read()

# ================= AUTHENTICATION APIS =================

@app.post("/api/auth/signup")
async def api_signup(payload: dict = Body(...)):
    username = payload.get("username", "").strip()
    password = payload.get("password", "").strip() or "grtc@123" or "grtc@123"
    full_name = payload.get("full_name", "").strip()
    mobile = payload.get("mobile", "").strip()
    email = payload.get("email", "").strip()
    
    if not username or not password or not full_name:
        raise HTTPException(status_code=400, detail="Name, Username/ID and Password are required.")
    
    try:
        user = database.register_user(
            username=username,
            password=password,
            full_name=full_name,
            mobile=mobile,
            email=email,
            role="student"
        )
        token = database.create_user_session(user["id"])
        return {"status": "success", "token": token, "user": user}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")
async def api_login(payload: dict = Body(...)):
    login_id = payload.get("login_id", "").strip()
    password = payload.get("password", "").strip() or "grtc@123" or "grtc@123"
    
    user = database.authenticate_user(login_id, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid User ID or Password.")
    
    token = database.create_user_session(user["id"])
    return {
        "status": "success",
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
            "center_name": user["center_name"],
            "candidate_id": user["candidate_id"]
        }
    }

@app.get("/api/auth/me")
async def api_get_me(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid.")
    
    # If student, attach candidate & batch details
    candidate = None
    batch = None
    if user["role"] == "student":
        candidate = database.get_candidate_by_user_id(user["id"])
        if candidate:
            batch = database.get_candidate_batch(candidate["id"])
            
    return {"user": user, "candidate": candidate, "batch": batch}

@app.post("/api/auth/logout")
async def api_logout(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    database.delete_user_session(token)
    return {"status": "success"}


@app.get("/api/candidates/check-mobile")
@app.get("/api/public/check-mobile")
async def api_check_mobile(mobile: str = ""):
    return database.check_mobile_registered(mobile)

@app.get("/api/candidates/check-mobile")
@app.get("/api/public/check-mobile")
async def api_check_mobile(mobile: str = ""):
    return database.check_mobile_registered(mobile)

@app.post("/api/public/register-admission")
async def api_public_register_admission(payload: dict = Body(...)):
    full_name = payload.get("full_name", "").strip()
    mobile = payload.get("mobile_no", "").strip()
    email = payload.get("email", "").strip()
    password = payload.get("password", "").strip() or "grtc@123"

    if not full_name or not mobile or not password:
        raise HTTPException(status_code=400, detail="Full Name, Mobile Number and Password are required.")

    # Duplicate mobile check
    mob_check = database.check_mobile_registered(mobile)
    if mob_check.get("registered"):
        c = mob_check["candidate"]
        raise HTTPException(
            status_code=400, 
            detail=f"⚠️ Mobile number {mobile} is already registered with student '{c.get('full_name')}' (Application No: {c.get('application_no')}). Duplicate registration not allowed."
        )

    # 1. Register or find user account
    try:
        user = database.register_user(
            username=mobile,
            password=password,
            full_name=full_name,
            mobile=mobile,
            email=email,
            role="student"
        )
    except ValueError as e:
        existing_user = database.authenticate_user(mobile, password)
        if existing_user:
            user = existing_user
        else:
            raise HTTPException(status_code=400, detail=str(e))

    # 2. Create Candidate record linked to user
    try:
        candidate = database.create_candidate(payload, user_id=user["id"])
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    token = database.create_user_session(user["id"])
    
    return {
        "status": "success",
        "user": user,
        "candidate": candidate,
        "token": token
    }

# ================= STUDENT PORTAL APIS =================

@app.post("/api/student/admission")
async def api_student_submit_admission(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] != "student":
        raise HTTPException(status_code=403, detail="Unauthorized.")
    
    existing = database.get_candidate_by_user_id(user["id"])
    if existing:
        updated = database.update_candidate(existing["id"], payload)
        return {"status": "success", "candidate": updated}
    else:
        created = database.create_candidate(payload, user_id=user["id"])
        return {"status": "success", "candidate": created}

# ================= BATCHES APIS (ADMIN & SUPERADMIN) =================

@app.get("/api/batches")
async def api_get_batches(course: str = "", center: str = "", status: str = ""):
    return database.get_batches(course=course, center=center, status=status)

@app.post("/api/batches")
async def api_create_batch(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["admin", "superadmin", "director"]:
        raise HTTPException(status_code=403, detail="Admin permission required.")
    
    payload["created_by"] = user["full_name"]
    batch = database.create_batch(payload)
    return {"status": "success", "batch": batch}

@app.put("/api/batches/{bid}")
async def api_update_batch(bid: int, payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["admin", "superadmin", "director"]:
        raise HTTPException(status_code=403, detail="Admin permission required.")
    
    updated = database.update_batch(bid, payload)
    return {"status": "success", "batch": updated}

@app.delete("/api/batches/{bid}")
async def api_delete_batch(bid: int, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["admin", "superadmin", "director"]:
        raise HTTPException(status_code=403, detail="Admin permission required.")
    
    database.delete_batch(bid)
    return {"status": "success"}

@app.get("/api/batches/{bid}/candidates")
async def api_get_batch_candidates(bid: int):
    return database.get_batch_candidates(bid)

@app.post("/api/batches/{bid}/enroll")
async def api_enroll_candidate(bid: int, payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["admin", "superadmin", "director"]:
        raise HTTPException(status_code=403, detail="Admin permission required.")
    
    cid = payload.get("candidate_id")
    roll = payload.get("roll_number")
    remarks = payload.get("remarks", "")
    
    database.enroll_candidate_in_batch(bid, cid, roll_number=roll, remarks=remarks)
    return {"status": "success", "message": "Student enrolled in batch successfully"}

@app.post("/api/batches/{bid}/remove")
async def api_remove_candidate(bid: int, payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["admin", "superadmin", "director"]:
        raise HTTPException(status_code=403, detail="Admin permission required.")
    
    cid = payload.get("candidate_id")
    database.remove_candidate_from_batch(bid, cid)
    return {"status": "success", "message": "Student removed from batch"}

# ================= SUPERADMIN USER MANAGEMENT =================

@app.get("/api/superadmin/users")
async def api_get_superadmin_users(role: str = "", authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["superadmin", "director"]:
        raise HTTPException(status_code=403, detail="SuperAdmin or Director permission required.")
    
    users = database.get_all_users(role=role if role else None)
    if user["role"] == "director":
        for u in users:
            if isinstance(u, dict):
                u["password_hash"] = "••••••••"
    return users

@app.post("/api/superadmin/users")
async def api_create_admin_user(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="SuperAdmin permission required.")
    
    try:
        new_user = database.register_user(
            username=payload.get("username"),
            password=payload.get("password"),
            full_name=payload.get("full_name"),
            mobile=payload.get("mobile", ""),
            email=payload.get("email", ""),
            role=payload.get("role", "admin"),
            center_name=payload.get("center_name", "Main Campus")
        )
        return {"status": "success", "user": new_user}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@app.put("/api/superadmin/users/{uid}")
@app.post("/api/superadmin/users/{uid}")
async def api_update_admin_user(uid: int, payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="SuperAdmin permission required.")
    
    try:
        updated = database.update_user(uid, payload)
        return {"status": "success", "user": updated}
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

@app.delete("/api/superadmin/users/{uid}")
async def api_delete_admin_user(uid: int, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="SuperAdmin permission required.")
    
    database.delete_user(uid)
    return {"status": "success"}

@app.get("/api/public/batches")
async def api_get_public_batches():
    try:
        batches = database.get_all_batches()
        public_list = []
        for b in batches:
            if isinstance(b, dict):
                public_list.append({
                    "batch_code": b.get("batch_code"),
                    "batch_name": b.get("batch_name"),
                    "course": b.get("course"),
                    "timing": b.get("timing"),
                    "days": b.get("days"),
                    "status": b.get("status"),
                    "center_name": b.get("center_name", "Main Campus")
                })
        return public_list
    except Exception as e:
        return []

@app.post("/api/public/enquire")
async def api_public_enquire(payload: dict = Body(...)):
    full_name = payload.get("full_name", "").strip()
    mobile = payload.get("mobile", "").strip()
    course = payload.get("course", "").strip()
    district = payload.get("district", "").strip()

    if not full_name or not mobile or not course:
        raise HTTPException(status_code=400, detail="Full name, mobile number, and course selection are required.")

    try:
        # Register inquiry candidate in database
        username = mobile
        password = "grtc@123"
        user = database.register_user(
            username=username,
            password=password,
            full_name=full_name,
            mobile=mobile,
            email=f"{mobile}@grtc.in",
            role="student"
        )
        return {
            "status": "success",
            "message": "Thank you! Your enquiry has been received. Our admission team will contact you shortly.",
            "user_id": user.get("id")
        }
    except Exception as ve:
        # If user already exists, still return success for enquiry
        return {
            "status": "success",
            "message": "Thank you! Your enquiry has been received. Our admission team will contact you shortly."
        }

# ================= CANDIDATES & SETTINGS =================

@app.get("/api/candidates")
async def api_get_candidates(
    search: str = "",
    course: str = "",
    academic_year: str = "",
    status: str = "",
    center: str = "",
    limit: int = 500,
    offset: int = 0
):
    candidates, total = database.get_candidates(
        search=search,
        course=course,
        academic_year=academic_year,
        status=status,
        center=center,
        limit=limit,
        offset=offset
    )
    return {"candidates": candidates, "total": total}

@app.get("/api/candidates/{cid}")
async def api_get_candidate(cid: str):
    candidate = database.get_candidate_by_id(cid)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    batch = database.get_candidate_batch(candidate["id"])
    return {"candidate": candidate, "batch": batch}

@app.post("/api/candidates")
async def api_create_candidate(payload: dict = Body(...)):
    try:
        new_cand = database.create_candidate(payload)
        return {"status": "success", "candidate": new_cand}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/candidates/{cid}")
async def api_update_candidate(cid: int, payload: dict = Body(...)):
    try:
        updated = database.update_candidate(cid, payload)
        return {"status": "success", "candidate": updated}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/candidates/{cid}")
async def api_delete_candidate(cid: int):
    database.delete_candidate(cid)
    return {"status": "success"}

@app.get("/api/stats")
async def api_get_stats(center: str = ""):
    return database.get_stats(center=center)

@app.get("/api/settings")
async def api_get_settings():
    return database.get_settings()


@app.post("/api/superadmin/upi-settings")
async def api_update_upi_settings(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] not in ["superadmin", "director"]:
        raise HTTPException(status_code=403, detail="Unauthorized: Only SuperAdmin or Director has authority to change Payment UPI ID and QR Code.")
    
    new_upi = payload.get("upi_id", "").strip()
    if not new_upi:
        raise HTTPException(status_code=400, detail="UPI ID cannot be empty.")
    
    settings = database.get_settings()
    settings["upi_id"] = new_upi
    database.update_settings(settings)
    
    return {"status": "success", "message": f"UPI ID successfully updated to {new_upi}", "upi_id": new_upi}

@app.post("/api/settings")
async def api_update_settings(payload: dict = Body(...), authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "") if authorization else None
    user = get_current_user_from_token(token)
    if not user or user["role"] != "superadmin":
        raise HTTPException(status_code=403, detail="Forbidden: Only SuperAdmin has authority to change institute settings and payment configuration.")
    database.update_settings(payload)
    return {"status": "success", "message": "Settings updated"}


@app.post("/api/upload-document")
async def api_upload_document(payload: dict = Body(...)):
    file_data = payload.get("data")
    file_name_orig = payload.get("filename", "document.jpg")
    
    if not file_data:
        raise HTTPException(status_code=400, detail="No file data provided")
    
    ext = os.path.splitext(file_name_orig)[1].lower()
    if not ext or ext not in [".jpg", ".jpeg", ".png", ".webp", ".pdf"]:
        ext = ".jpg"
        
    if "," in file_data:
        header, encoded = file_data.split(",", 1)
    else:
        encoded = file_data
        
    filename = f"doc_{uuid.uuid4().hex[:12]}{ext}"
    filepath = os.path.join(UPLOADS_DIR, filename)
    
    with open(filepath, "wb") as fh:
        fh.write(base64.b64decode(encoded))
        
    return {"url": f"/static/uploads/{filename}", "filename": file_name_orig}

@app.post("/api/upload")
async def api_upload_photo(payload: dict = Body(...)):
    image_data = payload.get("image")
    if not image_data:
        raise HTTPException(status_code=400, detail="No image provided")
    
    if "," in image_data:
        header, encoded = image_data.split(",", 1)
    else:
        encoded = image_data
    
    filename = f"cand_{uuid.uuid4().hex[:10]}.jpg"
    filepath = os.path.join(UPLOADS_DIR, filename)
    
    with open(filepath, "wb") as fh:
        fh.write(base64.b64decode(encoded))
    
    return {"url": f"/static/uploads/{filename}"}

@app.get("/api/export/csv")
async def api_export_csv(search: str = "", course: str = "", academic_year: str = "", status: str = "", center: str = ""):
    candidates, _ = database.get_candidates(
        search=search, course=course, academic_year=academic_year, status=status, center=center, limit=5000
    )
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "App No", "Date", "Candidate Name", "Mobile", "Email", "Course", "Branch",
        "Assigned Batch", "Category", "Status", "Center", "Total Fee", "Fee Paid", "Balance"
    ])
    for c in candidates:
        writer.writerow([
            c.get("application_no", ""),
            c.get("admission_date", ""),
            c.get("full_name", ""),
            c.get("mobile_no", ""),
            c.get("email", ""),
            c.get("course", ""),
            c.get("stream_branch", ""),
            c.get("assigned_batch", "Unassigned"),
            c.get("admission_category", ""),
            c.get("admission_status", ""),
            c.get("center_name", ""),
            c.get("total_course_fee", 0),
            c.get("fee_paid", 0),
            c.get("fee_balance", 0)
        ])
    output.seek(0)
    filename = f"admissions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=5000, reload=True)


@app.get("/api/public/enquiries")
async def api_get_public_enquiries():
    return database.get_all_enquiries()