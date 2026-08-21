function getAuthToken() {
  return localStorage.getItem("agy_auth_token") || localStorage.getItem("authToken") || getAuthToken() || "";
}

// Global App State
var currentUser = null;
var currentToken = localStorage.getItem("agy_auth_token") || localStorage.getItem("authToken") || null;
var currentSettings = null;
var webcamStream = null;
var activeBatchId = null;

// ================= UNIFIED LOGIN & ROLE-BASED PORTAL ROUTER =================
async function loadSettings() {
  try {
    const res = await fetch("/api/settings");
    currentSettings = await res.json();
  } catch (e) {
    console.error("Error loading settings:", e);
  }
}

async function handleLogin() {
  const login_id = document.getElementById("login_id")?.value?.trim();
  const password = document.getElementById("login_password")?.value?.trim();

  if (!login_id || !password) {
    alert("⚠️ Kripya Mobile / Email / User ID aur Password enter karein.");
    return;
  }

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ login_id, password })
    });

    const data = await res.json();
    if (res.ok) {
      currentToken = data.token;
      currentUser = data.user;
      localStorage.setItem("agy_auth_token", currentToken);

      // Redirect to /dashboard where role-based page automatically renders!
      if (window.location.pathname === "/login" || window.location.pathname === "/") {
        window.location.href = "/dashboard";
      } else {
        await checkAuth();
      }
    } else {
      alert("❌ Login Failed: " + (data.detail || "Invalid credentials"));
    }
  } catch (err) {
    alert("Connection error: " + err.message);
  }
}

function renderAppForRole(data) {
  const user = data.user;
  const role = (user.role || "").toLowerCase();

  // Show header user profile
  const headerUserBar = document.getElementById("header_user_bar");
  if (headerUserBar) {
    headerUserBar.style.display = "flex";
    document.getElementById("header_user_name").innerText = user.full_name || user.username;
    document.getElementById("header_user_id").innerText = `ID: ${user.username} (${user.mobile || ''})`;
    const rolePill = document.getElementById("header_user_role");
    if (rolePill) {
      rolePill.innerText = role.toUpperCase();
      rolePill.className = `role-pill ${role}`;
    }
  }

  const authView = document.getElementById("auth_view");
  if (authView) authView.style.display = "none";

  const mainView = document.getElementById("main_app_view");
  if (mainView) mainView.style.display = "block";

  // Hide all portal views first
  const portalStudent = document.getElementById("portal_student");
  const portalAdmin = document.getElementById("portal_admin");
  const portalSuperadmin = document.getElementById("portal_superadmin");

  if (portalStudent) portalStudent.style.display = "none";
  if (portalAdmin) portalAdmin.style.display = "none";
  if (portalSuperadmin) portalSuperadmin.style.display = "none";

  // Open the EXACT matching portal based on role:
  if (role === "superadmin") {
    // 👑 MASTER SUPERADMIN PORTAL
    if (portalSuperadmin) portalSuperadmin.style.display = "block";
    loadSuperAdminDashboard();
    if (document.getElementById("sa_upi_id") && currentSettings && currentSettings.upi_id) {
      document.getElementById("sa_upi_id").value = currentSettings.upi_id;
    }
  } else if (role === "director") {
    // ⭐ EXECUTIVE DIRECTOR PORTAL (Full Authority, Reports & UPI Settings)
    if (portalSuperadmin) portalSuperadmin.style.display = "block";
    loadSuperAdminDashboard();
    if (document.getElementById("sa_upi_card")) document.getElementById("sa_upi_card").style.display = "block";
  } else if (role === "director") {
    // ⭐ EXECUTIVE DIRECTOR PORTAL (Full Authority, Reports & UPI Settings)
    if (portalSuperadmin) portalSuperadmin.style.display = "block";
    loadSuperAdminDashboard();
    if (document.getElementById("sa_upi_card")) document.getElementById("sa_upi_card").style.display = "block";
  } else if (role === "admin" || role === "manager") {
    // 👔 CENTER MANAGER / ADMIN PORTAL
    if (portalAdmin) portalAdmin.style.display = "block";
    loadAdminDashboard();
  } else {
    // 🎓 STUDENT / CANDIDATE PORTAL
    if (portalStudent) portalStudent.style.display = "block";
    renderStudentDashboard(data);
  }
}



// Initialize on Load
document.addEventListener("DOMContentLoaded", async () => {
  await loadSettings();

  const path = window.location.pathname;

  if (currentToken) {
    await checkAuth();
  } else {
    // If not logged in and on dashboard, redirect to login
    if (path === "/dashboard") {
      window.location.href = "/login";
    }
  }

  setupAutoCalculations();
});

// Check Authentication Session
async function checkAuth() {
  try {
    const res = await fetch("/api/auth/me", {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });

    if (res.ok) {
      const data = await res.json();
      currentUser = data.user;

      const path = window.location.pathname;
      if (path === "/" || path === "/login" || path === "/register") {
        window.location.href = "/dashboard";
        return;
      }

      renderAppForRole(data);
    } else {
      logoutUser();
    }
  } catch (err) {
    logoutUser();
  }
}

async function logoutUser() {
  if (currentToken) {
    try {
      await fetch("/api/auth/logout", {
        method: "POST",
        headers: { "Authorization": `Bearer ${currentToken}` }
      });
    } catch (e) { }
  }
  currentToken = null;
  currentUser = null;
  localStorage.removeItem("agy_auth_token");

  if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
    window.location.href = "/login";
  }
}

// ================= 1. STUDENT PORTAL LOGIC =================

function renderStudentDashboard(data) {
  const cand = data.candidate;
  const batch = data.batch;

  // Status Badge
  const statusEl = document.getElementById("stu_status_badge");
  const formCardTitle = document.getElementById("stu_form_title");

  if (cand) {
    statusEl.innerText = cand.admission_status || "Pending";
    statusEl.className = `badge badge-${(cand.admission_status || "pending").toLowerCase()}`;
    formCardTitle.innerText = `My Admission Form (${cand.application_no})`;

    // Pre-populate candidate form
    for (const [key, val] of Object.entries(cand)) {
      const el = document.getElementById("stu_" + key);
      if (el) el.value = val !== null ? val : "";
    }
    if (cand.photo_url) {
      document.getElementById("stu_photo_preview").innerHTML = `<img src="${cand.photo_url}">`;
      document.getElementById("stu_photo_url").value = cand.photo_url;
    }

    // Populate Course & branches
    populateStudentCourses();
    document.getElementById("stu_course").value = cand.course || "";
    onStudentCourseChange();
    if (cand.stream_branch) document.getElementById("stu_stream_branch").value = cand.stream_branch;

    // Show Printable Slip Button
    document.getElementById("stu_slip_btn").style.display = "inline-flex";
  } else {
    statusEl.innerText = "Form Incomplete";
    statusEl.className = "badge badge-pending";
    formCardTitle.innerText = "Fill New Admission Form";
    populateStudentCourses();
    document.getElementById("stu_slip_btn").style.display = "none";
  }

  // Render My Batch Card
  const batchCard = document.getElementById("stu_batch_card");
  if (batch) {
    batchCard.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
          <h3 style="color: var(--primary); font-size: 1.15rem; font-weight: 700;">${batch.batch_name}</h3>
          <p style="color: var(--text-muted); font-size: 0.85rem;">Batch Code: <strong>${batch.batch_code}</strong> | Course: <strong>${batch.course}</strong></p>
        </div>
        <span class="badge badge-enrolled" style="font-size: 0.8rem;">Enrolled</span>
      </div>
      <div class="form-grid-4" style="margin-top: 1rem; background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid var(--border-color);">
        <div><strong>⏰ Timing:</strong><br>${batch.timing || "N/A"}</div>
        <div><strong>📅 Days:</strong><br>${batch.days || "Mon-Fri"}</div>
        <div><strong>👨‍🏫 Instructor:</strong><br>${batch.instructor || "Assigned Faculty"}</div>
        <div><strong>🏫 Classroom:</strong><br>Room ${batch.room_no || "Lab 1"}</div>
      </div>
    `;
  } else {
    batchCard.innerHTML = `
      <div style="text-align: center; padding: 1.5rem; color: var(--text-muted);">
        <div style="font-size: 2rem; margin-bottom: 6px;">⏳</div>
        <strong>No Batch Assigned Yet</strong>
        <p style="font-size: 0.85rem; margin-top: 4px;">Your center manager will review your admission and allocate your batch soon.</p>
      </div>
    `;
  }
}

function populateStudentCourses() {
  if (!currentSettings || !currentSettings.courses) return;
  const courseSel = document.getElementById("stu_course");
  courseSel.innerHTML = '<option value="">-- Select Course / Program --</option>';
  currentSettings.courses.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.name;
    opt.innerText = c.name;
    courseSel.appendChild(opt);
  });

  const yearSel = document.getElementById("stu_academic_year");
  if (yearSel && currentSettings.academic_years) {
    yearSel.innerHTML = "";
    currentSettings.academic_years.forEach(y => {
      const opt = document.createElement("option");
      opt.value = y;
      opt.innerText = y;
      yearSel.appendChild(opt);
    });
  }
}

function onStudentCourseChange() {
  const cName = document.getElementById("stu_course").value;
  const branchSel = document.getElementById("stu_stream_branch");
  branchSel.innerHTML = '<option value="">-- Select Branch --</option>';
  if (!currentSettings || !cName) return;
  const cObj = currentSettings.courses.find(c => c.name === cName);
  if (cObj && cObj.branches) {
    cObj.branches.forEach(b => {
      const opt = document.createElement("option");
      opt.value = b;
      opt.innerText = b;
      branchSel.appendChild(opt);
    });
  }
  if (cObj && cObj.default_fee && (!document.getElementById("stu_total_course_fee").value || document.getElementById("stu_total_course_fee").value == "0")) {
    document.getElementById("stu_total_course_fee").value = cObj.default_fee;
    calcStudentFeeBalance();
  }
}

function calcStudentFeeBalance() {
  const total = parseFloat(document.getElementById("stu_total_course_fee").value) || 0;
  const paid = parseFloat(document.getElementById("stu_fee_paid").value) || 0;
  document.getElementById("stu_fee_balance").value = Math.max(0, total - paid);
}

async function handleStudentAdmissionSubmit(e) {
  e.preventDefault();
  const form = document.getElementById("student_admission_form");
  const formData = new FormData(form);
  const data = {};
  for (const [k, v] of formData.entries()) {
    data[k.replace("stu_", "")] = v;
  }

  try {
    const res = await fetch("/api/student/admission", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    if (res.ok) {
      alert("Admission Details Saved Successfully!");
      await checkAuth();
    } else {
      alert("Error: " + (result.detail || "Could not save details"));
    }
  } catch (err) {
    alert("Connection error: " + err.message);
  }
}

// Student Slip Modal
async function openStudentSlipModal() {
  if (!currentUser) return;
  try {
    const res = await fetch("/api/auth/me", {
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    const data = await res.json();
    if (data.candidate) {
      renderSlipContent(data.candidate, data.batch);
      document.getElementById("slip_modal").classList.add("active");
    }
  } catch (err) {
    alert("Error loading slip: " + err.message);
  }
}

// ================= 2. ADMIN (CENTER MANAGER) PORTAL LOGIC =================

async function loadAdminDashboard() {
  await loadAdminStats();
  await loadAdminBatches();
  await loadAdminCandidates();
}

async function loadAdminStats() {
  try {
    const res = await fetch(`/api/stats?center=${encodeURIComponent(currentUser.center_name || "")}`);
    const stats = await res.json();
    document.getElementById("adm_stat_total").innerText = stats.total_candidates || 0;
    document.getElementById("adm_stat_enrolled").innerText = stats.enrolled_count || 0;
    document.getElementById("adm_stat_batches").innerText = stats.total_batches || 0;
    document.getElementById("adm_stat_fee").innerText = "₹" + (stats.total_fee_collected || 0).toLocaleString("en-IN");
  } catch (err) {
    console.error("Admin stats error:", err);
  }
}

async function loadAdminBatches() {
  try {
    const res = await fetch('/api/batches');
    let batches = await res.json();

    // Sort all batches numerically (Batch 1 -> Batch 40)
    batches.sort((a, b) => {
      const numA = parseInt(String(a.batch_name || "").replace(/[^0-9]/g, "")) || a.id;
      const numB = parseInt(String(b.batch_name || "").replace(/[^0-9]/g, "")) || b.id;
      return numA - numB;
    });

    const runningBatches = batches.filter(b => (b.status || "").toLowerCase() === "running");
    const upcomingBatches = batches.filter(b => (b.status || "").toLowerCase() === "upcoming");
    const completedBatches = batches.filter(b => (b.status || "").toLowerCase() === "completed");

    // Update Section Counters
    if (document.getElementById("cnt_running_batches")) document.getElementById("cnt_running_batches").innerText = runningBatches.length;
    if (document.getElementById("cnt_upcoming_batches")) document.getElementById("cnt_upcoming_batches").innerText = upcomingBatches.length;
    if (document.getElementById("cnt_completed_batches")) document.getElementById("cnt_completed_batches").innerText = completedBatches.length;

    // Helper to generate a single batch tile
    function createBatchTileElement(b, statusType) {
      const card = document.createElement("div");
      card.className = "card batch-card-tile";

      let borderColor = "#16a34a"; // Green for running
      let badgeClass = "badge-approved";
      if (statusType === "upcoming") { borderColor = "#f59e0b"; badgeClass = "badge-pending"; }
      else if (statusType === "completed") { borderColor = "#64748b"; badgeClass = "badge-rejected"; }

      card.style.borderTop = `4px solid ${borderColor}`;
      card.style.cursor = "pointer";
      card.style.transition = "transform 0.18s ease, box-shadow 0.18s ease";
      card.setAttribute("onclick", `openBatchDetailHub(${b.id})`);
      card.onmouseenter = function () { this.style.transform = "translateY(-3px)"; this.style.boxShadow = "0 8px 20px rgba(30, 58, 138, 0.15)"; };
      card.onmouseleave = function () { this.style.transform = "translateY(0)"; this.style.boxShadow = "var(--shadow-sm)"; };

      card.innerHTML = `
        <div class="card-body">
          <div style="display: flex; justify-content:space-between; align-items:flex-start;">
            <div>
              <strong style="color: var(--primary); font-size: 1.1rem; text-decoration: underline; text-decoration-color: #93c5fd;">${b.batch_name} ↗</strong>
              <div style="font-size: 0.8rem; color: var(--text-muted);">${b.batch_code} | ${b.course}</div>
            </div>
            <span class="badge ${badgeClass}">${b.status}</span>
          </div>
          <div style="margin: 10px 0; font-size: 0.83rem;">
            <div>⏰ <strong>Time:</strong> ${b.timing || "09:00 AM - 05:00 PM"} (${b.days || "Mon to Sat"})</div>
            <div>📅 <strong>Duration:</strong> ${b.start_date ? b.start_date : 'N/A'} to ${b.end_date ? b.end_date : 'N/A'}</div>
            <div>👨‍🏫 <strong>Instructor:</strong> ${b.instructor || "Faculty"} | 🏫 <strong>Room:</strong> ${b.room_no || "Lab"}</div>
            <div style="margin-top: 6px;">👥 <strong>Enrolled:</strong> <span style="color: var(--success); font-weight: bold;">${b.enrolled_count} / ${b.max_capacity}</span> students</div>
          </div>
          <div style="display: flex; gap: 6px; margin-top: 12px; border-top: 1px solid var(--border-color); padding-top: 8px; flex-wrap: wrap;">
            <button class="btn btn-outline-primary btn-sm" onclick="event.stopPropagation(); openEnrollModal(${b.id}, '${b.batch_name}')">➕ Enroll Student</button>
            <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); viewBatchStudents(${b.id}, '${b.batch_name}')">👥 View List (${b.enrolled_count})</button>
            <button class="btn btn-outline-secondary btn-sm" onclick="event.stopPropagation(); openEditBatchModal(${b.id})">✏️ Edit Batch</button>
            <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); deleteBatchRecord(${b.id})">🗑️</button>
          </div>
        </div>
      `;
      return card;
    }

    // 1. Render Running Batches (TOP)
    const gridRunning = document.getElementById("grid_running_batches");
    if (gridRunning) {
      gridRunning.innerHTML = "";
      if (runningBatches.length === 0) {
        gridRunning.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 1.2rem; color:var(--text-muted); background:#f0fdf4; border-radius:6px;">No currently running batches.</div>`;
      } else {
        runningBatches.forEach(b => gridRunning.appendChild(createBatchTileElement(b, "running")));
      }
    }

    // 2. Render Upcoming Batches (MIDDLE)
    const gridUpcoming = document.getElementById("grid_upcoming_batches");
    if (gridUpcoming) {
      gridUpcoming.innerHTML = "";
      if (upcomingBatches.length === 0) {
        gridUpcoming.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 1.2rem; color:var(--text-muted); background:#fefce8; border-radius:6px;">No upcoming batches scheduled.</div>`;
      } else {
        upcomingBatches.forEach(b => gridUpcoming.appendChild(createBatchTileElement(b, "upcoming")));
      }
    }

    // 3. Render Completed Batches (BOTTOM)
    const gridCompleted = document.getElementById("grid_completed_batches");
    if (gridCompleted) {
      gridCompleted.innerHTML = "";
      if (completedBatches.length === 0) {
        gridCompleted.innerHTML = `<div style="grid-column: 1/-1; text-align:center; padding: 1.2rem; color:var(--text-muted); background:#f8fafc; border-radius:6px;">No completed batches yet.</div>`;
      } else {
        completedBatches.forEach(b => gridCompleted.appendChild(createBatchTileElement(b, "completed")));
      }
    }

  } catch (err) {
    console.error("Load batches error:", err);
  }
}

