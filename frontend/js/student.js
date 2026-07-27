// ============================================================
// js/student.js - Student dashboard logic
// ============================================================

let subjectChart = null;
let cachedPrediction = null;
let cachedGuidance = null;

document.addEventListener('DOMContentLoaded', async () => {
  if (!requireAuth('student')) return;
  chartDefaults();
  populateSidebarUser();

  document.getElementById('pdf-btn').href = `${api.student.reportPdf()}?token=${getToken()}`;

  await Promise.all([loadPerformance(), loadNotifications(), loadSubjectsForModal()]);
  loadAssignments();
});

// ── Performance & Overview ────────────────────────────────────────────────────
async function loadPerformance() {
  try {
    const data = await api.student.performance();
    const { marks, analytics, latest_prediction } = data;

    // Stats
    document.getElementById('stat-avg').textContent = analytics.average_marks ? `${analytics.average_marks}%` : '--';
    document.getElementById('stat-att').textContent = analytics.average_attendance ? `${analytics.average_attendance}%` : '--';
    document.getElementById('stat-strong').textContent = analytics.num_strong ?? '--';
    document.getElementById('stat-weak').textContent = analytics.num_weak ?? '--';

    renderMarksTable(marks);
    renderMarksDetailSection(marks, analytics);
    renderSubjectChart(marks);

    if (latest_prediction) {
      cachedPrediction = latest_prediction;
      renderPredictionSummary(latest_prediction);
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderMarksTable(marks) {
  const tbody = document.getElementById('marks-table-body');
  if (!marks || !marks.length) {
    tbody.innerHTML = `<tr><td colspan="6">${emptyState('📚', 'No marks recorded yet.')}</td></tr>`;
    return;
  }
  tbody.innerHTML = marks.map(m => `
    <tr>
      <td><strong>${m.subject_name}</strong></td>
      <td style="color:${marksColor(m.marks)};font-weight:700">${m.marks}/100</td>
      <td>${pct(m.attendance)}</td>
      <td>${m.assignment_score}/100</td>
      <td style="min-width:120px">${progressBar(m.marks)}</td>
      <td><span class="badge badge-${m.marks>75?'success':m.marks<50?'danger':'warning'}">${marksLabel(m.marks)}</span></td>
    </tr>
  `).join('');
}

function renderMarksDetailSection(marks, analytics) {
  const container = document.getElementById('marks-detail-content');
  if (!marks || !marks.length) {
    container.innerHTML = emptyState('📚', 'No marks yet. Add your marks to get started.');
    return;
  }
  container.innerHTML = `
    <div style="display:flex;gap:2rem;flex-wrap:wrap;margin-bottom:1.5rem">
      <div><span style="color:var(--text-muted);font-size:0.85rem">Total Marks</span><br><strong style="font-size:1.4rem">${analytics.total_marks}</strong></div>
      <div><span style="color:var(--text-muted);font-size:0.85rem">Average</span><br><strong style="font-size:1.4rem;color:${marksColor(analytics.average_marks)}">${analytics.average_marks}%</strong></div>
      <div><span style="color:var(--text-muted);font-size:0.85rem">Strong Subjects</span><br><strong style="font-size:1.4rem;color:var(--success)">${analytics.num_strong}</strong></div>
      <div><span style="color:var(--text-muted);font-size:0.85rem">Weak Subjects</span><br><strong style="font-size:1.4rem;color:var(--danger)">${analytics.num_weak}</strong></div>
    </div>
    ${marks.map(m => `
      <div class="perf-bar-wrap">
        <div class="perf-bar-label">
          <span>${m.subject_name}</span>
          <span style="color:${marksColor(m.marks)}">${m.marks}/100 — Att: ${pct(m.attendance)}</span>
        </div>
        ${progressBar(m.marks)}
      </div>
    `).join('')}
  `;
}

function renderSubjectChart(marks) {
  const ctx = document.getElementById('chart-subjects');
  if (!ctx || !marks || !marks.length) return;
  if (subjectChart) subjectChart.destroy();
  subjectChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: marks.map(m => m.subject_name),
      datasets: [{
        label: 'Marks',
        data: marks.map(m => m.marks),
        backgroundColor: marks.map(m => m.marks > 75 ? 'rgba(16,185,129,0.7)' : m.marks < 50 ? 'rgba(239,68,68,0.7)' : 'rgba(245,158,11,0.7)'),
        borderRadius: 6,
      }, {
        label: 'Attendance',
        data: marks.map(m => m.attendance),
        backgroundColor: 'rgba(99,102,241,0.4)',
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
        x: { grid: { display: false } }
      }
    }
  });
}

function renderPredictionSummary(pred) {
  const gradeColors = { A: 'var(--success)', B: 'var(--info)', C: 'var(--warning)', Fail: 'var(--danger)' };
  const riskColors = { Low: 'var(--success)', Medium: 'var(--warning)', High: 'var(--danger)' };
  document.getElementById('pred-summary').innerHTML = `
    <div style="display:flex;gap:1.5rem;flex-wrap:wrap;margin-bottom:1rem">
      <div style="text-align:center;flex:1">
        <div style="font-size:2.5rem;font-weight:900;color:${gradeColors[pred.grade]}">${pred.grade}</div>
        <div style="font-size:0.8rem;color:var(--text-muted)">Predicted Grade</div>
      </div>
      <div style="text-align:center;flex:1">
        <div style="font-size:1.8rem;font-weight:800;color:${riskColors[pred.risk_level]}">${pred.risk_level}</div>
        <div style="font-size:0.8rem;color:var(--text-muted)">Risk Level</div>
      </div>
      <div style="text-align:center;flex:1">
        <div style="font-size:1.8rem;font-weight:800;color:var(--primary-light)">${pred.confidence}%</div>
        <div style="font-size:0.8rem;color:var(--text-muted)">Confidence</div>
      </div>
    </div>
    <div class="progress" style="height:8px">
      <div class="progress-bar" style="width:${pred.confidence}%"></div>
    </div>
  `;
}

// ── AI Prediction ──────────────────────────────────────────────────────────────
async function runPrediction() {
  const btn = document.getElementById('run-predict-btn');
  setLoading(btn, true, 'Analyzing...');
  try {
    const data = await api.student.predict();
    cachedPrediction = data.prediction;
    cachedGuidance = data.guidance;

    renderPredictionResult(data.prediction);
    renderGuidance(data.guidance);
    renderPredictionSummary(data.prediction);
    showToast('AI analysis complete! ✅', 'success');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

function renderPredictionResult(pred) {
  const gradeColors = { A: '#10b981', B: '#3b82f6', C: '#f59e0b', Fail: '#ef4444' };
  const riskColors = { Low: '#10b981', Medium: '#f59e0b', High: '#ef4444' };
  const analytics = pred.analytics || {};

  document.getElementById('prediction-result').innerHTML = `
    <div class="grid-2" style="margin-bottom:1.5rem">
      <div class="card" style="text-align:center">
        <div style="font-size:4rem;font-weight:900;color:${gradeColors[pred.grade]};line-height:1">${pred.grade}</div>
        <div style="font-size:0.9rem;color:var(--text-muted);margin-top:0.3rem">Predicted Final Grade</div>
        <div style="margin-top:0.75rem;font-size:0.85rem;color:var(--text-secondary)">Confidence: <strong style="color:var(--primary-light)">${pred.confidence}%</strong></div>
      </div>
      <div class="card" style="text-align:center">
        <div style="font-size:2.5rem;font-weight:900;color:${riskColors[pred.risk_level]};line-height:1">${pred.risk_level}</div>
        <div style="font-size:0.9rem;color:var(--text-muted);margin-top:0.3rem">Academic Risk Level</div>
        <div style="margin-top:0.75rem">
          <div class="badge badge-${pred.risk_level==='Low'?'success':pred.risk_level==='High'?'danger':'warning'}">${pred.risk_level} Risk</div>
        </div>
      </div>
    </div>
    <div class="card">
      <h3 style="margin-bottom:1rem">📊 Performance Analytics</h3>
      <div class="grid-3" style="gap:1rem;margin-bottom:1.5rem">
        <div style="text-align:center"><div style="font-size:1.6rem;font-weight:800;color:${marksColor(analytics.average_marks)}">${fmtNum(analytics.average_marks)}%</div><div style="font-size:0.8rem;color:var(--text-muted)">Avg Marks</div></div>
        <div style="text-align:center"><div style="font-size:1.6rem;font-weight:800;color:${marksColor(analytics.average_attendance)}">${fmtNum(analytics.average_attendance)}%</div><div style="font-size:0.8rem;color:var(--text-muted)">Avg Attendance</div></div>
        <div style="text-align:center"><div style="font-size:1.6rem;font-weight:800;color:var(--primary-light)">${analytics.num_weak_subjects ?? 0}</div><div style="font-size:0.8rem;color:var(--text-muted)">Weak Subjects</div></div>
      </div>
      <h4 style="margin-bottom:0.75rem">🔍 Key Factors (Explainable AI)</h4>
      ${(pred.factors || []).map(f => `
        <div style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0;border-bottom:1px solid var(--border)">
          <span style="font-size:1.1rem">${f.impact==='positive'?'✅':f.impact==='negative'?'❌':'➡️'}</span>
          <div style="flex:1">
            <span style="font-size:0.88rem;color:var(--text-primary)">${f.factor}</span>
          </div>
          <span style="font-size:0.82rem;font-weight:700;color:${f.impact==='positive'?'var(--success)':f.impact==='negative'?'var(--danger)':'var(--warning)'}">${f.value}</span>
        </div>
      `).join('')}
    </div>
  `;
}

// ── Guidance ──────────────────────────────────────────────────────────────────
function renderGuidance(g) {
  const container = document.getElementById('guidance-content');
  if (!g) return;
  const attStatus = g.attendance_status || {};
  container.innerHTML = `
    <div class="card" style="margin-bottom:1.5rem;background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(6,182,212,0.05));border-color:var(--primary)">
      <div style="font-size:1.1rem;font-weight:700">${g.motivational_message || ''}</div>
      <div style="margin-top:0.5rem;font-size:0.85rem;color:${attStatus.color||'var(--text-secondary)'}">${attStatus.message || ''}</div>
    </div>
    <div class="grid-2">
      <div class="card">
        <h3 style="margin-bottom:1rem">🎯 Priority Actions</h3>
        ${(g.priority_actions || []).map((a, i) => `
          <div style="display:flex;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border)">
            <span style="color:var(--primary-light);font-weight:700;min-width:1.2rem">${i+1}.</span>
            <span style="font-size:0.88rem;color:var(--text-secondary)">${a}</span>
          </div>
        `).join('')}
      </div>
      <div class="card">
        <h3 style="margin-bottom:1rem">💡 Recommendations</h3>
        ${(g.recommendations || []).map((r, i) => `
          <div style="display:flex;gap:0.75rem;padding:0.5rem 0;border-bottom:1px solid var(--border)">
            <span style="color:var(--accent);font-weight:700;min-width:1.2rem">${i+1}.</span>
            <span style="font-size:0.88rem;color:var(--text-secondary)">${r}</span>
          </div>
        `).join('')}
      </div>
    </div>
    <div class="card" style="margin-top:1.5rem">
      <h3 style="margin-bottom:1rem">📅 Weekly Study Plan (${g.daily_study_hours}h/day)</h3>
      <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:0.75rem">
        ${(g.weekly_plan || []).map(day => `
          <div style="background:var(--bg-elevated);border:1px solid var(--border);border-radius:var(--radius-md);padding:0.85rem">
            <div style="font-size:0.78rem;font-weight:700;color:var(--primary-light);text-transform:uppercase;margin-bottom:0.3rem">${day.day}</div>
            <div style="font-size:0.85rem;color:var(--text-primary)">${day.focus}</div>
            <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.3rem">${day.hours}h study</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// ── Assignments ───────────────────────────────────────────────────────────────
async function loadAssignments() {
  try {
    const data = await api.student.assignments();
    const container = document.getElementById('assignments-list');
    if (!data.assignments || !data.assignments.length) {
      container.innerHTML = emptyState('📋', 'No assignments assigned yet.');
      return;
    }
    container.innerHTML = data.assignments.map(a => {
      const overdue = isPastDeadline(a.deadline);
      return `
        <div class="card" style="margin-bottom:1rem">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.75rem">
            <div>
              <h3 style="margin-bottom:0.4rem">${a.title}</h3>
              <div style="font-size:0.85rem;color:var(--text-secondary);margin-bottom:0.5rem">${a.description || 'No description'}</div>
              <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
                <span class="badge badge-${overdue?'danger':'info'}">📅 ${a.deadline ? formatDateTime(a.deadline) : 'No deadline'}${overdue?' (Overdue)':''}</span>
                <span class="badge badge-primary">By: ${a.teacher_name}</span>
                ${a.submitted ? '<span class="badge badge-success">✅ Submitted</span>' : '<span class="badge badge-warning">⏳ Pending</span>'}
              </div>
            </div>
            <div style="display:flex;gap:0.5rem;flex-wrap:wrap">
              ${a.original_filename ? `<a href="${api.teacher.downloadFile(a.id)}" target="_blank" class="btn btn-secondary btn-sm">⬇️ Download</a>` : ''}
              ${!a.submitted && !overdue ? `<button class="btn btn-primary btn-sm" onclick="openSubmitModal(${a.id},'${a.title}')">📤 Submit</button>` : ''}
              ${a.submitted && a.submission ? `<div style="font-size:0.8rem;color:var(--text-muted)">Submitted: ${formatDateTime(a.submission.submitted_at)}</div>` : ''}
            </div>
          </div>
        </div>
      `;
    }).join('');
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function openSubmitModal(id, title) {
  document.getElementById('submit-assign-id').value = id;
  document.getElementById('submit-modal-title').textContent = `Submit: ${title}`;
  document.getElementById('submit-file-name').textContent = '';
  document.getElementById('submit-file').value = '';
  openModal('modal-submit');
}

document.getElementById('submit-file')?.addEventListener('change', function() {
  document.getElementById('submit-file-name').textContent = this.files[0]?.name || '';
});

async function submitAssignment(e) {
  e.preventDefault();
  const btn = document.getElementById('submit-assign-btn');
  const id = document.getElementById('submit-assign-id').value;
  const file = document.getElementById('submit-file').files[0];
  const fd = new FormData();
  if (file) fd.append('file', file);
  setLoading(btn, true, 'Submitting...');
  try {
    await api.student.submit(id, fd);
    showToast('Assignment submitted! ✅', 'success');
    closeModal('modal-submit');
    loadAssignments();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Marks Modal ───────────────────────────────────────────────────────────────
async function loadSubjectsForModal() {
  try {
    const user = Auth.getUser();
    const data = await api.teacher.subjects(user.department);
    const sel = document.getElementById('mark-subject-id');
    sel.innerHTML = '<option value="">Select subject</option>' +
      (data.subjects || []).map(s => `<option value="${s.id}">${s.name}</option>`).join('');
  } catch (_) {}
}

async function submitMark(e) {
  e.preventDefault();
  const btn = document.getElementById('save-mark-btn');
  setLoading(btn, true, 'Saving...');
  try {
    await api.student.addMark({
      subject_id: parseInt(document.getElementById('mark-subject-id').value),
      marks: parseFloat(document.getElementById('mark-marks').value),
      attendance: parseFloat(document.getElementById('mark-att').value || 0),
      assignment_score: parseFloat(document.getElementById('mark-assign').value || 0),
    });
    showToast('Marks saved!', 'success');
    closeModal('modal-add-mark');
    loadPerformance();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

// ── Notifications ─────────────────────────────────────────────────────────────
async function loadNotifications() {
  try {
    const data = await api.student.notifications();
    const list = document.getElementById('notif-list');
    const dot = document.getElementById('notif-dot');
    if (data.unread_count > 0) dot.classList.remove('hidden');

    if (!data.notifications?.length) {
      list.innerHTML = emptyState('🔔', 'No notifications');
      return;
    }
    list.innerHTML = data.notifications.map(n => `
      <div class="notif-item ${n.is_read ? '' : 'unread'}">
        ${!n.is_read ? '<div class="notif-dot-indicator"></div>' : '<div style="width:8px"></div>'}
        <div class="notif-content">
          <div class="notif-title">${n.title}</div>
          <div class="notif-msg">${n.message}</div>
          <div class="notif-time">${timeAgo(n.created_at)}</div>
        </div>
      </div>
    `).join('');
  } catch (_) {}
}

async function markAllRead() {
  await api.student.markRead();
  document.getElementById('notif-dot').classList.add('hidden');
  loadNotifications();
}

function toggleNotifPanel() {
  document.getElementById('notif-panel').classList.toggle('hidden');
}

// Close notif panel on outside click
document.addEventListener('click', e => {
  const panel = document.getElementById('notif-panel');
  const toggle = document.getElementById('notif-toggle');
  if (!panel.contains(e.target) && !toggle.contains(e.target)) {
    panel.classList.add('hidden');
  }
});

// Profile
async function loadProfile() {
  try {
    const data = await api.student.profile();
    const s = data.student;
    document.getElementById('profile-content').innerHTML = `
      <div class="grid-2">
        <div>
          <h3 style="margin-bottom:1rem">Personal Information</h3>
          ${[['Name', s.name], ['Email', s.email], ['Roll Number', s.roll_number], ['Department', s.department], ['Semester', s.semester]].map(([k,v]) => `
            <div style="display:flex;justify-content:space-between;padding:0.6rem 0;border-bottom:1px solid var(--border)">
              <span style="color:var(--text-muted);font-size:0.85rem">${k}</span>
              <span style="font-weight:600">${v || 'N/A'}</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  } catch (_) {}
}

document.querySelector('[data-section="sec-profile"]')?.addEventListener('click', loadProfile);

// ── Unit Recommendations (Syllabus Module) ────────────────────────────────────
let _unitsLoaded = false;

async function loadUnitRecommendations() {
  const container = document.getElementById('unit-rec-content');
  if (!container) return;

  container.innerHTML = `<div class="card" style="text-align:center;padding:2rem">
    <div style="font-size:2rem;animation:spin 1s linear infinite">⏳</div>
    <p style="color:var(--text-muted);margin-top:0.75rem">Loading your AI recommendations...</p>
  </div>`;

  try {
    const data = await api.syllabus.recommendations();
    const recs  = data.recommendations || [];

    if (!recs.length) {
      container.innerHTML = `<div class="card" style="text-align:center;padding:3rem">
        <div style="font-size:3rem">📭</div>
        <p style="color:var(--text-muted);margin-top:0.75rem">No marks found yet — add your marks first to get recommendations.</p>
      </div>`;
      return;
    }

    const PRIORITY_COLORS = { High: 'var(--danger)', Medium: 'var(--warning)', Low: 'var(--success)' };
    const PRIORITY_BG     = { High: 'rgba(239,68,68,0.1)', Medium: 'rgba(245,158,11,0.1)', Low: 'rgba(16,185,129,0.1)' };
    const PERF_ICONS      = { High: '🌟', Medium: '📈', Low: '⚠️' };

    container.innerHTML = `
      <!-- Summary banner -->
      <div class="card" style="margin-bottom:1.5rem;background:var(--grad-primary);border:none">
        <div style="display:flex;align-items:center;gap:1rem">
          <div style="font-size:2.5rem">🤖</div>
          <div>
            <h3 style="margin:0;color:#fff">AI Study Plan — ${data.student?.name || ''}</h3>
            <p style="margin:0.25rem 0 0;color:rgba(255,255,255,0.8);font-size:0.88rem">
              ${recs.length} subject(s) analysed &nbsp;·&nbsp;
              ${recs.filter(r=>r.priority==='High').length} High-priority &nbsp;·&nbsp;
              ${recs.filter(r=>r.priority==='Medium').length} Medium-priority
            </p>
          </div>
        </div>
      </div>

      <!-- Per-subject recommendation cards -->
      <div style="display:grid;gap:1.25rem">
        ${recs.map(rec => {
          const color = PRIORITY_COLORS[rec.priority];
          const bg    = PRIORITY_BG[rec.priority];
          const icon  = PERF_ICONS[rec.performance_level];
          return `
          <div class="card" style="border-left:4px solid ${color}">
            <!-- Header -->
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem">
              <div>
                <h4 style="margin:0">${rec.subject_name}</h4>
                <div style="margin-top:0.35rem;font-size:0.82rem;color:var(--text-muted)">
                  ${icon} Performance: <strong style="color:${color}">${rec.performance_level}</strong>
                  &nbsp;·&nbsp; Marks: <strong>${rec.marks}/100</strong>
                  &nbsp;·&nbsp; Attendance: <strong>${rec.attendance}%</strong>
                </div>
              </div>
              <span style="background:${bg};color:${color};border:1px solid ${color};padding:0.25rem 0.75rem;border-radius:99px;font-size:0.78rem;font-weight:700;white-space:nowrap">
                ${rec.priority} Priority
              </span>
            </div>

            <!-- AI message -->
            <div style="background:var(--bg-elevated);border-radius:10px;padding:0.85rem 1rem;margin-bottom:1rem;font-size:0.88rem;color:var(--text-secondary)">
              💡 ${rec.message}
            </div>
            <div style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem">
              🎯 Goal: <em>${rec.goal}</em>
            </div>

            <!-- Recommended units -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:0.75rem">
              ${rec.recommended_units.map(u => `
                <div style="background:${bg};border:1px solid ${color}33;border-radius:10px;padding:0.9rem">
                  <div style="font-weight:700;color:${color};font-size:0.85rem;margin-bottom:0.35rem">
                    Unit ${u.unit_number}: ${u.title}
                  </div>
                  ${u.topics && u.topics.length ? `
                    <ul style="margin:0;padding-left:1.1rem;color:var(--text-secondary);font-size:0.8rem">
                      ${u.topics.slice(0,4).map(t => `<li>${t.name}</li>`).join('')}
                      ${u.topics.length > 4 ? `<li style="color:var(--text-muted)">+${u.topics.length-4} more...</li>` : ''}
                    </ul>
                  ` : `<p style="font-size:0.78rem;color:var(--text-muted);margin:0">Syllabus not yet uploaded</p>`}
                </div>
              `).join('')}
            </div>
          </div>`;
        }).join('')}
      </div>
    `;
    _unitsLoaded = true;
  } catch (err) {
    container.innerHTML = `<div class="card" style="text-align:center;padding:2rem;color:var(--danger)">
      ❌ ${err.message}
    </div>`;
  }
}
