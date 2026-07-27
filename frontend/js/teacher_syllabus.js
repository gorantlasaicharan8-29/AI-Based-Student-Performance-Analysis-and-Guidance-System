// ============================================================
// js/teacher_syllabus.js - Syllabus management for teachers
// ============================================================

// ── Load subjects into the syllabus selector ──────────────────────────────────
async function loadSyllabusSubjects() {
  const sel = document.getElementById('syllabus-subject-sel');
  if (!sel) return;
  try {
    const data = await api.syllabus.subjects();
    const subjects = data.subjects || [];
    sel.innerHTML = `<option value="">-- Select Subject --</option>` +
      subjects.map(s =>
        `<option value="${s.id}" data-complete="${s.syllabus_complete}">${s.name} — ${s.department} ${s.syllabus_complete ? '✅' : `(${s.units_saved}/6)`}</option>`
      ).join('');
  } catch (err) {
    showToast('Failed to load subjects: ' + err.message, 'error');
  }
}

// ── Load the 6-unit editor for a selected subject ─────────────────────────────
async function loadSyllabusEditor() {
  const sel       = document.getElementById('syllabus-subject-sel');
  const container = document.getElementById('syllabus-editor-area');
  if (!sel || !container) return;

  const subjectId = sel.value;
  if (!subjectId) {
    container.innerHTML = `<div class="card" style="text-align:center;padding:3rem">
      <div style="font-size:3rem">📝</div>
      <p style="color:var(--text-muted);margin-top:0.75rem">Select a subject above to manage its 6-unit syllabus.</p>
    </div>`;
    return;
  }

  container.innerHTML = `<div class="card" style="text-align:center;padding:2rem"><p>Loading syllabus...</p></div>`;

  try {
    const data    = await api.syllabus.get(subjectId);
    const subject = data.subject;
    const units   = data.units;   // always 6 items

    container.innerHTML = `
      <div class="card">
        <div class="section-header" style="margin-bottom:1.25rem">
          <h3>📚 ${subject.name} — Syllabus Editor</h3>
          <span style="font-size:0.82rem;color:var(--text-muted)">${subject.department} · Sem ${subject.semester}</span>
        </div>
        <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:1.5rem">
          Define exactly 6 units. Each unit can have multiple topics (one per line).
        </p>
        <div id="unit-forms" style="display:grid;gap:1rem">
          ${units.map(u => renderUnitForm(u)).join('')}
        </div>
        <div style="margin-top:1.5rem;text-align:right">
          <button class="btn btn-primary" onclick="saveSyllabus(${subjectId})">
            💾 Save All 6 Units
          </button>
        </div>
      </div>
    `;
  } catch (err) {
    container.innerHTML = `<div class="card" style="color:var(--danger);padding:1.5rem">❌ ${err.message}</div>`;
  }
}

function renderUnitForm(unit) {
  const topicsText = unit.topics.map(t => t.name).join('\n');
  return `
    <div style="background:var(--bg-elevated);border-radius:12px;padding:1rem;border:1px solid var(--border)">
      <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem">
        <span style="background:var(--grad-primary);color:#fff;width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.9rem;flex-shrink:0">
          ${unit.unit_number}
        </span>
        <input type="text" id="unit-title-${unit.unit_number}" class="form-control"
          placeholder="Unit ${unit.unit_number} title (e.g. Introduction to Data Structures)"
          value="${escapeHtml(unit.title)}" style="flex:1" />
      </div>
      <textarea id="unit-topics-${unit.unit_number}" class="form-control"
        rows="4" placeholder="Enter topics, one per line..."
        style="font-size:0.83rem">${escapeHtml(topicsText)}</textarea>
      <div style="font-size:0.75rem;color:var(--text-muted);margin-top:0.4rem">
        ${unit.topics.length > 0 ? `${unit.topics.length} topic(s) saved` : 'No topics yet'}
      </div>
    </div>
  `;
}

function escapeHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Save all 6 units ──────────────────────────────────────────────────────────
async function saveSyllabus(subjectId) {
  const btn = document.querySelector('[onclick^="saveSyllabus"]');
  if (btn) { btn.disabled = true; btn.textContent = 'Saving...'; }

  const units = [];
  for (let n = 1; n <= 6; n++) {
    const title      = document.getElementById(`unit-title-${n}`)?.value?.trim() || `Unit ${n}`;
    const topicsRaw  = document.getElementById(`unit-topics-${n}`)?.value || '';
    const topics     = topicsRaw.split('\n').map(t => t.trim()).filter(Boolean);
    units.push({ unit_number: n, title, topics });
  }

  try {
    const result = await api.syllabus.save(subjectId, { units });
    showToast(result.message || 'Syllabus saved!', 'success');
    loadSyllabusSubjects();   // refresh dropdown badges
  } catch (err) {
    showToast('Save failed: ' + err.message, 'error');
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '💾 Save All 6 Units'; }
  }
}

// ── Weak Areas ────────────────────────────────────────────────────────────────
async function loadWeakAreas() {
  const container = document.getElementById('weak-areas-content');
  if (!container) return;
  container.innerHTML = `<div class="card" style="text-align:center;padding:2rem"><p>Loading weak area report...</p></div>`;

  try {
    const data   = await api.syllabus.weakAreas();
    const report = data.weak_area_report || [];

    if (!report.length) {
      container.innerHTML = `<div class="card" style="text-align:center;padding:3rem">
        <div style="font-size:3rem">✅</div>
        <p style="color:var(--text-muted)">No weak areas identified — all students performing well!</p>
      </div>`;
      return;
    }

    const PRIORITY_COLORS = { High: 'var(--danger)', Medium: 'var(--warning)', Low: 'var(--success)' };

    container.innerHTML = report.map(subject => `
      <div class="card" style="margin-bottom:1.25rem">
        <h4 style="margin:0 0 1rem">${subject.subject_name}</h4>
        <div style="display:grid;gap:0.75rem">
          ${subject.unit_weaknesses.map(uw => {
            const color = PRIORITY_COLORS[uw.priority] || 'var(--text-muted)';
            return `
              <div style="background:var(--bg-elevated);border-radius:10px;padding:0.9rem;border-left:3px solid ${color}">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
                  <strong>Unit ${uw.unit_number}: ${uw.unit_title}</strong>
                  <span style="background:${color}22;color:${color};font-size:0.75rem;padding:0.2rem 0.6rem;border-radius:99px;font-weight:700">
                    ${uw.priority} Priority
                  </span>
                </div>
                <div style="font-size:0.82rem;color:var(--text-muted)">
                  ${uw.students.length} student(s) need attention:
                  <span style="color:var(--text-primary);font-weight:600">
                    ${uw.students.map(s => `${s.name} (${s.marks}%)`).join(', ')}
                  </span>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<div class="card" style="color:var(--danger)">❌ ${err.message}</div>`;
  }
}