async function loadAdminCandidates() {
  const search = document.getElementById("adm_search")?.value || "";
  const status = document.getElementById("adm_status_filter")?.value || "";
  try {
    const res = await fetch(`/api/candidates?search=${encodeURIComponent(search)}&status=${encodeURIComponent(status)}`);
    const data = await res.json();
    renderAdminCandidatesTable(data.candidates);
  } catch (err) {
    console.error("Load candidates error:", err);
  }
}

function renderAdminCandidatesTable(candidates) {
  const tbody = document.getElementById("admin_candidates_tbody");
  tbody.innerHTML = "";

  if (!candidates || candidates.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No student records found.</td></tr>`;
    return;
  }

  candidates.forEach(c => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${c.application_no}</strong></td>
      <td>
        <strong>${c.full_name}</strong><br>
        <small style="color: var(--text-muted);">${c.mobile_no} | ${c.gender}</small>
      </td>
      <td>
        <strong>${c.course}</strong><br>
        <small style="color: var(--text-muted);">${c.stream_branch || "General"}</small>
      </td>
      <td>
        ${c.assigned_batch ? `<span class="badge badge-approved">🎓 ${c.assigned_batch}</span>` : `<span style="color: var(--danger); font-size: 0.78rem;">⚠️ Not Assigned</span>`}
      </td>
      <td>
        <div>Paid: <strong>₹${(c.fee_paid || 0).toLocaleString("en-IN")}</strong></div>
        <small style="color: var(--danger);">Bal: ₹${(c.fee_balance || 0).toLocaleString("en-IN")}</small>
      </td>
      <td><span class="badge badge-${(c.admission_status || "pending").toLowerCase()}">${c.admission_status}</span></td>
      <td>
        <div style="display: flex; gap: 4px;">
          <button class="btn btn-secondary btn-sm" onclick="viewCandidateSlipAdmin(${c.id})">📄 Slip</button>
          <button class="btn btn-outline-primary btn-sm" onclick="editCandidateAdmin(${c.id})">✏️</button>
          <button class="btn btn-danger btn-sm" onclick="deleteCandidateAdmin(${c.id})">🗑️</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Batch Creation Modal
function openCreateBatchModal() {
  populateBatchCourseOptions();
  document.getElementById("create_batch_modal").classList.add("active");
}
function closeCreateBatchModal() {
  document.getElementById("create_batch_modal").classList.remove("active");
}

function populateBatchCourseOptions() {
  if (!currentSettings || !currentSettings.courses) return;
  const sel = document.getElementById("batch_course");
  sel.innerHTML = '<option value="">-- Select Course --</option>';
  currentSettings.courses.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.name;
    opt.innerText = c.name;
    sel.appendChild(opt);
  });
}

async function handleCreateBatchSubmit(e) {
  e.preventDefault();
  const payload = {
    batch_name: document.getElementById("batch_name").value,
    course: document.getElementById("batch_course").value,
    stream_branch: document.getElementById("batch_branch").value,
    timing: document.getElementById("batch_timing").value,
    days: document.getElementById("batch_days").value,
    instructor: document.getElementById("batch_instructor").value,
    room_no: document.getElementById("batch_room").value,
    max_capacity: document.getElementById("batch_capacity").value,
    start_date: document.getElementById("batch_start_date")?.value || "",
    end_date: document.getElementById("batch_end_date")?.value || "",
    center_name: currentUser.center_name || "Main Campus"
  };

  try {
    const res = await fetch("/api/batches", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("Batch Created Successfully!");
      closeCreateBatchModal();
      await loadAdminBatches();
      await loadAdminStats();
    } else {
      alert("Failed to create batch.");
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// Enroll Student Modal
async function openEnrollModal(batchId, batchName) {
  activeBatchId = batchId;
  document.getElementById("enroll_modal_batch_name").innerText = batchName;

  // Load unassigned or all candidates
  const res = await fetch("/api/candidates?limit=200");
  const data = await res.json();
  const select = document.getElementById("enroll_student_select");
  select.innerHTML = '<option value="">-- Select Candidate to Enroll --</option>';

  data.candidates.forEach(c => {
    const opt = document.createElement("option");
    opt.value = c.id;
    opt.innerText = `${c.full_name} (${c.application_no}) - ${c.course} [Current: ${c.assigned_batch || "Unassigned"}]`;
    select.appendChild(opt);
  });

  document.getElementById("enroll_student_modal").classList.add("active");
}
function closeEnrollModal() {
  document.getElementById("enroll_student_modal").classList.remove("active");
}

async function handleEnrollSubmit(e) {
  e.preventDefault();
  const candidate_id = document.getElementById("enroll_student_select").value;
  const roll_number = document.getElementById("enroll_roll_no").value;
  const remarks = document.getElementById("enroll_remarks").value;

  if (!candidate_id) {
    alert("Please select a candidate.");
    return;
  }

  try {
    const res = await fetch(`/api/batches/${activeBatchId}/enroll`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ candidate_id, roll_number, remarks })
    });
    if (res.ok) {
      alert("Student Enrolled in Batch Successfully!");
      closeEnrollModal();
      await loadAdminBatches();
      await loadAdminCandidates();
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// View Students in Batch Modal
async function viewBatchStudents(batchId, batchName) {
  document.getElementById("batch_students_modal_title").innerText = `Enrolled Students in: ${batchName}`;
  const res = await fetch(`/api/batches/${batchId}/candidates`);
  const students = await res.json();

  const tbody = document.getElementById("batch_students_tbody");
  tbody.innerHTML = "";

  if (!students || students.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 1.5rem; color: var(--text-muted);">No students enrolled in this batch yet.</td></tr>`;
  } else {
    students.forEach((s, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${idx + 1}</td>
        <td><strong>${s.application_no}</strong></td>
        <td><strong>${s.full_name}</strong><br><small style="color: var(--text-muted);">${s.mobile_no}</small></td>
        <td>${s.enrollment_date}</td>
        <td>
          <button class="btn btn-danger btn-sm" onclick="removeStudentFromBatch(${batchId}, ${s.id})">❌ Remove</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  document.getElementById("batch_students_modal").classList.add("active");
}
function closeBatchStudentsModal() {
  document.getElementById("batch_students_modal").classList.remove("active");
}

async function removeStudentFromBatch(batchId, candidateId) {
  if (!confirm("Are you sure you want to remove this student from the batch?")) return;
  try {
    const res = await fetch(`/api/batches/${batchId}/remove`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ candidate_id: candidateId })
    });
    if (res.ok) {
      alert("Student removed from batch.");
      closeBatchStudentsModal();
      await loadAdminBatches();
      await loadAdminCandidates();
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// Admin Candidate Actions
async function viewCandidateSlipAdmin(cid) {
  const res = await fetch(`/api/candidates/${cid}`);
  const data = await res.json();
  renderSlipContent(data.candidate, data.batch);
  document.getElementById("slip_modal").classList.add("active");
}

async function deleteCandidateAdmin(cid) {
  if (!confirm("Delete this candidate record?")) return;
  await fetch(`/api/candidates/${cid}`, { method: "DELETE" });
  await loadAdminCandidates();
  await loadAdminStats();
}

async function deleteBatchRecord(bid) {
  if (!confirm("Delete this batch and clear student enrollments?")) return;
  await fetch(`/api/batches/${bid}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${currentToken}` }
  });
  await loadAdminBatches();
  await loadAdminStats();
}

// ================= 3. SUPERADMIN PORTAL LOGIC =================

async function loadSuperAdminDashboard() {
  await loadSuperAdminStats();
  await loadSuperAdminUsers();
}

async function loadSuperAdminStats() {
  try {
    const res = await fetch("/api/stats");
    const stats = await res.json();
    document.getElementById("sa_stat_total").innerText = stats.total_candidates || 0;
    document.getElementById("sa_stat_enrolled").innerText = stats.enrolled_count || 0;
    document.getElementById("sa_stat_batches").innerText = stats.total_batches || 0;
    document.getElementById("sa_stat_fee").innerText = "₹" + (stats.total_fee_collected || 0).toLocaleString("en-IN");
  } catch (err) {
    console.error("SuperAdmin stats error:", err);
  }
}

async function loadSuperAdminUsers() {
  const tbody = document.getElementById("superadmin_users_tbody");
  let data = null;

  // Try 1: Admin API endpoint with Token
  const token = getAuthToken();
  if (token) {
    try {
      const res = await fetch("/api/superadmin/users", {
        headers: { "Authorization": "Bearer " + token }
      });
      if (res.ok) {
        data = await res.json();
      }
    } catch(e1) {
      console.warn("Admin API error, switching to public fallback:", e1);
    }
  }

  // Try 2: Public fallback API endpoint
  if (!data || !Array.isArray(data)) {
    try {
      const resPub = await fetch("/api/public/users");
      if (resPub.ok) {
        data = await resPub.json();
      }
    } catch(e2) {
      console.warn("Public API error:", e2);
    }
  }

  if (data && Array.isArray(data) && data.length > 0) {
    globalAllUsers = data;
    updateUserRoleCounts();
    renderSuperAdminUsersTable();
  } else {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:1.5rem; color:#b45309; font-weight:700;">Click "Refresh Users" button above to load accounts.</td></tr>`;
    }
  }
}

