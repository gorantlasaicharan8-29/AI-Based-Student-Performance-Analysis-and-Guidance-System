// ============================================================
// js/hod.js - HOD dashboard logic
// ============================================================

let hodStudents = [];
let gradeChart = null, riskChart = null, deptChart = null, subjectChart = null, trendChart = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth('hod')) return;
  chartDefaults();
  populateSidebarUser();
  await loadOverview();
  loadAtRisk();
  loadTopPerformers();
  loadHodAssignments();
  loadTeachers();
  loadAnalytics();
});

function onHodDeptChange() { loadOverview(); loadHodStudents(); loadAtRisk(); loadTopPerformers(); }

// ── Overview ──────────────────────────────────────────────────────────────────
async function loadOverview() {
  const dept = document.getElementById('hod-dept-filter').value;
  try {
    const data = await api.hod.overview(dept);
    document.getElementById('h-stat-students').textContent = data.total_students;
    document.getElementById('h-stat-teachers').textContent = data.total_teachers;
    document.getElementById('h-stat-assign').textContent = data.total_assignments;
    document.getElementById('h-stat-risk').textContent = data.at_risk_count;
    document.getElementById('h-stat-top').textContent = data.top_performers_count;
    document.getElementById('h-stat-subs').textContent = data.total_submissions;

    renderGradeChart(data.grade_distribution);
    renderRiskChart(data.risk_distribution);
    renderDeptChart(data.department_averages);
  } catch (err) { showToast(err.message, 'error'); }
}

function renderGradeChart(dist) {
  const ctx = document.getElementById('chart-grades');
  if (!ctx) return;
  if (gradeChart) gradeChart.destroy();
  gradeChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Grade A', 'Grade B', 'Grade C', 'Fail'],
      datasets: [{
        data: [dist.A||0, dist.B||0, dist.C||0, dist.Fail||0],
        backgroundColor: ['rgba(16,185,129,0.8)', 'rgba(59,130,246,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)'],
        borderWidth: 0,
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
}

function renderRiskChart(dist) {
  const ctx = document.getElementById('chart-risk');
  if (!ctx) return;
  if (riskChart) riskChart.destroy();
  riskChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Low Risk', 'Medium Risk', 'High Risk'],
      datasets: [{
        data: [dist.Low||0, dist.Medium||0, dist.High||0],
        backgroundColor: ['rgba(16,185,129,0.8)', 'rgba(245,158,11,0.8)', 'rgba(239,68,68,0.8)'],
        borderWidth: 0,
      }]
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
  });
}

function renderDeptChart(deptData) {
  const ctx = document.getElementById('chart-dept');
  if (!ctx || !deptData || !deptData.length) return;
  if (deptChart) deptChart.destroy();
  deptChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: deptData.map(d => d.department),
      datasets: [{
        label: 'Average Marks (%)',
        data: deptData.map(d => d.average_marks),
        backgroundColor: deptData.map(d =>
          d.average_marks >= 75 ? 'rgba(16,185,129,0.7)' : d.average_marks >= 50 ? 'rgba(245,158,11,0.7)' : 'rgba(239,68,68,0.7)'
        ),
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } }, x: { grid: { display: false } } }
    }
  });
}

// ── Analytics ─────────────────────────────────────────────────────────────────
async function loadAnalytics() {
  const dept = document.getElementById('hod-dept-filter').value;
  try {
    const [subjData, trendData] = await Promise.all([
      api.hod.subjectAnalytics(dept),
      api.hod.trends(),
    ]);

    // Subject table
    const tbody = document.getElementById('subject-analytics-body');
    const subjects = subjData.subjects || [];
    tbody.innerHTML = subjects.map(s => `
      <tr>
        <td><strong>${s.subject}</strong></td>
        <td style="color:${marksColor(s.average_marks)};font-weight:700">${fmtNum(s.average_marks)}%</td>
        <td>${s.student_count}</td>
        <td style="min-width:150px">${progressBar(s.average_marks)}</td>
      </tr>
    `).join('') || `<tr><td colspan="4" style="text-align:center;color:var(--text-muted)">No data</td></tr>`;

    // Subject chart
    if (subjects.length) {
      const ctx = document.getElementById('chart-subjects-hod');
      if (ctx) {
        if (subjectChart) subjectChart.destroy();
        subjectChart = new Chart(ctx, {
          type: 'bar',
          data: {
            labels: subjects.map(s => s.subject),
            datasets: [{ label: 'Avg Marks', data: subjects.map(s => s.average_marks), backgroundColor: 'rgba(99,102,241,0.7)', borderRadius: 6 }]
          },
          options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { min: 0, max: 100 } } }
        });
      }
    }

    // Trends chart
    const trends = trendData.trends || [];
    if (trends.length) {
      const ctx2 = document.getElementById('chart-trends');
      if (ctx2) {
        if (trendChart) trendChart.destroy();
        trendChart = new Chart(ctx2, {
          type: 'line',
          data: {
            labels: trends.map(t => t.month),
            datasets: [
              { label: 'Grade A', data: trends.map(t => t.A), borderColor: '#10b981', tension: 0.4, fill: false },
              { label: 'Grade B', data: trends.map(t => t.B), borderColor: '#3b82f6', tension: 0.4, fill: false },
              { label: 'High Risk', data: trends.map(t => t.High_Risk), borderColor: '#ef4444', tension: 0.4, fill: false },
            ]
          },
          options: { responsive: true, maintainAspectRatio: false, scales: { y: { grid: { color: 'rgba(255,255,255,0.05)' } } } }
        });
      }
    }
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Students ──────────────────────────────────────────────────────────────────
async function loadHodStudents() {
  const dept = document.getElementById('hod-dept-filter').value;
  const perf = document.getElementById('hod-perf-filter')?.value;
  try {
    const params = { per_page: 50 };
    if (dept) params.department = dept;
    if (perf) params.performance = perf;
    const data = await api.hod.students(params);
    hodStudents = data.students || [];
    renderHodStudentTable(hodStudents);
  } catch (err) { showToast(err.message, 'error'); }
}

