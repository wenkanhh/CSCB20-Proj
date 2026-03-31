const DEFAULT_API_BASE = 'http://127.0.0.1:5000/api';

function getApiBase() {
  return localStorage.getItem('apiBase') || DEFAULT_API_BASE;
}

function setApiBase(value) {
  localStorage.setItem('apiBase', value);
}

async function apiFetch(path, options = {}) {
  const url = `${getApiBase()}${path}`;
  const response = await fetch(url, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = null;
  try {
    data = await response.json();
  } catch (_) {
    data = null;
  }

  if (!response.ok) {
    const message = data?.error || data?.detail || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}

const AuthAPI = {
  register(payload) {
    return apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(payload) });
  },
  login(payload) {
    return apiFetch('/auth/login', { method: 'POST', body: JSON.stringify(payload) });
  },
  logout() {
    return apiFetch('/auth/logout', { method: 'POST' });
  },
  session() {
    return apiFetch('/auth/session');
  },
};

const UserAPI = {
  profile() {
    return apiFetch('/me/profile');
  },
  updateProfile(payload) {
    return apiFetch('/me/profile', { method: 'PUT', body: JSON.stringify(payload) });
  },
  programs() {
    return apiFetch('/me/programs');
  },
  addProgram(payload) {
    return apiFetch('/me/programs', { method: 'POST', body: JSON.stringify(payload) });
  },
  completedCourses() {
    return apiFetch('/me/completed-courses');
  },
  addCompletedCourse(payload) {
    return apiFetch('/me/completed-courses', { method: 'POST', body: JSON.stringify(payload) });
  },
};

const CourseAPI = {
  listCourses({ search = '', prefix = '', limit = 200 } = {}) {
    const params = new URLSearchParams({ search, prefix, limit });
    return apiFetch(`/courses?${params.toString()}`);
  },
  getCourse(code) {
    return apiFetch(`/courses/${encodeURIComponent(code)}`);
  },
  getOfferings(code) {
    return apiFetch(`/courses/${encodeURIComponent(code)}/offerings`);
  },
  listPrograms({ search = '', type = '' } = {}) {
    const params = new URLSearchParams({ search, type });
    return apiFetch(`/programs?${params.toString()}`);
  },
  getProgram(code) {
    return apiFetch(`/programs/${encodeURIComponent(code)}`);
  },
};

const PlannerAPI = {
  eligibility(code) {
    return apiFetch(`/me/eligibility/${encodeURIComponent(code)}`);
  },
  recommendations({ programCode = '', limit = 20 } = {}) {
    const params = new URLSearchParams();
    if (programCode) params.set('program_code', programCode);
    params.set('limit', limit);
    return apiFetch(`/me/recommendations?${params.toString()}`);
  },
  dashboard({ programCode = '' } = {}) {
    const params = new URLSearchParams();
    if (programCode) params.set('program_code', programCode);
    return apiFetch(`/me/planner-dashboard?${params.toString()}`);
  },
  degreeAudit(programCode) {
    return apiFetch(`/me/degree-audit/${encodeURIComponent(programCode)}`);
  },
  saveRecommendation(payload) {
    return apiFetch('/me/saved-recommendations', { method: 'POST', body: JSON.stringify(payload) });
  },
  savedRecommendations() {
    return apiFetch('/me/saved-recommendations');
  },
};