function openCreateAdminModal() {
  document.getElementById("create_admin_modal").classList.add("active");
}
function closeCreateAdminModal() {
  document.getElementById("create_admin_modal").classList.remove("active");
}

async function handleCreateAdminSubmit(e) {
  e.preventDefault();
  const payload = {
    username: document.getElementById("new_admin_username").value.trim(),
    password: document.getElementById("new_admin_password").value.trim(),
    full_name: document.getElementById("new_admin_name").value.trim(),
    mobile: document.getElementById("new_admin_mobile").value.trim(),
    email: document.getElementById("new_admin_email").value.trim(),
    role: "admin",
    center_name: document.getElementById("new_admin_center").value.trim()
  };

  try {
    const res = await fetch("/api/superadmin/users", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("Center Manager (Admin) Created Successfully!");
      closeCreateAdminModal();
      await loadSuperAdminUsers();
    } else {
      const err = await res.json();
      alert("Error: " + (err.detail || "Could not create manager"));
    }
  } catch (err) {
    alert("Connection error: " + err.message);
  }
}

async function deleteUserRecord(uid) {
  if (!confirm("Are you sure you want to delete this user account?")) return;
  try {
    const res = await fetch(`/api/superadmin/users/${uid}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (res.ok) {
      alert("User deleted.");
      await loadSuperAdminUsers();
    }
  } catch (err) {
    alert("Error: " + err.message);
  }
}

// ================= PRINT SLIP RENDERER =================

function renderSlipContent(c, batch) {
  document.getElementById("slip_content").innerHTML = `
    <div class="print-slip-container">
      <div class="print-header">
        <h2>${currentSettings.institution_name || "INSTITUTION NAME"}</h2>
        <p>${currentSettings.institution_tagline || ""}</p>
        <p style="font-size: 0.8rem; margin-top: 3px;">📍 ${currentSettings.institution_address || ""} | 📞 ${currentSettings.institution_phone || ""}</p>
        <div class="print-title-badge">OFFICIAL ADMISSION ACKNOWLEDGEMENT & FEE RECEIPT</div>
      </div>

      <div class="slip-grid">
        <table class="slip-table">
          <tr>
            <td class="lbl">Application / Roll No:</td>
            <td><strong style="color: #1e3a8a; font-size: 1.05rem;">${c.application_no}</strong></td>
            <td class="lbl">Admission Date:</td>
            <td><strong>${c.admission_date}</strong></td>
          </tr>
          <tr>
            <td class="lbl">Candidate Name:</td>
            <td colspan="3"><strong style="font-size: 1.05rem; text-transform: uppercase;">${c.full_name}</strong></td>
          </tr>
          <tr>
            <td class="lbl">Course / Program:</td>
            <td><strong>${c.course}</strong></td>
            <td class="lbl">Stream / Branch:</td>
            <td><strong>${c.stream_branch || "General"}</strong></td>
          </tr>
          <tr>
            <td class="lbl">Allocated Batch:</td>
            <td><strong style="color: #16a34a;">${batch ? batch.batch_name : (c.assigned_batch || "Under Allocation")}</strong></td>
            <td class="lbl">Batch Timing:</td>
            <td>${batch ? batch.timing : "To be notified"}</td>
          </tr>
          <tr>
            <td class="lbl">Contact Mobile:</td>
            <td>${c.mobile_no}</td>
            <td class="lbl">Father's Name:</td>
            <td>${c.father_name || "N/A"}</td>
          </tr>
          <tr style="background: #f1f5f9;">
            <td class="lbl" style="background: #e2e8f0;">Total Course Fee:</td>
            <td><strong>₹${(c.total_course_fee || 0).toLocaleString("en-IN")}</strong></td>
            <td class="lbl" style="background: #e2e8f0;">Fee Paid:</td>
            <td><strong style="color: #16a34a; font-size: 1.05rem;">₹${(c.fee_paid || 0).toLocaleString("en-IN")}</strong></td>
          </tr>
          <tr>
            <td class="lbl">Balance Remaining:</td>
            <td><strong style="color: #dc2626;">₹${(c.fee_balance || 0).toLocaleString("en-IN")}</strong></td>
            <td class="lbl">Payment Mode & Ref:</td>
            <td>${c.payment_mode} (Ref: ${c.payment_ref || "N/A"})</td>
          </tr>
        </table>

        <div class="slip-photo-box">
          ${c.photo_url ? `<img src="${c.photo_url}">` : `<span style="font-size:11px; color:#64748b; text-align:center;">Candidate<br>Photo</span>`}
        </div>
      </div>

      <div class="slip-sign-row">
        <div class="sign-box">Candidate's Signature</div>
        <div class="sign-box">Center Manager / Cashier</div>
        <div class="sign-box">Authorized Admission Officer</div>
      </div>
    </div>
  `;
}

function closeSlipModal() {
  document.getElementById("slip_modal").classList.remove("active");
}
function printAdmissionSlip() {
  window.print();
}

// Photo & Webcam
function handlePhotoUploadStudent(input) {
  if (input.files && input.files[0]) {
    const reader = new FileReader();
    reader.onload = async (e) => {
      const base64Data = e.target.result;
      document.getElementById("stu_photo_preview").innerHTML = `<img src="${base64Data}">`;
      const res = await fetch("/api/upload", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: base64Data })
      });
      const d = await res.json();
      document.getElementById("stu_photo_url").value = d.url;
    };
    reader.readAsDataURL(input.files[0]);
  }
}

async function openWebcamStudent() {
  const modal = document.getElementById("webcam_modal");
  modal.classList.add("active");
  try {
    webcamStream = await navigator.mediaDevices.getUserMedia({ video: true });
    document.getElementById("webcam_video").srcObject = webcamStream;
  } catch (err) {
    alert("Camera access failed. Ensure webcam is connected.");
    closeWebcamModal();
  }
}
function closeWebcamModal() {
  if (webcamStream) {
    webcamStream.getTracks().forEach(t => t.stop());
    webcamStream = null;
  }
  document.getElementById("webcam_modal").classList.remove("active");
}
async function captureWebcamStudent() {
  const video = document.getElementById("webcam_video");
  const canvas = document.createElement("canvas");
  canvas.width = video.videoWidth || 640;
  canvas.height = video.videoHeight || 480;
  canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
  const base64Data = canvas.toDataURL("image/jpeg", 0.9);
  document.getElementById("stu_photo_preview").innerHTML = `<img src="${base64Data}">`;
  closeWebcamModal();

  const res = await fetch("/api/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image: base64Data })
  });
  const d = await res.json();
  document.getElementById("stu_photo_url").value = d.url;
}

// Auto Calculations
function setupAutoCalculations() {
  const maxEl = document.getElementById("stu_prev_max_marks");
  const obtEl = document.getElementById("stu_prev_marks_obtained");
  const percEl = document.getElementById("stu_prev_percentage");

  function calcP() {
    const m = parseFloat(maxEl.value) || 0;
    const o = parseFloat(obtEl.value) || 0;
    if (m > 0 && o >= 0) percEl.value = ((o / m) * 100).toFixed(2);
  }
  if (maxEl && obtEl) {
    maxEl.addEventListener("input", calcP);
    obtEl.addEventListener("input", calcP);
  }

  const totFee = document.getElementById("stu_total_course_fee");
  const paidFee = document.getElementById("stu_fee_paid");
  if (totFee && paidFee) {
    totFee.addEventListener("input", calcStudentFeeBalance);
    paidFee.addEventListener("input", calcStudentFeeBalance);
  }
}

function exportCsvAdmin() {
  window.open("/api/export/csv", "_blank");
}


// ================= SUPERADMIN UPI MANAGEMENT =================
async function saveSuperAdminUpiSettings() {
  const newUpi = document.getElementById("sa_upi_id")?.value?.trim();
  const statusEl = document.getElementById("sa_upi_status");

  if (!newUpi) {
    alert("⚠️ Kripya valid UPI ID enter karein.");
    return;
  }

  try {
    const res = await fetch("/api/superadmin/upi-settings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ upi_id: newUpi })
    });
    const data = await res.json();
    if (res.ok) {
      alert("✅ UPI ID Successfully Updated to: " + newUpi);
      if (statusEl) {
        statusEl.style.color = "var(--success)";
        statusEl.innerHTML = "✅ Active UPI ID: " + newUpi;
      }
      await loadSettings();
    } else {
      alert("❌ Update Failed: " + (data.detail || "Unauthorized"));
    }
  } catch (err) {
    alert("Connection error: " + err.message);
  }
}


// ================= SUPERADMIN 3 SEPARATE USER SECTIONS & EDIT LOGIC =================
var allLoadedUsers = [];

async function loadSuperAdminUsers() {
  const tbody = document.getElementById("superadmin_users_tbody");
  let data = null;

  // Try 1: Admin API endpoint with Token
  const token = getAuthToken();
  if (token) {
    try {
      const res = await fetch("/api/superadmin/users", {
        headers: { "Authorization": "Bearer " + token }
      });
      if (res.ok) {
        data = await res.json();
      }
    } catch(e1) {
      console.warn("Admin API error, switching to public fallback:", e1);
    }
  }

  // Try 2: Public fallback API endpoint
  if (!data || !Array.isArray(data)) {
    try {
      const resPub = await fetch("/api/public/users");
      if (resPub.ok) {
        data = await resPub.json();
      }
    } catch(e2) {
      console.warn("Public API error:", e2);
    }
  }

  if (data && Array.isArray(data) && data.length > 0) {
    globalAllUsers = data;
    updateUserRoleCounts();
    renderSuperAdminUsersTable();
  } else {
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:1.5rem; color:#b45309; font-weight:700;">Click "Refresh Users" button above to load accounts.</td></tr>`;
    }
  }
}

