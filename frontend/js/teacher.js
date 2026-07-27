// ============================================================
// js/teacher.js - Teacher dashboard logic
// ============================================================

let allStudents = [];
let allAssignments = [];
let allSubjects = [];

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth('teacher')) return;
  chartDefaults();
  populateSidebarUser();
  await Promise.all([loadStudents(), loadAssignments(), loadSubjects()]);
});

function onDeptChange() { loadStudents(); }

// ── Students ──────────────────────────────────────────────────────────────────
async function loadStudents() {
  const dept = document.getElementById('dept-filter')?.value;
  try {
    const data = await api.teacher.students(dept);
    allStudents = data.students || [];

    // Stats
    document.getElementById('t-stat-students').textContent = allStudents.length;

    renderOverviewTable(allStudents);
    renderStudentList(allStudents);
    populateStudentSelects();
  } catch (err) { showToast(err.message, 'error'); }
}

function renderOverviewTable(students) {
  const tbody = document.getElementById('overview-student-list');
  if (!students.length) { tbody.innerHTML = `<tr><td colspan="7">${emptyState('👨‍🎓', 'No students found')}</td></tr>`; return; }
  tbody.innerHTML = students.slice(0, 15).map(s => `
    <tr>
      <td><strong>${s.name}</strong></td>
      <td style="color:var(--text-muted)">${s.roll_number}</td>
      <td>${s.department}</td>
      <td style="color:${marksColor(s.average_marks||0)};font-weight:700">${fmtNum(s.average_marks||0)}%</td>
      <td>${s.grade ? gradeBadge(s.grade) : '<span class="badge badge-info">N/A</span>'}</td>
      <td>${s.risk_level ? riskBadge(s.risk_level) : '<span class="badge badge-info">N/A</span>'}</td>
      <td><button class="btn btn-secondary btn-sm" onclick="viewStudentDetail(${s.id})">View</button></td>
    </tr>
  `).join('');
}

function renderStudentList(students) {
  const tbody = document.getElementById('student-list-body');
  tbody.innerHTML = students.map(s => `
    <tr>
      <td><strong>${s.name}</strong></td>
      <td>${s.roll_number}</td>
      <td>${s.department}</td>
      <td>Sem ${s.semester}</td>
      <td style="color:${marksColor(s.average_marks||0)};font-weight:700">${fmtNum(s.average_marks||0)}%</td>
      <td>${s.grade ? gradeBadge(s.grade) : '--'}</td>
      <td>${s.risk_level ? riskBadge(s.risk_level) : '--'}</td>
      <td>
        <button class="btn btn-secondary btn-sm" onclick="viewStudentDetail(${s.id})">📋 Detail</button>
        <button class="btn btn-outline btn-sm" onclick="goEnterMarks(${s.id})" style="margin-left:4px">📊 Marks</button>
      </td>
    </tr>
  `).join('');
}

function filterStudentList() {
  const q = document.getElementById('student-search').value.toLowerCase();
  const filtered = allStudents.filter(s =>
    s.name.toLowerCase().includes(q) || s.roll_number.toLowerCase().includes(q) || s.department.toLowerCase().includes(q)
  );
  renderStudentList(filtered);
}