// Load students when section is activated
document.querySelector('[data-section="sec-students"]')?.addEventListener('click', loadHodStudents);

function filterHodStudents() {
  const q = document.getElementById('hod-student-search').value.toLowerCase();
  const perf = document.getElementById('hod-perf-filter').value;
  let filtered = hodStudents.filter(s =>
    s.name.toLowerCase().includes(q) || s.roll_number.toLowerCase().includes(q) || s.department.toLowerCase().includes(q)
  );
  if (perf === 'strong') filtered = filtered.filter(s => s.average_marks > 75);
  if (perf === 'average') filtered = filtered.filter(s => s.average_marks >= 50 && s.average_marks <= 75);
  if (perf === 'weak') filtered = filtered.filter(s => s.average_marks < 50);
  renderHodStudentTable(filtered);
}

function renderHodStudentTable(students) {
  const tbody = document.getElementById('hod-student-body');
  if (!students.length) { tbody.innerHTML = `<tr><td colspan="9">${emptyState('👨‍🎓', 'No students found')}</td></tr>`; return; }
  tbody.innerHTML = students.map(s => `
    <tr>
      <td><strong>${s.name}</strong></td>
      <td style="color:var(--text-muted)">${s.roll_number}</td>
      <td>${s.department}</td>
      <td>Sem ${s.semester}</td>
      <td style="color:${marksColor(s.average_marks||0)};font-weight:700">${fmtNum(s.average_marks||0)}%</td>
      <td>${s.num_subjects||0}</td>
      <td>${s.grade ? gradeBadge(s.grade) : '<span class="badge badge-info">N/A</span>'}</td>
      <td>${s.risk_level ? riskBadge(s.risk_level) : '<span class="badge badge-info">N/A</span>'}</td>
      <td><button class="btn btn-secondary btn-sm" onclick="viewHodStudentFull(${s.id})">🔍 Full Data</button></td>
    </tr>
  `).join('');
}

async function viewHodStudentFull(id) {
  try {
    const data = await api.hod.studentFull(id);
    const { student, marks, predictions, submissions } = data;
    const latest = predictions[0];
    document.getElementById('hod-detail-title').textContent = `${student.name} — ${student.roll_number}`;
    document.getElementById('hod-detail-content').innerHTML = `
      <div style="display:flex;gap:0.75rem;flex-wrap:wrap;margin-bottom:1.25rem">
        ${[['Dept', student.department], ['Sem', `Sem ${student.semester}`],
           ['Avg Marks', latest ? `${fmtNum(latest.average_marks)}%` : 'N/A'],
           ['Grade', latest ? latest.grade : 'N/A'], ['Risk', latest ? latest.risk_level : 'N/A']].map(([k,v]) =>
          `<div style="background:var(--bg-elevated);padding:0.5rem 0.9rem;border-radius:var(--radius-md);text-align:center">
            <div style="font-size:0.7rem;color:var(--text-muted)">${k}</div><div style="font-weight:700">${v}</div>
          </div>`).join('')}
      </div>
      <h4 style="margin-bottom:0.75rem">📊 Marks</h4>
      ${marks.length ? marks.map(m => `
        <div class="perf-bar-wrap">
          <div class="perf-bar-label"><span>${m.subject_name}</span><span style="color:${marksColor(m.marks)}">${m.marks}/100 | Att: ${pct(m.attendance)}</span></div>
          ${progressBar(m.marks)}
        </div>`).join('') : '<p style="color:var(--text-muted)">No marks recorded</p>'}
      <h4 style="margin:1rem 0 0.75rem">📤 Submissions (${submissions.length})</h4>
      ${submissions.length ? `<div style="display:flex;flex-direction:column;gap:0.4rem">
        ${submissions.map(s => `
          <div style="display:flex;justify-content:space-between;padding:0.5rem;background:var(--bg-elevated);border-radius:var(--radius-sm)">
            <span style="font-size:0.85rem">${s.assignment_title}</span>
            <span>${submissionBadge(s.status)}</span>
          </div>`).join('')}
      </div>` : '<p style="color:var(--text-muted)">No submissions</p>'}
    `;
    openModal('modal-hod-student');
  } catch (err) { showToast(err.message, 'error'); }
}