function renderSplitUserTables(users) {
  const managers = users.filter(u => u.role === "admin" || u.role === "manager");
  const students = users.filter(u => u.role === "student");
  const superadmins = users.filter(u => u.role === "superadmin");

  // Update Counters
  if (document.getElementById("count_managers")) document.getElementById("count_managers").innerText = managers.length;
  if (document.getElementById("count_students")) document.getElementById("count_students").innerText = students.length;
  if (document.getElementById("count_superadmins")) document.getElementById("count_superadmins").innerText = superadmins.length;

  // 1. Render Center Managers
  const mgrTbody = document.getElementById("sa_managers_tbody");
  if (mgrTbody) {
    mgrTbody.innerHTML = "";
    if (managers.length === 0) {
      mgrTbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:1.2rem; color:var(--text-muted);">No Center Managers created yet.</td></tr>';
    } else {
      managers.forEach(u => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${u.id}</strong></td>
          <td><strong>${u.username}</strong><br><small style="color:var(--text-muted);">${u.mobile || ''}</small></td>
          <td>${u.full_name}</td>
          <td><span class="role-pill admin">ADMIN</span></td>
          <td>${u.center_name || 'Main Campus'}</td>
          <td><code>${u.password_hash || 'manager123'}</code></td>
          <td style="white-space:nowrap;">
            <button class="btn btn-outline-primary btn-sm" style="margin-right:4px; padding:3px 8px;" onclick="openEditUserModal(${u.id})">✏️ Edit</button>
            <button class="btn btn-danger btn-sm" style="padding:3px 8px;" onclick="deleteUserRecord(${u.id})">🗑️ Delete</button>
          </td>
        `;
        mgrTbody.appendChild(tr);
      });
    }
  }

  // 2. Render Students
  const stuTbody = document.getElementById("sa_students_tbody");
  if (stuTbody) {
    stuTbody.innerHTML = "";
    if (students.length === 0) {
      stuTbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:1.2rem; color:var(--text-muted);">No registered students yet.</td></tr>';
    } else {
      students.forEach(u => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><strong>${u.id}</strong></td>
          <td><strong>${u.username}</strong></td>
          <td>${u.full_name}</td>
          <td><span class="role-pill student">STUDENT</span></td>
          <td><code>${u.password_hash || 'grtc@123'}</code></td>
          <td>${u.center_name || 'Main Campus'}</td>
          <td style="white-space:nowrap;">
            <button class="btn btn-outline-primary btn-sm" style="margin-right:4px; padding:3px 8px;" onclick="openEditUserModal(${u.id})">✏️ Edit</button>
            <button class="btn btn-danger btn-sm" style="padding:3px 8px;" onclick="deleteUserRecord(${u.id})">🗑️ Delete</button>
          </td>
        `;
        stuTbody.appendChild(tr);
      });
    }
  }

  // 3. Render SuperAdmins
  const saTbody = document.getElementById("sa_superadmins_tbody");
  if (saTbody) {
    saTbody.innerHTML = "";
    superadmins.forEach(u => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><strong>${u.id}</strong></td>
        <td><strong>${u.username}</strong></td>
        <td>${u.full_name}</td>
        <td><span class="role-pill superadmin">SUPERADMIN</span></td>
        <td>Headquarters</td>
        <td>${u.mobile || 'N/A'}</td>
        <td>
          <button class="btn btn-outline-primary btn-sm" onclick="openEditUserModal(${u.id})">✏️ Edit</button>
        </td>
      `;
      saTbody.appendChild(tr);
    });
  }
}

function switchSuperAdminUserTab(tab) {
  const tabs = ["managers", "students", "superadmins"];
  tabs.forEach(t => {
    const sec = document.getElementById(`section_${t}_view`);
    const btn = document.getElementById(`tab_btn_${t}`);
    if (t === tab) {
      if (sec) sec.style.display = "block";
      if (btn) { btn.className = "btn btn-primary btn-sm"; }
    } else {
      if (sec) sec.style.display = "none";
      if (btn) { btn.className = "btn btn-outline-primary btn-sm"; }
    }
  });
}

function filterManagerTable() {
  const q = (document.getElementById("search_managers_input")?.value || "").toLowerCase();
  const rows = document.querySelectorAll("#sa_managers_tbody tr");
  rows.forEach(r => {
    r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
  });
}

function filterStudentTable() {
  const q = (document.getElementById("search_students_input")?.value || "").toLowerCase();
  const rows = document.querySelectorAll("#sa_students_tbody tr");
  rows.forEach(r => {
    r.style.display = r.innerText.toLowerCase().includes(q) ? "" : "none";
  });
}

// Edit User Modal Handlers
function openEditUserModal(uid) {
  const user = allLoadedUsers.find(u => u.id === uid);
  if (!user) return;

  document.getElementById("edit_user_id").value = user.id;
  document.getElementById("edit_full_name").value = user.full_name || "";
  document.getElementById("edit_username").value = user.username || "";
  document.getElementById("edit_mobile").value = user.mobile || "";
  document.getElementById("edit_password").value = user.password_hash || "";
  document.getElementById("edit_center_name").value = user.center_name || "Main Campus";
  document.getElementById("edit_role").value = user.role || "student";
  document.getElementById("edit_modal_title").innerText = `✏️ Edit User: ${user.full_name} (${user.role.toUpperCase()})`;

  document.getElementById("edit_user_modal").classList.add("active");
}

function closeEditUserModal() {
  document.getElementById("edit_user_modal").classList.remove("active");
}

async function handleEditUserSubmit(e) {
  e.preventDefault();
  const uid = document.getElementById("edit_user_id").value;
  const payload = {
    full_name: document.getElementById("edit_full_name").value.trim(),
    username: document.getElementById("edit_username").value.trim(),
    mobile: document.getElementById("edit_mobile").value.trim(),
    password: document.getElementById("edit_password").value.trim(),
    center_name: document.getElementById("edit_center_name").value.trim(),
    role: document.getElementById("edit_role").value
  };

  try {
    const res = await fetch(`/api/superadmin/users/${uid}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("✅ User details updated successfully!");
      closeEditUserModal();
      await loadSuperAdminUsers();
    } else {
      const err = await res.json();
      alert("❌ Update failed: " + (err.detail || "Error"));
    }
  } catch (err) {
    alert("Connection error: " + err.message);
  }
}

// Switch to Manager View
function switchToManagerView() {
  const adminPortal = document.getElementById("portal_admin");
  if (adminPortal) {
    adminPortal.style.display = "block";
    loadAdminDashboard();
    adminPortal.scrollIntoView({ behavior: "smooth" });
  }
}

// Navigation Dock Router
function navigatePortalSection(target) {
  const items = document.querySelectorAll(".bottom-nav-item");
  items.forEach(el => el.classList.remove("active"));

  const activeBtn = document.getElementById(`nav_btn_${target}`);
  if (activeBtn) activeBtn.classList.add("active");

  if (target === "dashboard") {
    if (currentUser && currentUser.role === "superadmin") {
      document.getElementById("portal_superadmin").style.display = "block";
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else if (currentUser && (currentUser.role === "admin" || currentUser.role === "manager")) {
      document.getElementById("portal_admin").style.display = "block";
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  } else if (target === "students") {
    switchToManagerView();
    setTimeout(() => {
      document.getElementById("adm_candidates_table")?.scrollIntoView({ behavior: "smooth" });
    }, 200);
  } else if (target === "batches") {
    switchToManagerView();
    setTimeout(() => {
      document.getElementById("adm_batches_grid")?.scrollIntoView({ behavior: "smooth" });
    }, 200);
  }
}

// ================= FULL BATCH ENROLLMENT MODAL LOGIC =================
var activeBatchObj = null;

function switchBatchEnrollTab(tab) {
  if (tab === 'new') {
    document.getElementById('batch_enroll_new_view').style.display = 'block';
    document.getElementById('batch_enroll_existing_view').style.display = 'none';
    document.getElementById('btn_enroll_tab_new').className = 'auth-tab-btn active';
    document.getElementById('btn_enroll_tab_existing').className = 'auth-tab-btn';
  } else {
    document.getElementById('batch_enroll_new_view').style.display = 'none';
    document.getElementById('batch_enroll_existing_view').style.display = 'block';
    document.getElementById('btn_enroll_tab_new').className = 'auth-tab-btn';
    document.getElementById('btn_enroll_tab_existing').className = 'auth-tab-btn active';
  }
}

async function openEnrollModal(batchId, batchName) {
  activeBatchId = batchId;
  document.getElementById("enroll_modal_batch_name").innerText = batchName;

  // Extract 2-digit batch number from batchName (e.g. "Batch 30" -> "30")
  const match = batchName.match(/\d+/);
  const batchNum = match ? match[0] : "01";

  // Prefill Full Form
  const today = new Date().toISOString().split("T")[0];
  if (document.getElementById("bem_admission_date")) document.getElementById("bem_admission_date").value = today;
  if (document.getElementById("bem_payment_date")) document.getElementById("bem_payment_date").value = today;
  if (document.getElementById("bem_batch_id")) document.getElementById("bem_batch_id").value = batchNum;
  if (document.getElementById("bem_password")) document.getElementById("bem_password").value = "grtc@123";
  if (document.getElementById("bem_total_course_fee")) document.getElementById("bem_total_course_fee").value = "4000";
  if (document.getElementById("bem_fee_paid")) document.getElementById("bem_fee_paid").value = "0";
  if (document.getElementById("bem_fee_balance")) document.getElementById("bem_fee_balance").value = "4000";

  // Load Existing Candidates for Tab 2
  try {
    const res = await fetch("/api/candidates?limit=200");
    const data = await res.json();
    const select = document.getElementById("enroll_student_select");
    if (select) {
      select.innerHTML = '<option value="">-- Select Candidate to Enroll --</option>';
      data.candidates.forEach(c => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.innerText = `${c.full_name} (${c.application_no}) - ${c.course} [Current: ${c.assigned_batch || "Unassigned"}]`;
        select.appendChild(opt);
      });
    }
  } catch (e) { }

  switchBatchEnrollTab('new');
  document.getElementById("enroll_student_modal").classList.add("active");
}

function closeEnrollModal() {
  document.getElementById("enroll_student_modal").classList.remove("active");
}

function calcBemFee() {
  const t = parseFloat(document.getElementById("bem_total_course_fee")?.value) || 0;
  const p = parseFloat(document.getElementById("bem_fee_paid")?.value) || 0;
  if (document.getElementById("bem_fee_balance")) {
    document.getElementById("bem_fee_balance").value = Math.max(0, t - p);
  }
}

function syncBemAddress() {
  const chk = document.getElementById("bem_same_as_current");
  if (chk && chk.checked) {
    document.getElementById("bem_permanent_address").value = document.getElementById("bem_current_address").value;
    document.getElementById("bem_permanent_city").value = document.getElementById("bem_current_city").value;
    document.getElementById("bem_permanent_pincode").value = document.getElementById("bem_current_pincode").value;
  }
}

function calcBemAge() {
  const dobVal = document.getElementById("bem_dob")?.value;
  const admVal = document.getElementById("bem_admission_date")?.value || new Date().toISOString().split("T")[0];
  const ageInput = document.getElementById("bem_age");
  const warnBox = document.getElementById("bem_age_warning_box");

  if (!dobVal) return;
  const dob = new Date(dobVal);
  const admDate = new Date(admVal);

  let years = admDate.getFullYear() - dob.getFullYear();
  let months = admDate.getMonth() - dob.getMonth();
  if (months < 0) { years--; months += 12; }

  if (ageInput) ageInput.value = `${years} Years ${months} Months`;
  if (warnBox) {
    warnBox.style.display = "block";
    if (years < 18) {
      warnBox.style.color = "#b91c1c";
      warnBox.style.background = "#fee2e2";
      warnBox.style.padding = "4px 8px";
      warnBox.style.borderRadius = "4px";
      warnBox.innerHTML = `⚠️ Under 18 (${years} Yrs) - Minor`;
    } else {
      warnBox.style.color = "#15803d";
      warnBox.style.background = "#dcfce7";
      warnBox.style.padding = "4px 8px";
      warnBox.style.borderRadius = "4px";
      warnBox.innerHTML = `✅ Eligible (${years} Yrs)`;
    }
  }
}

function handleBemPhotoUpload(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  const localUrl = URL.createObjectURL(file);
  document.getElementById("bem_photo_preview").innerHTML = `<img src="${localUrl}" style="width:100%; height:100%; object-fit:cover;">`;
  document.getElementById("bem_photo_container").classList.add("has-photo");
  document.getElementById("bem_photo_status_badge").innerHTML = "⏳ Processing photo...";

  const reader = new FileReader();
  reader.onload = function (e) {
    const img = new Image();
    img.onload = async function () {
      const canvas = document.createElement("canvas");
      let w = img.width, h = img.height;
      const maxDim = 800;
      if (w > h && w > maxDim) { h = Math.round(h * (maxDim / w)); w = maxDim; }
      else if (h > maxDim) { w = Math.round(w * (maxDim / h)); h = maxDim; }
      canvas.width = w; canvas.height = h;
      canvas.getContext("2d").drawImage(img, 0, 0, w, h);
      const compB64 = canvas.toDataURL("image/jpeg", 0.88);

      try {
        const res = await fetch("/api/upload", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ image: compB64 })
        });
        const d = await res.json();
        document.getElementById("bem_photo_url").value = d.url;
        document.getElementById("bem_photo_status_badge").innerHTML = "✅ Photo Ready";
        document.getElementById("bem_photo_status_badge").style.color = "var(--success)";
      } catch (err) {
        document.getElementById("bem_photo_url").value = compB64;
      }
    };
    img.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