async function viewStudentDetail(id) {
  try {
    const data = await api.teacher.studentDetail(id);
    const { student, marks, latest_prediction } = data;
    document.getElementById('detail-modal-title').textContent = `${student.name} — ${student.roll_number}`;
    document.getElementById('student-detail-content').innerHTML = `
      <div style="display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.25rem">
        ${[['Dept', student.department], ['Semester', `Sem ${student.semester}`],
           ['Grade', latest_prediction ? latest_prediction.grade : 'N/A'],
           ['Risk', latest_prediction ? latest_prediction.risk_level : 'N/A']].map(([k,v]) =>
          `<div style="background:var(--bg-elevated);padding:0.6rem 1rem;border-radius:var(--radius-md);text-align:center">
            <div style="font-size:0.75rem;color:var(--text-muted)">${k}</div>
            <div style="font-weight:700;font-size:0.95rem">${v}</div>
          </div>`).join('')}
      </div>
      <h4 style="margin-bottom:0.75rem">Subject Marks</h4>
      ${marks.length ? marks.map(m => `
        <div class="perf-bar-wrap">
          <div class="perf-bar-label">
            <span>${m.subject_name}</span>
            <span style="color:${marksColor(m.marks)}">${m.marks}/100 — Att: ${pct(m.attendance)}</span>
          </div>
          ${progressBar(m.marks)}
        </div>`).join('') : '<p style="color:var(--text-muted)">No marks recorded.</p>'}
      ${latest_prediction ? `
        <div style="margin-top:1rem;padding:1rem;background:var(--bg-elevated);border-radius:var(--radius-md)">
          <strong>Latest AI Prediction:</strong> Grade ${gradeBadge(latest_prediction.grade)} | Risk ${riskBadge(latest_prediction.risk_level)}
          | Avg: ${fmtNum(latest_prediction.average_marks)}% | Confidence: ${latest_prediction.confidence}%
        </div>` : ''}
    `;
    openModal('modal-student-detail');
  } catch (err) { showToast(err.message, 'error'); }
}

function goEnterMarks(studentId) {
  activateSection('sec-marks');
  document.getElementById('marks-student-sel').value = studentId;
  loadStudentMarksForm();
}

function populateStudentSelects() {
  const sel = document.getElementById('marks-student-sel');
  sel.innerHTML = '<option value="">-- Select a student --</option>' +
    allStudents.map(s => `<option value="${s.id}">${s.name} (${s.roll_number})</option>`).join('');
}

// ── Marks Entry ───────────────────────────────────────────────────────────────
async function loadStudentMarksForm() {
  const studentId = document.getElementById('marks-student-sel').value;
  const container = document.getElementById('marks-entry-form');
  if (!studentId) { container.classList.add('hidden'); return; }

  try {
    const data = await api.teacher.studentDetail(studentId);
    const student = data.student;
    const existingMarks = {};
    data.marks.forEach(m => { existingMarks[m.subject_id] = m; });

    const subjData = await api.teacher.subjects(student.department);
    const subjects = subjData.subjects || [];

    if (!subjects.length) {
      container.innerHTML = '<p style="color:var(--text-muted)">No subjects found for this department. Add subjects first.</p>';
      container.classList.remove('hidden');
      return;
    }

    container.innerHTML = `
      <h4 style="margin-bottom:1rem">Entering marks for: <span style="color:var(--primary-light)">${student.name} (${student.roll_number})</span></h4>
      <div class="table-container">
        <table>
          <thead><tr><th>Subject</th><th>Marks (0-100)</th><th>Attendance %</th><th>Assignment Score</th></tr></thead>
          <tbody>
            ${subjects.map(s => {
              const ex = existingMarks[s.id] || {};
              return `<tr class="marks-entry-row">
                <td><strong>${s.name}</strong></td>
                <td><input type="number" class="entry-marks" data-subject="${s.id}" min="0" max="100" value="${ex.marks || ''}" placeholder="0-100" /></td>
                <td><input type="number" class="entry-att" data-subject="${s.id}" min="0" max="100" value="${ex.attendance || ''}" placeholder="0-100" /></td>
                <td><input type="number" class="entry-assign" data-subject="${s.id}" min="0" max="100" value="${ex.assignment_score || ''}" placeholder="0-100" /></td>
              </tr>`;
            }).join('')}
          </tbody>
        </table>
      </div>
      <button class="btn btn-primary" style="margin-top:1rem" id="save-marks-btn" onclick="saveAllMarks(${studentId})">💾 Save All Marks</button>
    `;
    container.classList.remove('hidden');
  } catch (err) { showToast(err.message, 'error'); }
}

