// ============================================================
// js/utils.js - Shared utility functions (toast, formatters, etc.)
// ============================================================

// ── Toast notifications ────────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container') || createToastContainer();
  const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <span style="font-size:1.1rem;flex-shrink:0">${icons[type] || 'ℹ️'}</span>
    <div style="flex:1">
      <div style="font-weight:600;font-size:0.88rem;color:var(--text-primary)">${message}</div>
    </div>
    <button onclick="this.parentElement.remove()" style="background:none;border:none;color:var(--text-muted);cursor:pointer;font-size:1rem;padding:0 4px">×</button>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOut 0.3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

function createToastContainer() {
  const c = document.createElement('div');
  c.id = 'toast-container';
  document.body.appendChild(c);
  return c;
}

// ── Loading state ──────────────────────────────────────────────────────────────
function setLoading(btn, loading, text = null) {
  if (!btn) return;
  if (loading) {
    btn._origText = btn.innerHTML;
    btn.innerHTML = `<span class="spinner"></span> ${text || 'Loading...'}`;
    btn.disabled = true;
  } else {
    btn.innerHTML = btn._origText || text || 'Submit';
    btn.disabled = false;
  }
}

// ── Date formatters ────────────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric'
  });
}

function formatDateTime(dateStr) {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit'
  });
}

function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60) return 'Just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
  return `${Math.floor(diff/86400)}d ago`;
}

function isPastDeadline(dateStr) {
  return dateStr && new Date(dateStr) < new Date();
}

// ── Grade badge ────────────────────────────────────────────────────────────────
function gradeBadge(grade) {
  const map = { A: 'success', B: 'info', C: 'warning', Fail: 'danger' };
  return `<span class="badge badge-${map[grade] || 'info'}">${grade}</span>`;
}

function riskBadge(risk) {
  const map = { Low: 'success', Medium: 'warning', High: 'danger' };
  return `<span class="badge badge-${map[risk] || 'info'}">${risk}</span>`;
}

function submissionBadge(status) {
  const map = { submitted: 'info', reviewed: 'warning', graded: 'success' };
  return `<span class="badge badge-${map[status] || 'info'}">${status}</span>`;
}

// ── Progress bar ───────────────────────────────────────────────────────────────
function progressBar(value, max = 100, color = null) {
  const pct = Math.min(100, Math.max(0, (value / max) * 100));
  let barColor = color;
  if (!barColor) {
    if (pct >= 75) barColor = 'var(--success)';
    else if (pct >= 50) barColor = 'var(--warning)';
    else barColor = 'var(--danger)';
  }
  return `
    <div class="progress">
      <div class="progress-bar" style="width:${pct}%;background:${barColor}"></div>
    </div>`;
}

// ── Empty state ────────────────────────────────────────────────────────────────
function emptyState(icon, message) {
  return `<div class="empty-state">
    <div class="empty-state-icon">${icon}</div>
    <p>${message}</p>
  </div>`;
}

// ── Navigate between sections ──────────────────────────────────────────────────
function activateSection(sectionId) {
  document.querySelectorAll('.page-section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const section = document.getElementById(sectionId);
  if (section) section.classList.add('active');

  const navItem = document.querySelector(`[data-section="${sectionId}"]`);
  if (navItem) navItem.classList.add('active');

  // Close mobile sidebar
  document.querySelector('.sidebar')?.classList.remove('open');
}

// ── Modal helpers ──────────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.remove('hidden');
}

function closeModal(id) {
  document.getElementById(id)?.classList.add('hidden');
}

// ── Confirm dialog ────────────────────────────────────────────────────────────
function confirmAction(message, callback) {
  if (confirm(message)) callback();
}

// ── Number formatting ──────────────────────────────────────────────────────────
function fmtNum(n, dec = 1) {
  return parseFloat(n || 0).toFixed(dec);
}

function pct(val) { return `${fmtNum(val)}%`; }

// ── Marks color ────────────────────────────────────────────────────────────────
function marksColor(marks) {
  if (marks >= 75) return 'var(--success)';
  if (marks >= 50) return 'var(--warning)';
  return 'var(--danger)';
}

function marksLabel(marks) {
  if (marks > 75) return '⭐ Strong';
  if (marks < 50) return '⚠️ Weak';
  return '→ Average';
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
  Auth.clear();
  window.location.href = '/';
}

// ── Redirect if not logged in ──────────────────────────────────────────────────
function requireAuth(expectedRole = null) {
  if (!Auth.isLoggedIn()) {
    window.location.href = '/';
    return false;
  }
  if (expectedRole && Auth.getRole() !== expectedRole) {
    showToast('Access denied', 'error');
    logout();
    return false;
  }
  return true;
}

// ── Update sidebar user info ───────────────────────────────────────────────────
function populateSidebarUser() {
  const user = Auth.getUser();
  if (!user) return;
  const nameEl = document.getElementById('sidebar-user-name');
  const roleEl = document.getElementById('sidebar-user-role');
  if (nameEl) nameEl.textContent = user.name;
  if (roleEl) roleEl.textContent = user.role.toUpperCase();
}

// ── Chart.js default config ────────────────────────────────────────────────────
function chartDefaults() {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = '#94a3b8';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
}