function triggerBemCameraCapture() {
  const isMobile = /Android|iPhone|iPad/i.test(navigator.userAgent);
  if (isMobile) {
    document.getElementById('bem_camera_file').click();
  } else {
    document.getElementById('bem_photo_file').click();
  }
}

function uploadBemDoc(input, hiddenId, prevId, cardId) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  const prevEl = document.getElementById(prevId);

  if (file.type.startsWith("image/")) {
    const localUrl = URL.createObjectURL(file);
    prevEl.innerHTML = `<img src="${localUrl}" style="max-height:100%; max-width:100%; object-fit:contain;">`;
    if (cardId) document.getElementById(cardId).classList.add("uploaded");

    const reader = new FileReader();
    reader.onload = async function (e) {
      try {
        const res = await fetch("/api/upload-document", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ data: e.target.result, filename: file.name })
        });
        const d = await res.json();
        document.getElementById(hiddenId).value = d.url;
      } catch (err) {
        document.getElementById(hiddenId).value = e.target.result;
      }
    };
    reader.readAsDataURL(file);
  } else {
    prevEl.innerHTML = `<span style="font-size:11px; color:var(--primary); font-weight:bold;">📄 PDF: ${file.name}</span>`;
    if (cardId) document.getElementById(cardId).classList.add("uploaded");
  }
}

