// ============================================================
// js/hod_syllabus.js - HOD unit difficulty analysis
// ============================================================

async function loadHodUnitAnalysis() {
  const container = document.getElementById('unit-analysis-content');
  if (!container) return;
  container.innerHTML = `<div class="card" style="text-align:center;padding:2rem"><p>Loading...</p></div>`;

  try {
    const dept   = document.getElementById('hod-dept-filter')?.value || '';
    const data   = await api.syllabus.unitAnalysis(dept);
    const report = data.unit_analysis || [];

    if (!report.length) {
      container.innerHTML = `<div class="card" style="text-align:center;padding:3rem">
        <div style="font-size:3rem">✅</div>
        <p style="color:var(--text-muted)">No data available. Add student marks first.</p>
      </div>`;
      return;
    }

    container.innerHTML = report.map(subject => {
      const mostDiff = subject.most_difficult_unit;
      return `
      <div class="card" style="margin-bottom:1.5rem">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:1rem;flex-wrap:wrap;gap:0.5rem">
          <div>
            <h4 style="margin:0">${subject.subject_name}</h4>
            <span style="font-size:0.8rem;color:var(--text-muted)">${subject.total_marks} mark record(s)</span>
          </div>
          ${mostDiff && mostDiff.low > 0 ? `
            <div style="background:rgba(239,68,68,0.1);border:1px solid var(--danger);border-radius:8px;padding:0.4rem 0.85rem;font-size:0.8rem">
              🔴 Most difficult: <strong>Unit ${mostDiff.unit_number} — ${mostDiff.unit_title}</strong>
              (${mostDiff.low} low-performer${mostDiff.low !== 1 ? 's' : ''})
            </div>
          ` : ''}
        </div>

        <!-- Unit heatmap grid -->
        <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:0.6rem">
          ${subject.units.map(u => {
            const total = u.low + u.medium + u.high || 1;
            const lowPct  = Math.round((u.low  / total) * 100);
            const medPct  = Math.round((u.medium / total) * 100);
            const highPct = Math.round((u.high / total) * 100);
            const heatColor = u.low > u.high
              ? `rgba(239,68,68,${0.15 + (u.low/total)*0.4})`
              : `rgba(16,185,129,${0.15 + (u.high/total)*0.4})`;
            return `
              <div style="background:${heatColor};border-radius:10px;padding:0.75rem;text-align:center">
                <div style="font-weight:700;font-size:0.85rem;margin-bottom:0.5rem">Unit ${u.unit_number}</div>
                <div style="font-size:0.72rem;color:var(--text-secondary);margin-bottom:0.25rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${u.unit_title}">${u.unit_title}</div>
                <div style="margin-top:0.5rem;display:flex;flex-direction:column;gap:2px;font-size:0.72rem">
                  <div style="display:flex;justify-content:space-between"><span style="color:var(--danger)">Low</span><strong>${u.low}</strong></div>
                  <div style="display:flex;justify-content:space-between"><span style="color:var(--warning)">Med</span><strong>${u.medium}</strong></div>
                  <div style="display:flex;justify-content:space-between"><span style="color:var(--success)">High</span><strong>${u.high}</strong></div>
                </div>
                ${u.low_students.length ? `
                  <div style="margin-top:0.5rem;font-size:0.68rem;color:var(--danger)" title="${u.low_students.join(', ')}">
                    ⚠️ ${u.low_students.slice(0,2).join(', ')}${u.low_students.length > 2 ? ` +${u.low_students.length-2}` : ''}
                  </div>` : ''}
              </div>
            `;
          }).join('')}
        </div>
        <div style="display:flex;gap:1rem;margin-top:0.75rem;font-size:0.75rem;color:var(--text-muted)">
          <span>🔴 Low: marks &lt;50</span>
          <span>🟡 Medium: 50–74</span>
          <span>🟢 High: ≥75</span>
          <span style="margin-left:auto">Darker red = more students need help in that unit</span>
        </div>
      </div>
    `}).join('');
  } catch (err) {
    container.innerHTML = `<div class="card" style="color:var(--danger);padding:1.5rem">❌ ${err.message}</div>`;
  }
}
