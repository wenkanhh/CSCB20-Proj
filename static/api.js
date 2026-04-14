// Empty string means: use the same website address that opened the page
// Example: if Flask is running on localhost:5000, it will call that same server
const DEFAULT_API_BASE = '';

// Get saved API base from localStorage
function getApiBase() {
  return localStorage.getItem('apiBase') || DEFAULT_API_BASE;
}

// Save API base to localStorage
function setApiBase(value) {
  localStorage.setItem('apiBase', value);
}

// General function for calling backend API routes
async function apiFetch(path, options = {}) {
  const url = `${getApiBase()}${path}`;

  const response = await fetch(url, {
    credentials: 'include', // include Flask session cookie
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
    ...options,
  });

  let data = null;

  // Try to read JSON response
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  // If request failed, show the backend error message if possible
  if (!response.ok) {
    const message = data?.error || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return data;
}

const CourseAPI = {
  getCourse(courseCode) {
    return apiFetch(`/api/course/${encodeURIComponent(courseCode)}`);
  },
};

const PlannerAPI = {
  getPlan(programCode) {
    const params = new URLSearchParams({
      program_code: programCode,
    });

    return apiFetch(`/api/planner?${params.toString()}`);
  },
};