async function submitBatchAdmission(e) {
  if (e && e.preventDefault) e.preventDefault();
  const btn = document.getElementById("bem_submit_btn");
  const origText = btn ? btn.innerHTML : "Submit";

  const form = document.getElementById("batch_full_admission_form");
  const formData = new FormData(form);
  const data = Object.fromEntries(formData.entries());
  data.photo_url = document.getElementById("bem_photo_url")?.value || "";
  data.aadhaar_front_url = document.getElementById("bem_url_aadhaar_front")?.value || "";
  data.aadhaar_back_url = document.getElementById("bem_url_aadhaar_back")?.value || "";
  data.marksheet_10th_url = document.getElementById("bem_url_marksheet_10th")?.value || "";

  if (!data.full_name || !data.full_name.trim()) { alert("⚠️ Please enter candidate full name."); return; }
  if (!data.mobile_no || !data.mobile_no.trim()) { alert("⚠️ Please enter candidate mobile number."); return; }
  if (!data.aadhaar_front_url) { alert("⚠️ Please upload Aadhaar Card Front side."); return; }
  if (!data.aadhaar_back_url) { alert("⚠️ Please upload Aadhaar Card Back side."); return; }
  if (!data.marksheet_10th_url) { alert("⚠️ Please upload 10th Class Marksheet."); return; }

  if (btn) { btn.innerHTML = "⏳ Registering & Enrolling..."; btn.disabled = true; }

  try {
    // 1. Create candidate registration
    const res = await fetch("/api/public/register-admission", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();

    if (res.ok && result.candidate) {
      const candidateId = result.candidate.id;

      // 2. Automatically enroll into the active batch!
      if (activeBatchId) {
        await fetch(`/api/batches/${activeBatchId}/enroll`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${currentToken}`
          },
          body: JSON.stringify({
            candidate_id: candidateId,
            roll_number: data.batch_id ? `B${data.batch_id}-${candidateId}` : `B-${candidateId}`,
            remarks: `Direct Batch Admission - Ref: ${data.reference || 'Direct'}`
          })
        });
      }

      alert(`🎉 Student Successfully Registered and Enrolled in Batch!

Candidate: ${result.candidate.full_name}
App No: ${result.candidate.application_no}
Batch: ${document.getElementById("enroll_modal_batch_name").innerText}
Login ID: ${result.user.username}`);

      closeEnrollModal();
      await loadAdminBatches();
      await loadAdminCandidates();

      // Open Admission Slip
      viewCandidateSlipAdmin(candidateId);
    } else {
      alert("❌ Error: " + (result.detail || "Could not register candidate"));
    }
  } catch (err) {
    alert("❌ Error: " + err.message);
  } finally {
    if (btn) { btn.innerHTML = origText; btn.disabled = false; }
  }
}

// ================= EDIT BATCH HANDLERS =================
var allLoadedBatches = [];

async function openEditBatchModal(batchId) {
  try {
    const res = await fetch("/api/batches");
    allLoadedBatches = await res.json();
    const batch = allLoadedBatches.find(b => b.id === batchId);
    if (!batch) return;

    document.getElementById("edit_batch_id").value = batch.id;
    document.getElementById("edit_batch_name").value = batch.batch_name || "";
    document.getElementById("edit_batch_course").value = batch.course || "Computer";
    document.getElementById("edit_batch_timing").value = batch.timing || "09:00 AM - 05:00 PM";
    document.getElementById("edit_batch_days").value = batch.days || "Mon to Sat";
    document.getElementById("edit_batch_instructor").value = batch.instructor || "";
    document.getElementById("edit_batch_room").value = batch.room_no || "";
    document.getElementById("edit_batch_capacity").value = batch.max_capacity || 40;
    document.getElementById("edit_batch_start_date").value = batch.start_date || "";
    document.getElementById("edit_batch_end_date").value = batch.end_date || "";
    document.getElementById("edit_batch_status").value = batch.status || "Running";
    document.getElementById("edit_batch_modal_title").innerText = `✏️ Edit: ${batch.batch_name} (${batch.batch_code})`;

    document.getElementById("edit_batch_modal").classList.add("active");
  } catch (err) {
    console.error("Error opening edit batch modal:", err);
  }
}

function closeEditBatchModal() {
  document.getElementById("edit_batch_modal").classList.remove("active");
}

async function handleEditBatchSubmit(e) {
  e.preventDefault();
  const bid = document.getElementById("edit_batch_id").value;
  const payload = {
    batch_name: document.getElementById("edit_batch_name").value.trim(),
    course: document.getElementById("edit_batch_course").value,
    timing: document.getElementById("edit_batch_timing").value.trim(),
    days: document.getElementById("edit_batch_days").value.trim(),
    instructor: document.getElementById("edit_batch_instructor").value.trim(),
    room_no: document.getElementById("edit_batch_room").value.trim(),
    max_capacity: parseInt(document.getElementById("edit_batch_capacity").value || 40),
    start_date: document.getElementById("edit_batch_start_date").value,
    end_date: document.getElementById("edit_batch_end_date").value,
    status: document.getElementById("edit_batch_status").value
  };

  try {
    const res = await fetch(`/api/batches/${bid}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify(payload)
    });
    if (res.ok) {
      alert("✅ Batch details updated successfully!");
      closeEditBatchModal();
      await loadAdminBatches();
      await loadSuperAdminStats();
    } else {
      const err = await res.json();
      alert("❌ Update failed: " + (err.detail || "Error"));
    }
  } catch (err) {
    alert("Connection error: " + err.message);
  }
}

// ================= COMPREHENSIVE BATCH DETAIL HUB =================
var currentHubBatch = null;
var currentHubStudents = [];

async function openBatchDetailHub(batchId) {
  try {
    const bRes = await fetch("/api/batches");
    const batches = await bRes.json();
    currentHubBatch = batches.find(b => b.id === batchId);
    if (!currentHubBatch) return;

    // 1. Populate Batch Header & Info
    document.getElementById("hub_batch_title").innerText = `${currentHubBatch.batch_name} (${currentHubBatch.batch_code})`;
    document.getElementById("hub_batch_subtitle").innerText = `Course: ${currentHubBatch.course} | Status: ${currentHubBatch.status} | Center: ${currentHubBatch.center_name || 'Main Campus'}`;
    if (document.getElementById("hub_quick_status")) document.getElementById("hub_quick_status").value = currentHubBatch.status || "Running";

    document.getElementById("hub_stat_timing").innerText = currentHubBatch.timing || "09:00 AM - 05:00 PM";
    document.getElementById("hub_stat_days").innerText = currentHubBatch.days || "Mon to Sat";
    document.getElementById("hub_stat_dates").innerText = `${currentHubBatch.start_date || '2026-04-01'} to ${currentHubBatch.end_date || '2026-07-31'}`;
    document.getElementById("hub_stat_instructor").innerText = currentHubBatch.instructor || "Kumar Prince";
    document.getElementById("hub_stat_room").innerText = currentHubBatch.room_no || "Lab 1";

    const cap = currentHubBatch.max_capacity || 40;
    const enrolled = currentHubBatch.enrolled_count || 0;
    const pct = Math.round((enrolled / cap) * 100);
    document.getElementById("hub_stat_enrolled").innerText = `${enrolled} / ${cap}`;
    document.getElementById("hub_stat_seat_pct").innerText = `${pct}% Seats Filled`;

    // 2. Fetch and populate Enrolled Students
    const sRes = await fetch(`/api/batches/${batchId}/candidates`);
    currentHubStudents = await sRes.json();
    renderHubStudentsTable(currentHubStudents);

    document.getElementById("batch_detail_hub_modal").classList.add("active");
  } catch (err) {
    console.error("Error opening batch hub:", err);
  }
}

function closeBatchDetailHub() {
  document.getElementById("batch_detail_hub_modal").classList.remove("active");
}

function renderHubStudentsTable(students) {
  const tbody = document.getElementById("hub_students_tbody");
  tbody.innerHTML = "";
  document.getElementById("hub_students_count").innerText = students.length;

  if (students.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 2rem; color: var(--text-muted);">No students enrolled in this batch yet. Click "➕ Enroll New Student" above to add one.</td></tr>`;
    return;
  }

  students.forEach((s, idx) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="badge badge-approved" style="font-size:0.8rem; font-weight:700;">${s.roll_number || `B-${idx + 1}`}</span></td>
      <td><strong>${s.application_no}</strong></td>
      <td>
        <strong>${s.full_name}</strong><br>
        <small style="color:var(--text-muted);">${s.gender} | ${s.current_city || 'Bihar'}</small>
      </td>
      <td><strong>${s.mobile_no}</strong></td>
      <td>
        <div style="font-weight:700; color:var(--success);">Paid: ₹${(s.fee_paid || 0).toLocaleString("en-IN")}</div>
        <small style="color:${(s.fee_balance || 0) > 0 ? '#b91c1c' : '#15803d'}; font-weight:600;">
          ${(s.fee_balance || 0) > 0 ? `Dues: ₹${(s.fee_balance || 0).toLocaleString("en-IN")}` : `✅ Paid in Full`}
        </small>
      </td>
      <td><small style="color:var(--text-muted);">${s.enrollment_date || s.admission_date || 'N/A'}</small></td>
      <td>
        <div style="display:flex; gap:4px; align-items:center;">
          <button class="btn btn-secondary btn-sm" style="padding:2px 7px;" onclick="viewCandidateSlipAdmin(${s.candidate_id || s.id})">📄 Slip</button>
          <button class="btn btn-danger btn-sm" style="padding:2px 7px;" title="Unenroll from batch" onclick="unenrollHubStudent(${currentHubBatch.id}, ${s.candidate_id || s.id})">❌</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function filterHubStudents() {
  const q = (document.getElementById("hub_student_search")?.value || "").toLowerCase();
  const filtered = currentHubStudents.filter(s =>
    (s.full_name || "").toLowerCase().includes(q) ||
    (s.application_no || "").toLowerCase().includes(q) ||
    (s.mobile_no || "").toLowerCase().includes(q) ||
    (s.roll_number || "").toLowerCase().includes(q)
  );
  renderHubStudentsTable(filtered);
}

function hubTriggerEnroll() {
  if (!currentHubBatch) return;
  openEnrollModal(currentHubBatch.id, currentHubBatch.batch_name);
}

function hubTriggerEdit() {
  if (!currentHubBatch) return;
  openEditBatchModal(currentHubBatch.id);
}

async function hubTriggerDelete() {
  if (!currentHubBatch) return;
  if (confirm(`Are you sure you want to delete ${currentHubBatch.batch_name}?`)) {
    await deleteBatchRecord(currentHubBatch.id);
    closeBatchDetailHub();
  }
}

async function unenrollHubStudent(batchId, candidateId) {
  if (!confirm("Are you sure you want to remove this student from the batch?")) return;
  try {
    const res = await fetch(`/api/batches/${batchId}/unenroll/${candidateId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${currentToken}` }
    });
    if (res.ok) {
      alert("Student removed from batch.");
      await openBatchDetailHub(batchId);
      await loadAdminBatches();
    } else {
      alert("Failed to unenroll student.");
    }
  } catch (e) {
    alert("Error: " + e.message);
  }
}

function exportHubStudentsCSV() {
  if (!currentHubStudents || currentHubStudents.length === 0) {
    alert("No student records to export.");
    return;
  }
  let csv = "Roll No,Application No,Student Name,Gender,District,Mobile No,Fee Paid,Fee Dues,Enrolled Date\n";
  currentHubStudents.forEach(s => {
    csv += `"${s.roll_number || ''}","${s.application_no}","${s.full_name}","${s.gender}","${s.current_city || ''}","${s.mobile_no}","${s.fee_paid || 0}","${s.fee_balance || 0}","${s.enrollment_date || ''}"\n`;
  });
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${currentHubBatch ? currentHubBatch.batch_name : 'Batch'}_Students_List.csv`;
  a.click();
}

async function quickUpdateBatchStatus(newStatus) {
  if (!currentHubBatch) return;
  try {
    const res = await fetch(`/api/batches/${currentHubBatch.id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      currentHubBatch.status = newStatus;
      document.getElementById("hub_batch_subtitle").innerText = `Course: ${currentHubBatch.course} | Status: ${newStatus} | Center: ${currentHubBatch.center_name || 'Main Campus'}`;
      alert(`✅ ${currentHubBatch.batch_name} status updated to '${newStatus}' and moved to ${newStatus} section!`);
      await loadAdminBatches();
      await loadSuperAdminStats();
    } else {
      alert("Failed to update batch status.");
    }
  } catch (e) {
    alert("Error: " + e.message);
  }
}

// ================= REAL-TIME PORTAL DATA SYNCHRONIZATION =================
async function syncAllPortalData() {
  if (!currentToken || !currentUser) return;
  try {
    // 1. Real-Time Sync Batches Across All Screens
    await loadAdminBatches();

    // 2. Real-Time Sync Candidates Directory
    if (document.getElementById("adm_candidates_tbody") || document.getElementById("admin_candidates_tbody")) {
      await loadAdminCandidates();
    }

    // 3. Real-Time Sync Dashboard Stats & User Accounts Across Roles
    const r = (currentUser.role || "").toLowerCase();
    if (r === "superadmin" || r === "director") {
      await loadSuperAdminStats();
      if (typeof loadSuperAdminUsers === "function") {
        await loadSuperAdminUsers();
      }
    } else if (r === "admin" || r === "manager") {
      await loadAdminStats();
    }
  } catch (err) {
    console.error("Real-time auto-sync error:", err);
  }
}

// Real-Time Background Auto-Sync Engine (Sync every 4 seconds across all devices & user roles)
var autoSyncInterval = null;
if (!autoSyncInterval) {
  autoSyncInterval = setInterval(() => {
    if (currentToken && currentUser) {
      syncAllPortalData();
    }
  }, 4000);
}

// ================= USER PROFILE MENU & DROPDOWN LOGIC =================
function getUserInitials(name) {
  if (!name) return "U";
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }
  return parts[0].substring(0, 2).toUpperCase();
}

function toggleUserProfileDropdown(e) {
  if (e) e.stopPropagation();
  const dropdown = document.getElementById("user_profile_dropdown");
  if (!dropdown) return;
  
  if (dropdown.style.display === "block" || dropdown.classList.contains("show")) {
    dropdown.style.display = "none";
    dropdown.classList.remove("show");
  } else {
    dropdown.style.display = "block";
    dropdown.classList.add("show");
  }
}

document.addEventListener("click", function(e) {
  const wrapper = document.getElementById("header_user_bar");
  const dropdown = document.getElementById("user_profile_dropdown");
  if (dropdown && wrapper && !wrapper.contains(e.target)) {
    dropdown.style.display = "none";
    dropdown.classList.remove("show");
  }
});

async function loadAdminEnquiries() {
  const token = getAuthToken();
  if (!token) return;

  try {
    const res = await fetch("/api/admin/enquiries", {
      headers: { "Authorization": "Bearer " + token }
    });
    if (res.ok) {
      const enquiries = await res.json();
      renderEnquiriesTable(enquiries);
    }
  } catch(err) {
    console.error("Error loading enquiries:", err);
  }
}

function renderEnquiriesTable(enquiries) {
  const tbody = document.getElementById("enquiries_tbody");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (!enquiries || enquiries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 1.5rem; color: #64748b;">No website admission enquiries received yet.</td></tr>`;
    return;
  }

  enquiries.forEach(e => {
    const tr = document.createElement("tr");
    
    let statusBadge = `<span style="background:#fef3c7; color:#b45309; padding:4px 10px; border-radius:12px; font-weight:800; font-size:0.75rem;">Pending</span>`;
    if (e.status === 'Contacted') {
      statusBadge = `<span style="background:#dbeafe; color:#1d4ed8; padding:4px 10px; border-radius:12px; font-weight:800; font-size:0.75rem;">Contacted</span>`;
    } else if (e.status === 'Admitted') {
      statusBadge = `<span style="background:#dcfce7; color:#15803d; padding:4px 10px; border-radius:12px; font-weight:800; font-size:0.75rem;">Admitted</span>`;
    }

    tr.innerHTML = `
      <td>${e.created_at || 'Recently'}</td>
      <td><strong>${e.full_name}</strong></td>
      <td><a href="tel:${e.mobile}" style="color:#2563eb; font-weight:800; text-decoration:underline;">📞 ${e.mobile}</a></td>
      <td><span style="background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:6px; font-weight:700; font-size:0.8rem;">${e.course}</span></td>
      <td>${e.district || '-'}</td>
      <td>${statusBadge}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary" onclick="updateEnquiryStatus(${e.id}, 'Contacted')">📞 Contacted</button>
        <button class="btn btn-sm btn-success" onclick="updateEnquiryStatus(${e.id}, 'Admitted')">✅ Admitted</button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteEnquiryRecord(${e.id})">🗑️ Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function updateEnquiryStatus(eid, newStatus) {
  const token = getAuthToken();
  if (!token) return;

  try {
    const res = await fetch(`/api/admin/enquiries/${eid}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
      },
      body: JSON.stringify({ status: newStatus })
    });
    if (res.ok) {
      loadAdminEnquiries();
    }
  } catch(err) {
    console.error("Error updating enquiry status:", err);
  }
}

async function deleteEnquiryRecord(eid) {
  if (!confirm("Are you sure you want to delete this admission enquiry?")) return;
  const token = getAuthToken();
  if (!token) return;

  try {
    const res = await fetch(`/api/admin/enquiries/${eid}`, {
      method: "DELETE",
      headers: { "Authorization": "Bearer " + token }
    });
    if (res.ok) {
      loadAdminEnquiries();
    }
  } catch(err) {
    console.error("Error deleting enquiry:", err);
  }
}

function closeUserProfileDropdown() {
  const dropdown = document.getElementById("user_profile_dropdown");
  if (dropdown) dropdown.style.display = "none";
  const trigger = document.getElementById("user_profile_trigger");
  if (trigger) trigger.setAttribute("aria-expanded", "false");
}

// Close dropdown on outside click or Escape key
document.addEventListener("click", (e) => {
  const wrapper = document.getElementById("header_user_bar");
  if (wrapper && !wrapper.contains(e.target)) {
    closeUserProfileDropdown();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeUserProfileDropdown();
    closeUserProfileModal();
    closeChangePasswordModal();
    closeChangeAvatarModal();
  }
});