// ── At-Risk ───────────────────────────────────────────────────────────────────
async function loadAtRisk() {
  const dept = document.getElementById('hod-dept-filter').value;
  try {
    const data = await api.hod.atRisk(dept);
    const container = document.getElementById('atrisk-list');
    if (!data.at_risk_students.length) { container.innerHTML = emptyState('✅', 'No high-risk students found!'); return; }
    container.innerHTML = data.at_risk_students.map(s => {
      const pred = s.prediction || {};
      return `
        <div class="card" style="margin-bottom:1rem;border-left:3px solid var(--danger)">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.75rem">
            <div>
              <h3 style="margin-bottom:0.3rem">${s.name} <span style="color:var(--text-muted);font-weight:400;font-size:0.85rem">(${s.roll_number})</span></h3>
              <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
                <span class="badge badge-primary">${s.department}</span>
                <span class="badge badge-danger">High Risk</span>
                ${pred.grade ? gradeBadge(pred.grade) : ''}
                <span class="badge badge-warning">Avg: ${fmtNum(pred.average_marks||0)}%</span>
                <span class="badge badge-info">Att: ${fmtNum(pred.average_attendance||0)}%</span>
              </div>
            </div>
            <button class="btn btn-secondary btn-sm" onclick="viewHodStudentFull(${s.id})">📋 Full Data</button>
          </div>
        </div>`;
    }).join('');
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Top Performers ────────────────────────────────────────────────────────────
async function loadTopPerformers() {
  const dept = document.getElementById('hod-dept-filter').value;
  try {
    const data = await api.hod.topPerformers(dept);
    const container = document.getElementById('top-list');
    if (!data.top_performers.length) { container.innerHTML = emptyState('⭐', 'No data yet.'); return; }
    container.innerHTML = data.top_performers.map((p, i) => {
      const s = p.student;
      const medal = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : `#${i+1}`;
      return `
        <div class="card" style="margin-bottom:0.75rem;display:flex;align-items:center;gap:1.5rem">
          <div style="font-size:1.5rem;min-width:40px;text-align:center">${medal}</div>
          <div style="flex:1">
            <div style="font-weight:700">${s.name} <span style="color:var(--text-muted);font-size:0.85rem">(${s.roll_number})</span></div>
            <div style="font-size:0.82rem;color:var(--text-secondary)">${s.department} · Sem ${s.semester}</div>
          </div>
          <div style="font-size:1.5rem;font-weight:900;color:var(--success)">${fmtNum(p.average_marks)}%</div>
        </div>`;
    }).join('');
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Assignments ───────────────────────────────────────────────────────────────
async function loadHodAssignments() {
  try {
    const data = await api.hod.assignments();
    const container = document.getElementById('hod-assign-list');
    if (!data.assignments.length) { container.innerHTML = emptyState('📋', 'No assignments'); return; }
    container.innerHTML = `<div class="table-container"><table>
      <thead><tr><th>Title</th><th>Teacher</th><th>Department</th><th>Deadline</th><th>Submissions</th><th>Status</th></tr></thead>
      <tbody>${data.assignments.map(a => `
        <tr>
          <td><strong>${a.title}</strong></td>
          <td>${a.teacher_name}</td>
          <td>${a.target_department || 'All'}</td>
          <td><span class="badge badge-${isPastDeadline(a.deadline)?'danger':'info'}">${a.deadline ? formatDate(a.deadline) : 'No deadline'}</span></td>
          <td>${a.submission_count} <small style="color:var(--text-muted)">(${a.submission_rate||'--'})</small></td>
          <td><span class="badge badge-${a.is_active?'success':'warning'}">${a.is_active?'Active':'Inactive'}</span></td>
        </tr>`).join('')}
      </tbody>
    </table></div>`;
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Teachers ──────────────────────────────────────────────────────────────────
async function loadTeachers() {
  const dept = document.getElementById('hod-dept-filter').value;
  try {
    const data = await api.hod.teachers(dept);
    document.getElementById('hod-teachers-body').innerHTML = data.teachers.map(t => `
      <tr>
        <td><strong>${t.name}</strong></td>
        <td style="color:var(--text-muted)">${t.email}</td>
        <td>${t.department || 'N/A'}</td>
        <td><span class="badge badge-primary">${t.assignments_created} assignments</span></td>
      </tr>
    `).join('') || `<tr><td colspan="4">${emptyState('👩‍🏫', 'No teachers found')}</td></tr>`;
  } catch (err) { showToast(err.message, 'error'); }
}