async function saveAllMarks(studentId) {
  const btn = document.getElementById('save-marks-btn');
  const entries = [];
  document.querySelectorAll('.entry-marks').forEach(inp => {
    if (inp.value !== '') {
      const sid = parseInt(inp.dataset.subject);
      const attEl = document.querySelector(`.entry-att[data-subject="${sid}"]`);
      const assignEl = document.querySelector(`.entry-assign[data-subject="${sid}"]`);
      entries.push({
        subject_id: sid,
        marks: parseFloat(inp.value),
        attendance: parseFloat(attEl?.value || 0),
        assignment_score: parseFloat(assignEl?.value || 0),
      });
    }
  });
  if (!entries.length) { showToast('Enter at least one mark', 'warning'); return; }
  setLoading(btn, true, 'Saving...');
  try {
    await api.teacher.enterMarks(studentId, entries);
    showToast(`${entries.length} mark record(s) saved!`, 'success');
    loadStudents();
  } catch (err) { showToast(err.message, 'error'); }
  finally { setLoading(btn, false); }
}

// ── Assignments ───────────────────────────────────────────────────────────────
async function loadAssignments() {
  try {
    const data = await api.teacher.assignments();
    allAssignments = data.assignments || [];
    document.getElementById('t-stat-assignments').textContent = allAssignments.length;
    let totalSubs = allAssignments.reduce((a,b) => a + (b.submission_count||0), 0);
    document.getElementById('t-stat-subs').textContent = totalSubs;
    renderAssignments();
    populateSubmissionSelect();
  } catch (err) { showToast(err.message, 'error'); }
}

function renderAssignments() {
  const container = document.getElementById('assignments-container');
  if (!allAssignments.length) { container.innerHTML = emptyState('📋', 'No assignments yet.'); return; }
  container.innerHTML = allAssignments.map(a => `
    <div class="card" style="margin-bottom:1rem">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.75rem">
        <div>
          <h3 style="margin-bottom:0.4rem">${a.title}</h3>
          <div style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:0.5rem">${a.description || ''}</div>
          <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
            <span class="badge badge-${isPastDeadline(a.deadline)?'danger':'info'}">📅 ${a.deadline ? formatDateTime(a.deadline) : 'No deadline'}</span>
            <span class="badge badge-primary">Dept: ${a.target_department || 'All'}</span>
            <span class="badge badge-success">${a.submission_count} submissions</span>
          </div>
        </div>
        <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
          ${a.original_filename ? `<a href="${api.teacher.downloadFile(a.id)}" target="_blank" class="btn btn-secondary btn-sm">⬇️ File</a>` : ''}
          <button class="btn btn-outline btn-sm" onclick="openSubmissionsFor(${a.id})">📊 Submissions</button>
          <button class="btn btn-danger btn-sm" onclick="deleteAssignment(${a.id})">🗑️</button>
        </div>
      </div>
    </div>
  `).join('');
}

document.getElementById('a-file')?.addEventListener('change', function() {
  document.getElementById('a-file-name').textContent = this.files[0]?.name || '';
});

async function createAssignment(e) {
  e.preventDefault();
  const btn = document.getElementById('create-assign-btn');
  const fd = new FormData();
  fd.append('title', document.getElementById('a-title').value);
  fd.append('description', document.getElementById('a-desc').value);
  const dateVal = document.getElementById('a-deadline-date').value;
  const timeVal = document.getElementById('a-deadline-time').value || '23:59';
  if (dateVal) {
    fd.append('deadline', `${dateVal}T${timeVal}`);
  }
  const dept = document.getElementById('a-dept').value;
  if (dept) fd.append('target_department', dept);
  const file = document.getElementById('a-file').files[0];
  if (file) fd.append('file', file);
  setLoading(btn, true, 'Creating...');
  try {
    await api.teacher.createAssignment(fd);
    showToast('Assignment created!', 'success');
    closeModal('modal-create-assign');
    e.target.reset();
    document.getElementById('a-file-name').textContent = '';
    loadAssignments();
  } catch (err) { showToast(err.message, 'error'); }
  finally { setLoading(btn, false); }
}

async function deleteAssignment(id) {
  confirmAction('Delete this assignment?', async () => {
    try { await api.teacher.deleteAssignment(id); showToast('Deleted', 'success'); loadAssignments(); }
    catch (err) { showToast(err.message, 'error'); }
  });
}