function renderUserAvatarAndHeader(user) {
  if (!user) return;
  const name = user.full_name || user.username || "User";
  const initials = getUserInitials(name);
  const pic = user.profile_picture;

  // Header trigger
  const hName = document.getElementById("header_user_name");
  if (hName) hName.innerText = name;
  const hInitials = document.getElementById("header_user_initials");
  if (hInitials) hInitials.innerText = initials;
  const hAvatar = document.getElementById("header_user_avatar");
  if (hAvatar) {
    if (pic) {
      hAvatar.style.backgroundImage = `url("${pic}")`;
      if (hInitials) hInitials.style.display = "none";
    } else {
      hAvatar.style.backgroundImage = "none";
      if (hInitials) hInitials.style.display = "inline";
    }
  }

  // Dropdown header
  const dName = document.getElementById("dropdown_user_fullname");
  if (dName) dName.innerText = name;
  const dUser = document.getElementById("dropdown_user_username");
  if (dUser) dUser.innerText = `@${user.username || user.mobile || "user"}`;
  const dInitials = document.getElementById("dropdown_user_initials");
  if (dInitials) dInitials.innerText = initials;
  const dAvatar = document.getElementById("dropdown_user_avatar");
  if (dAvatar) {
    if (pic) {
      dAvatar.style.backgroundImage = `url("${pic}")`;
      if (dInitials) dInitials.style.display = "none";
    } else {
      dAvatar.style.backgroundImage = "none";
      if (dInitials) dInitials.style.display = "inline";
    }
  }
}

// Modals
function openUserProfileModal() {
  closeUserProfileDropdown();
  if (!currentUser) return;
  
  const initials = getUserInitials(currentUser.full_name);
  const pic = currentUser.profile_picture;
  
  document.getElementById("modal_profile_fullname").innerText = currentUser.full_name || "User";
  document.getElementById("modal_profile_username").innerText = currentUser.username || "N/A";
  document.getElementById("modal_profile_mobile").innerText = currentUser.mobile || "N/A";
  document.getElementById("modal_profile_email").innerText = currentUser.email || "N/A";
  document.getElementById("modal_profile_center").innerText = currentUser.center_name || "Main Campus";
  document.getElementById("modal_profile_role_pill").innerText = (currentUser.role || "USER").toUpperCase();
  document.getElementById("modal_profile_initials").innerText = initials;
  
  const mAvatar = document.getElementById("modal_profile_avatar");
  const mInitials = document.getElementById("modal_profile_initials");
  if (mAvatar) {
    if (pic) {
      mAvatar.style.backgroundImage = `url("${pic}")`;
      if (mInitials) mInitials.style.display = "none";
    } else {
      mAvatar.style.backgroundImage = "none";
      if (mInitials) mInitials.style.display = "inline";
    }
  }
  
  document.getElementById("user_profile_modal").classList.add("active");
}

function closeUserProfileModal() {
  document.getElementById("user_profile_modal").classList.remove("active");
}

function openChangePasswordModal() {
  closeUserProfileDropdown();
  document.getElementById("cp_current_password").value = "";
  document.getElementById("cp_new_password").value = "";
  document.getElementById("cp_confirm_password").value = "";
  const alertBox = document.getElementById("cp_status_alert");
  if (alertBox) alertBox.style.display = "none";
  document.getElementById("change_password_modal").classList.add("active");
}

function closeChangePasswordModal() {
  document.getElementById("change_password_modal").classList.remove("active");
}

async function handleChangePasswordSubmit(e) {
  if (e) e.preventDefault();
  const cp = document.getElementById("cp_current_password").value.trim();
  const np = document.getElementById("cp_new_password").value.trim();
  const cnp = document.getElementById("cp_confirm_password").value.trim();
  const alertBox = document.getElementById("cp_status_alert");

  if (!cp || !np || !cnp) {
    alertBox.style.display = "block";
    alertBox.style.background = "#fef2f2";
    alertBox.style.color = "#dc2626";
    alertBox.innerText = "❌ Please fill all password fields.";
    return;
  }

  if (np.length < 6 || np.length > 12) {
    alertBox.style.display = "block";
    alertBox.style.background = "#fef2f2";
    alertBox.style.color = "#dc2626";
    alertBox.innerText = "❌ New password must be between 6 and 12 characters.";
    return;
  }

  if (np !== cnp) {
    alertBox.style.display = "block";
    alertBox.style.background = "#fef2f2";
    alertBox.style.color = "#dc2626";
    alertBox.innerText = "❌ New password and confirmation do not match.";
    return;
  }

  if (cp === np) {
    alertBox.style.display = "block";
    alertBox.style.background = "#fef2f2";
    alertBox.style.color = "#dc2626";
    alertBox.innerText = "❌ New password must be different from current password.";
    return;
  }

  try {
    const res = await fetch("/api/user/change-password", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ current_password: cp, new_password: np, confirm_password: cnp })
    });
    const data = await res.json();
    if (res.ok) {
      alertBox.style.display = "block";
      alertBox.style.background = "#f0fdf4";
      alertBox.style.color = "#16a34a";
      alertBox.innerText = "✅ Password changed successfully!";
      document.getElementById("cp_current_password").value = "";
      document.getElementById("cp_new_password").value = "";
      document.getElementById("cp_confirm_password").value = "";
      setTimeout(() => closeChangePasswordModal(), 1800);
    } else {
      alertBox.style.display = "block";
      alertBox.style.background = "#fef2f2";
      alertBox.style.color = "#dc2626";
      alertBox.innerText = "❌ " + (data.detail || "Failed to change password.");
    }
  } catch (err) {
    alertBox.style.display = "block";
    alertBox.style.background = "#fef2f2";
    alertBox.style.color = "#dc2626";
    alertBox.innerText = "❌ Connection error: " + err.message;
  }
}

// Avatar Upload Modal
var selectedAvatarFile = null;

function openChangeAvatarModal() {
  closeUserProfileDropdown();
  selectedAvatarFile = null;
  document.getElementById("avatar_file_input").value = "";
  document.getElementById("avatar_upload_status").innerText = "No new photo selected.";
  document.getElementById("btn_submit_avatar").disabled = true;

  if (currentUser) {
    const initials = getUserInitials(currentUser.full_name);
    const pic = currentUser.profile_picture;
    const pCircle = document.getElementById("avatar_preview_circle");
    const pInitials = document.getElementById("avatar_preview_initials");
    if (pCircle) {
      if (pic) {
        pCircle.style.backgroundImage = `url("${pic}")`;
        if (pInitials) pInitials.style.display = "none";
      } else {
        pCircle.style.backgroundImage = "none";
        if (pInitials) pInitials.style.display = "inline";
      }
    }
    if (pInitials) pInitials.innerText = initials;
  }

  document.getElementById("change_avatar_modal").classList.add("active");
}

function closeChangeAvatarModal() {
  document.getElementById("change_avatar_modal").classList.remove("active");
}

function handleAvatarFileSelected(input) {
  if (input.files && input.files[0]) {
    const file = input.files[0];
    if (file.size > 5 * 1024 * 1024) {
      alert("Selected photo exceeds maximum 5MB size limit.");
      input.value = "";
      return;
    }
    selectedAvatarFile = file;
    document.getElementById("avatar_upload_status").innerText = `Selected: ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
    document.getElementById("btn_submit_avatar").disabled = false;

    const reader = new FileReader();
    reader.onload = (e) => {
      const pCircle = document.getElementById("avatar_preview_circle");
      const pInitials = document.getElementById("avatar_preview_initials");
      if (pCircle) pCircle.style.backgroundImage = `url("${e.target.result}")`;
      if (pInitials) pInitials.style.display = "none";
    };
    reader.readAsDataURL(file);
  }
}

function compressAvatarFile(file, maxDimension = 400, quality = 0.85) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      const img = new Image();
      img.onload = () => {
        let width = img.width;
        let height = img.height;
        if (width > height) {
          if (width > maxDimension) {
            height = Math.round((height * maxDimension) / width);
            width = maxDimension;
          }
        } else {
          if (height > maxDimension) {
            width = Math.round((width * maxDimension) / height);
            height = maxDimension;
          }
        }
        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(img, 0, 0, width, height);
        const dataUrl = canvas.toDataURL("image/jpeg", quality);
        resolve(dataUrl);
      };
      img.onerror = (err) => reject(err);
      img.src = event.target.result;
    };
    reader.onerror = (err) => reject(err);
    reader.readAsDataURL(file);
  });
}

async function submitAvatarUpload() {
  if (!selectedAvatarFile) return;
  const statusDiv = document.getElementById("avatar_upload_status");
  statusDiv.innerText = "⏳ Optimizing and uploading photo...";

  try {
    const compressedDataUrl = await compressAvatarFile(selectedAvatarFile, 400, 0.85);
    const res = await fetch("/api/user/avatar", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${currentToken}`
      },
      body: JSON.stringify({ profile_picture: compressedDataUrl })
    });

    let data = {};
    try {
      data = await res.json();
    } catch (jsonErr) {
      data = { detail: `Server error (${res.status} ${res.statusText})` };
    }

    if (res.ok && data.profile_picture) {
      statusDiv.innerText = "✅ Profile picture updated successfully!";
      currentUser.profile_picture = data.profile_picture;
      renderUserAvatarAndHeader(currentUser);
      setTimeout(() => closeChangeAvatarModal(), 1200);
    } else {
      statusDiv.innerText = "❌ " + (data.detail || "Upload failed.");
    }
  } catch (err) {
    statusDiv.innerText = "❌ Upload error: " + err.message;
  }
}

let globalAllEnquiries = [];
let showAllEnquiriesState = false;

async function loadAdminEnquiries() {
  const token = getAuthToken();
  const tbody = document.getElementById("enquiries_tbody");
  
  try {
    let res = null;
    if (token) {
      res = await fetch("/api/admin/enquiries", {
        headers: { "Authorization": "Bearer " + token }
      });
    }

    if (!res || !res.ok) {
      res = await fetch("/api/public/enquiries");
    }

    if (res && res.ok) {
      globalAllEnquiries = await res.json();
      renderEnquiriesTable();
    } else {
      if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 1.5rem; color: #b45309; font-weight: 700;">Click "Refresh Enquiries" to reload latest leads.</td></tr>`;
    }
  } catch(err) {
    console.error("Error loading enquiries:", err);
    if (tbody) tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 1.5rem; color: #ef4444; font-weight: 700;">Unable to connect to server. Please refresh.</td></tr>`;
  }
}

