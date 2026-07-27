// ============================================================
// js/api.js - Central API client for all backend calls
// ============================================================

const API_BASE = '/api';

// ── Token management ──────────────────────────────────────────────────────────
const Auth = {
  getToken: () => localStorage.getItem('token'),
  getUser:  () => JSON.parse(localStorage.getItem('user') || 'null'),
  setSession: (token, user) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
  },
  clear: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  },
  isLoggedIn: () => !!localStorage.getItem('token'),
  getRole: () => {
    const u = Auth.getUser();
    return u ? u.role : null;
  },
};

// ── HTTP helpers ──────────────────────────────────────────────────────────────
async function apiRequest(method, endpoint, body = null, isFormData = false) {
  const headers = {};
  const token = Auth.getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!isFormData && body) headers['Content-Type'] = 'application/json';

  const options = { method, headers };
  if (body) options.body = isFormData ? body : JSON.stringify(body);

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, options);
    const data = await res.json().catch(() => ({}));

    if (res.status === 401) {
      Auth.clear();
      window.location.href = '/';
      return;
    }

    if (!res.ok) {
      throw new Error(data.error || `Request failed (${res.status})`);
    }

    return data;
  } catch (err) {
    if (err.name === 'TypeError') throw new Error('Network error — is the server running?');
    throw err;
  }
}

const api = {
  get:    (ep)          => apiRequest('GET', ep),
  post:   (ep, body)    => apiRequest('POST', ep, body),
  put:    (ep, body)    => apiRequest('PUT', ep, body),
  delete: (ep)          => apiRequest('DELETE', ep),
  postForm: (ep, fd)    => apiRequest('POST', ep, fd, true),
  putForm:  (ep, fd)    => apiRequest('PUT',  ep, fd, true),

  // ── Auth ──────────────────────────────────────────────────────────────────
  login:    (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  me:       ()     => api.get('/auth/me'),

  // ── Student ───────────────────────────────────────────────────────────────
  student: {
    profile:       ()           => api.get('/student/profile'),
    updateProfile: (d)          => api.put('/student/profile', d),
    marks:         ()           => api.get('/student/marks'),
    addMark:       (d)          => api.post('/student/marks', d),
    performance:   ()           => api.get('/student/performance'),
    predict:       ()           => api.post('/student/predict', {}),
    assignments:   ()           => api.get('/student/assignments'),
    submit:        (id, fd)     => api.postForm(`/student/assignments/${id}/submit`, fd),
    notifications: ()           => api.get('/student/notifications'),
    markRead:      ()           => api.put('/student/notifications/read-all', {}),
    reportPdf:     ()           => `${API_BASE}/student/report/pdf`,
  },

  // ── Teacher ───────────────────────────────────────────────────────────────
  teacher: {
    students:         (dept)    => api.get(`/teacher/students${dept ? '?department='+dept : ''}`),
    studentDetail:    (id)      => api.get(`/teacher/students/${id}`),
    enterMarks:       (id, d)   => api.post(`/teacher/students/${id}/marks`, d),
    subjects:         (dept)    => api.get(`/teacher/subjects${dept ? '?department='+dept : ''}`),
    addSubject:       (d)       => api.post('/teacher/subjects', d),
    assignments:      ()        => api.get('/teacher/assignments'),
    createAssignment: (fd)      => api.postForm('/teacher/assignments', fd),
    updateAssignment: (id, d)   => api.put(`/teacher/assignments/${id}`, d),
    deleteAssignment: (id)      => api.delete(`/teacher/assignments/${id}`),
    submissions:      (id)      => api.get(`/teacher/assignments/${id}/submissions`),
    reviewSubmission: (id, d)   => api.put(`/teacher/submissions/${id}/review`, d),
    downloadFile:     (id)      => `${API_BASE}/teacher/assignments/${id}/download`,
  },

  // ── HOD ───────────────────────────────────────────────────────────────────
  hod: {
    overview:         (dept)    => api.get(`/hod/overview${dept ? '?department='+dept : ''}`),
    students:         (params)  => api.get('/hod/students?' + new URLSearchParams(params).toString()),
    studentFull:      (id)      => api.get(`/hod/students/${id}`),
    atRisk:           (dept)    => api.get(`/hod/at-risk${dept ? '?department='+dept : ''}`),
    topPerformers:    (dept)    => api.get(`/hod/top-performers${dept ? '?department='+dept : ''}`),
    deptAnalytics:    ()        => api.get('/hod/analytics/department'),
    subjectAnalytics: (dept)    => api.get(`/hod/analytics/subjects${dept ? '?department='+dept : ''}`),
    trends:           ()        => api.get('/hod/analytics/trends'),
    assignments:      ()        => api.get('/hod/assignments'),
    teachers:         (dept)    => api.get(`/hod/teachers${dept ? '?department='+dept : ''}`),
  },

  // ── Syllabus ──────────────────────────────────────────────────────────────
  syllabus: {
    subjects:        (dept)         => api.get(`/syllabus/subjects${dept ? '?department='+dept : ''}`),
    get:             (subjectId)    => api.get(`/syllabus/${subjectId}`),
    save:            (subjectId, d) => api.post(`/syllabus/${subjectId}`, d),
    recommendations: ()             => api.get('/syllabus/recommendations'),
    weakAreas:       (dept)         => api.get(`/syllabus/teacher/weak-areas${dept ? '?department='+dept : ''}`),
    unitAnalysis:    (dept)         => api.get(`/syllabus/hod/unit-analysis${dept ? '?department='+dept : ''}`),
  },
};