// ── Submissions ───────────────────────────────────────────────────────────────
function populateSubmissionSelect() {
  const sel = document.getElementById('sub-assign-sel');
  sel.innerHTML = '<option value="">-- Select Assignment --</option>' +
    allAssignments.map(a => `<option value="${a.id}">${a.title}</option>`).join('');
}

function openSubmissionsFor(id) {
  activateSection('sec-submissions');
  document.getElementById('sub-assign-sel').value = id;
  loadSubmissions();
}

async function loadSubmissions() {
  const id = document.getElementById('sub-assign-sel').value;
  const container = document.getElementById('submissions-container');
  if (!id) { container.innerHTML = ''; return; }
  try {
    const data = await api.teacher.submissions(id);
    document.getElementById('t-stat-subs').textContent = data.total_submitted;
    if (!data.submissions.length) { container.innerHTML = emptyState('📤', 'No submissions yet'); return; }
    container.innerHTML = `<div class="table-container"><table>
      <thead><tr><th>Student</th><th>Roll No</th><th>Submitted</th><th>Status</th><th>Grade</th><th>File</th><th>Actions</th></tr></thead>
      <tbody>${data.submissions.map(s => `
        <tr>
          <td><strong>${s.student_name}</strong></td>
          <td>${s.roll_number}</td>
          <td>${formatDateTime(s.submitted_at)}</td>
          <td>${submissionBadge(s.status)}</td>
          <td>${s.grade !== null ? s.grade : '--'}</td>
          <td>${s.original_filename ? `<a href="/api/teacher/submissions/${s.id}/download" class="btn btn-secondary btn-sm" target="_blank">⬇️</a>` : 'No file'}</td>
          <td><button class="btn btn-outline btn-sm" onclick="openReview(${s.id})">✏️ Review</button></td>
        </tr>`).join('')}
      </tbody>
    </table></div>`;
  } catch (err) { showToast(err.message, 'error'); }
}

function openReview(subId) {
  document.getElementById('review-sub-id').value = subId;
  document.getElementById('review-grade').value = '';
  document.getElementById('review-feedback').value = '';
  openModal('modal-review');
}

async function submitReview(e) {
  e.preventDefault();
  const btn = document.getElementById('review-btn');
  const id = document.getElementById('review-sub-id').value;
  setLoading(btn, true, 'Saving...');
  try {
    await api.teacher.reviewSubmission(id, {
      status: document.getElementById('review-status').value,
      grade: parseFloat(document.getElementById('review-grade').value || 0),
      feedback: document.getElementById('review-feedback').value,
    });
    showToast('Review saved!', 'success');
    closeModal('modal-review');
    loadSubmissions();
  } catch (err) { showToast(err.message, 'error'); }
  finally { setLoading(btn, false); }
}

// ── Subjects ──────────────────────────────────────────────────────────────────
async function loadSubjects() {
  try {
    const data = await api.teacher.subjects();
    allSubjects = data.subjects || [];
    document.getElementById('subjects-body').innerHTML = allSubjects.map(s => `
      <tr><td><strong>${s.name}</strong></td><td>${s.department}</td><td>Sem ${s.semester}</td><td>${s.max_marks}</td></tr>
    `).join('') || `<tr><td colspan="4">${emptyState('📚', 'No subjects. Add one!')}</td></tr>`;
  } catch (err) { showToast(err.message, 'error'); }
}

async function addSubject(e) {
  e.preventDefault();
  const btn = document.getElementById('add-subj-btn');
  setLoading(btn, true, 'Adding...');
  try {
    await api.teacher.addSubject({
      name: document.getElementById('subj-name').value,
      department: document.getElementById('subj-dept').value,
      semester: parseInt(document.getElementById('subj-sem').value),
      max_marks: parseFloat(document.getElementById('subj-max').value),
    });
    showToast('Subject added!', 'success');
    closeModal('modal-add-subject');
    loadSubjects();
  } catch (err) { showToast(err.message, 'error'); }
  finally { setLoading(btn, false); }
}

// Update at-risk count using students data
function updateAtRiskCount() {
  const atRisk = allStudents.filter(s => s.risk_level === 'High').length;
  document.getElementById('t-stat-weak').textContent = atRisk;
}
setTimeout(updateAtRiskCount, 1000);