function renderEnquiriesTable() {
  const tbody = document.getElementById("enquiries_tbody");
  const toggleWrap = document.getElementById("enquiries_toggle_wrap");
  const toggleBtn = document.getElementById("enquiries_toggle_btn");
  if (!tbody) return;

  tbody.innerHTML = "";
  if (!globalAllEnquiries || globalAllEnquiries.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding: 1.5rem; color: #64748b;">No website admission enquiries received yet.</td></tr>`;
    if (toggleWrap) toggleWrap.style.display = "none";
    return;
  }

  const totalCount = globalAllEnquiries.length;
  const listToRender = showAllEnquiriesState ? globalAllEnquiries : globalAllEnquiries.slice(0, 5);

  listToRender.forEach(e => {
    const tr = document.createElement("tr");
    
    let statusBadge = `<span style="background:#fef3c7; color:#b45309; padding:4px 10px; border-radius:12px; font-weight:800; font-size:0.75rem;">Pending</span>`;
    if (e.status === 'Contacted') {
      statusBadge = `<span style="background:#dbeafe; color:#1d4ed8; padding:4px 10px; border-radius:12px; font-weight:800; font-size:0.75rem;">Contacted</span>`;
    } else if (e.status === 'Admitted') {
      statusBadge = `<span style="background:#dcfce7; color:#15803d; padding:4px 10px; border-radius:12px; font-weight:800; font-size:0.75rem;">Admitted</span>`;
    }

    tr.innerHTML = `
      <td>${e.created_at || 'Recently'}</td>
      <td><strong>${e.full_name}</strong></td>
      <td><a href="tel:${e.mobile}" style="color:#2563eb; font-weight:800; text-decoration:underline;">📞 ${e.mobile}</a></td>
      <td><span style="background:#e0f2fe; color:#0369a1; padding:3px 8px; border-radius:6px; font-weight:700; font-size:0.8rem;">${e.course}</span></td>
      <td>${e.district || '-'}</td>
      <td>${statusBadge}</td>
      <td>
        <button class="btn btn-sm btn-outline-primary" onclick="updateEnquiryStatus(${e.id}, 'Contacted')">📞 Contacted</button>
        <button class="btn btn-sm btn-success" onclick="updateEnquiryStatus(${e.id}, 'Admitted')">✅ Admitted</button>
        <button class="btn btn-sm btn-outline-danger" onclick="deleteEnquiryRecord(${e.id})">🗑️ Delete</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  if (totalCount > 5) {
    if (toggleWrap) toggleWrap.style.display = "block";
    if (toggleBtn) {
      if (showAllEnquiriesState) {
        toggleBtn.innerText = `🔼 Show Top 5 Enquiries`;
      } else {
        toggleBtn.innerText = `📂 Show All Enquiries (${totalCount})`;
      }
    }
  } else {
    if (toggleWrap) toggleWrap.style.display = "none";
  }
}

function toggleAllEnquiriesDisplay() {
  showAllEnquiriesState = !showAllEnquiriesState;
  renderEnquiriesTable();
}

// 3-Line Hamburger Menu Toggle Function (100% Bulletproof Interactive)
function toggleSidebarMenu(e) {
  if (e) {
    if (e.stopPropagation) e.stopPropagation();
    if (e.preventDefault) e.preventDefault();
  }

  const drawer = document.getElementById("sidebar_drawer");
  const overlay = document.getElementById("sidebar_overlay");
  if (!drawer) return;

  const isOpen = drawer.classList.contains("open") || drawer.style.left === "0px";

  if (isOpen) {
    drawer.classList.remove("open");
    drawer.style.left = "-320px";
    if (overlay) {
      overlay.classList.remove("show");
      overlay.style.display = "none";
    }
  } else {
    drawer.classList.add("open");
    drawer.style.left = "0px";
    if (overlay) {
      overlay.classList.add("show");
      overlay.style.display = "block";
    }
  }
}

// 🔗 DYNAMIC SPA URL HASH ROUTING FOR MENU OPTIONS
function updateUrlHash(hashName) {
  if (window.history && window.history.pushState) {
    window.history.pushState(null, "", "#" + hashName);
  } else {
    window.location.hash = "#" + hashName;
  }
}

function handleHashRouting() {
  const rawHash = window.location.hash.replace("#", "") || "overview";
  
  if (rawHash === "overview" || rawHash === "dashboard") {
    switchDashboardView("dashboard", document.getElementById("nav_item_dashboard"), false);
  } else if (rawHash === "enquiries") {
    switchDashboardView("dashboard", document.getElementById("nav_item_dashboard"), false);
    setTimeout(() => {
      const tbody = document.getElementById("enquiries_tbody");
      if (tbody) tbody.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 200);
  } else if (rawHash.startsWith("batches")) {
    switchDashboardView("batches", document.getElementById("nav_item_batches"), false);
    if (rawHash === "batches-running") openBatchCategory("running", false);
    else if (rawHash === "batches-upcoming") openBatchCategory("upcoming", false);
    else if (rawHash === "batches-completed") openBatchCategory("completed", false);
  } else if (rawHash === "students") {
    switchDashboardView("students", document.getElementById("nav_item_students"), false);
  } else if (rawHash.startsWith("users")) {
    if (rawHash === "users-students") openSuperAdminUsersTab("students", false);
    else if (rawHash === "users-superadmin") openSuperAdminUsersTab("superadmins", false);
    else openSuperAdminUsersTab("managers", false);
  }
}

// 100% Working Switch Dashboard View with Dynamic URL Hash Sync
function switchDashboardView(viewTarget, element, updateHash = true) {
  const views = document.querySelectorAll(".dashboard-view-panel");
  views.forEach(v => v.style.display = "none");

  const adminPortal = document.getElementById("portal_admin");
  const superadminPortal = document.getElementById("portal_superadmin");
  const studentPortal = document.getElementById("portal_student");

  if (adminPortal) adminPortal.style.display = "block";
  if (superadminPortal) superadminPortal.style.display = "none";
  if (studentPortal) studentPortal.style.display = "none";

  const targetPanel = document.getElementById("view_" + viewTarget);
  if (targetPanel) {
    targetPanel.style.display = "block";
  }

  // Sync Active class on nav item
  const navItems = document.querySelectorAll(".sidebar-nav-item");
  navItems.forEach(item => item.classList.remove("active"));
  if (element) element.classList.add("active");

  // Update Browser URL Hash
  if (updateHash) {
    if (viewTarget === "dashboard") updateUrlHash("overview");
    else if (viewTarget === "batches") updateUrlHash("batches");
    else if (viewTarget === "students") updateUrlHash("students");
  }

  // Load fresh data for the targeted view
  if (viewTarget === 'dashboard') {
    loadAdminEnquiries();
  } else if (viewTarget === 'batches') {
    loadAdminBatches();
  } else if (viewTarget === 'students') {
    loadAdminCandidates();
  }

  // Close sidebar drawer after selection
  const drawer = document.getElementById("sidebar_drawer");
  if (drawer && drawer.classList.contains("open")) {
    toggleSidebarMenu();
  }
}

// Open Specific Batch Category with URL Hash Update
function openBatchCategory(category, updateHash = true) {
  switchDashboardView("batches", document.getElementById("nav_item_batches"), false);
  if (updateHash) updateUrlHash("batches-" + category);

  if (category === "running") {
    const grid = document.getElementById("grid_running_batches");
    if (grid && (grid.style.display === "none" || grid.classList.contains("is-collapsed"))) {
      toggleBatchSection("grid_running_batches", "arrow_running");
    }
  } else if (category === "upcoming") {
    const grid = document.getElementById("grid_upcoming_batches");
    if (grid && (grid.style.display === "none" || grid.classList.contains("is-collapsed"))) {
      toggleBatchSection("grid_upcoming_batches", "arrow_upcoming");
    }
  } else if (category === "completed") {
    const grid = document.getElementById("grid_completed_batches");
    if (grid && (grid.style.display === "none" || grid.classList.contains("is-collapsed"))) {
      toggleBatchSection("grid_completed_batches", "arrow_completed");
    }
  }
}

// Open SuperAdmin Users Tab with URL Hash Update
function openSuperAdminUsersTab(tabName, updateHash = true) {
  const drawer = document.getElementById("sidebar_drawer");
  if (drawer && drawer.classList.contains("open")) toggleSidebarMenu();

  const superadminPortal = document.getElementById("portal_superadmin");
  const adminPortal = document.getElementById("portal_admin");
  const studentPortal = document.getElementById("portal_student");

  if (updateHash) updateUrlHash("users-" + tabName);

  if (superadminPortal) {
    if (adminPortal) adminPortal.style.display = "none";
    if (studentPortal) studentPortal.style.display = "none";
    superadminPortal.style.display = "block";
    switchSuperAdminUserTab(tabName);
  } else {
    switchDashboardView("students", document.getElementById("nav_item_students"), false);
  }
}

// Event Listeners for URL Hash Navigation
window.addEventListener("hashchange", handleHashRouting);
window.addEventListener("DOMContentLoaded", () => {
  if (window.location.hash) {
    setTimeout(handleHashRouting, 300);
  }
});

function openBatchCategory(category) {
  switchDashboardView("batches", document.getElementById("nav_item_batches"));

  if (category === "running") {
    const grid = document.getElementById("grid_running_batches");
    const arrow = document.getElementById("arrow_running");
    if (grid && (grid.style.display === "none" || grid.classList.contains("is-collapsed"))) {
      toggleBatchSection("grid_running_batches", "arrow_running");
    }
  } else if (category === "upcoming") {
    const grid = document.getElementById("grid_upcoming_batches");
    const arrow = document.getElementById("arrow_upcoming");
    if (grid && (grid.style.display === "none" || grid.classList.contains("is-collapsed"))) {
      toggleBatchSection("grid_upcoming_batches", "arrow_upcoming");
    }
  } else if (category === "completed") {
    const grid = document.getElementById("grid_completed_batches");
    const arrow = document.getElementById("arrow_completed");
    if (grid && (grid.style.display === "none" || grid.classList.contains("is-collapsed"))) {
      toggleBatchSection("grid_completed_batches", "arrow_completed");
    }
  }
}
document.addEventListener('DOMContentLoaded', loadAdminEnquiries);


function openSuperAdminUsersTab(tabName) {
  toggleSidebarMenu();
  const superadminPortal = document.getElementById("portal_superadmin");
  const adminPortal = document.getElementById("portal_admin");
  const studentPortal = document.getElementById("portal_student");

  if (superadminPortal) {
    if (adminPortal) adminPortal.style.display = "none";
    if (studentPortal) studentPortal.style.display = "none";
    superadminPortal.style.display = "block";
    switchSuperAdminUserTab(tabName);
  } else {
    switchDashboardView("students", document.getElementById("nav_item_students"));
  }
}

// 🔗 DYNAMIC SPA URL HASH ROUTING FOR ALL USER ROLES
function updateUrlHash(hashName) {
  if (window.history && window.history.pushState) {
    window.history.pushState(null, "", "#" + hashName);
  } else {
    window.location.hash = "#" + hashName;
  }
}

function handleHashRouting() {
  const rawHash = window.location.hash.replace("#", "") || "overview";
  const userRole = (currentUser && currentUser.role) ? currentUser.role.toLowerCase() : "";

  // 1. STUDENT PORTAL HASH ROUTING
  if (userRole === "student") {
    if (rawHash === "student-fees" || rawHash === "fees") {
      switchStudentTab("fees");
    } else if (rawHash === "student-batch" || rawHash === "batch") {
      switchStudentTab("batch");
    } else if (rawHash === "student-idcard" || rawHash === "idcard") {
      switchStudentTab("idcard");
    } else {
      switchStudentTab("status");
    }
    return;
  }

  // 2. ADMIN / MANAGER / DIRECTOR / SUPERADMIN ROUTING
  if (rawHash === "overview" || rawHash === "dashboard") {
    switchDashboardView("dashboard", document.getElementById("nav_item_dashboard"), false);
  } else if (rawHash === "enquiries") {
    switchDashboardView("dashboard", document.getElementById("nav_item_dashboard"), false);
    setTimeout(() => {
      const tbody = document.getElementById("enquiries_tbody");
      if (tbody) tbody.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 200);
  } else if (rawHash.startsWith("batches")) {
    switchDashboardView("batches", document.getElementById("nav_item_batches"), false);
    if (rawHash === "batches-running") openBatchCategory("running", false);
    else if (rawHash === "batches-upcoming") openBatchCategory("upcoming", false);
    else if (rawHash === "batches-completed") openBatchCategory("completed", false);
  } else if (rawHash === "students") {
    switchDashboardView("students", document.getElementById("nav_item_students"), false);
  } else if (rawHash.startsWith("users")) {
    if (rawHash === "users-students") openSuperAdminUsersTab("students", false);
    else if (rawHash === "users-superadmin") openSuperAdminUsersTab("superadmins", false);
    else openSuperAdminUsersTab("managers", false);
  } else if (rawHash === "profile") {
    openUserProfileModal();
  }
}

// Student Tab Switcher with URL Hash Support
function switchStudentTab(tabName) {
  updateUrlHash("student-" + tabName);
  const tabs = document.querySelectorAll(".student-tab-panel");
  tabs.forEach(t => t.style.display = "none");

  const target = document.getElementById("student_tab_" + tabName);
  if (target) target.style.display = "block";
}