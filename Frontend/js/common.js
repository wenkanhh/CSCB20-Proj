function $(selector) {
  return document.querySelector(selector);
}

function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function showAlert(target, type, message) {
  if (!target) return;
  target.innerHTML = `<div class="alert ${type}">${message}</div>`;
}

function clearAlert(target) {
  if (!target) return;
  target.innerHTML = '';
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderNavbar(active = '') {
  const mount = document.querySelector('[data-navbar]');
  if (!mount) return;

  mount.innerHTML = `
    <header class="site-header">
      <div class="container nav-wrap">
        <a class="brand" href="dashboard.html">Course Planner</a>
        <nav class="navbar">
          <a class="${active === 'dashboard' ? 'active' : ''}" href="dashboard.html">Dashboard</a>
          <a class="${active === 'courses' ? 'active' : ''}" href="courses.html">Courses</a>
          <a class="${active === 'recommendations' ? 'active' : ''}" href="recommendations.html">Recommendations</a>
          <a class="${active === 'profile' ? 'active' : ''}" href="profile.html">Profile</a>
          <a class="${active === 'login' ? 'active' : ''}" href="login.html">Login</a>
          <a class="${active === 'register' ? 'active' : ''}" href="register.html">Register</a>
          <button id="logoutBtn" type="button">Logout</button>
        </nav>
      </div>
    </header>
  `;

  const logoutBtn = $('#logoutBtn');
  logoutBtn?.addEventListener('click', async () => {
    try {
      await AuthAPI.logout();
      window.location.href = 'login.html';
    } catch (error) {
      alert(error.message);
    }
  });
}

function renderFooter() {
  const mount = document.querySelector('[data-footer]');
  if (!mount) return;
  mount.innerHTML = `<footer class="site-footer"><div class="container">Course Planner frontend starter</div></footer>`;
}

function createCourseCard(course, extraHtml = '') {
  const code = course.course_code || 'Unknown Code';
  const name = course.course_name || 'Untitled Course';
  const details = course.course_details || 'No description available.';
  const shortDetails = details.length > 220 ? `${details.slice(0, 220)}...` : details;
  return `
    <article class="course-item">
      <div class="actions" style="justify-content:space-between; align-items:center; margin-top:0;">
        <div>
          <h3 style="margin-bottom:0.35rem;">${escapeHtml(code)} — ${escapeHtml(name)}</h3>
          <div class="meta">Prefix: ${escapeHtml(course.course_code_prefix || course.course_prefix || '')} | Credits: ${escapeHtml(course.credits || '0.5')}</div>
        </div>
        <a class="badge" href="course-details.html?code=${encodeURIComponent(code)}">Open details</a>
      </div>
      <p class="muted">${escapeHtml(shortDetails)}</p>
      ${extraHtml}
    </article>
  `;
}

function createAuditGroupCard(group) {
  const courses = group.courses || [];
  const missing = group.missing_courses || [];
  const taken = group.completed_courses || [];
  const badgeClass = group.satisfied ? 'good' : 'warn';
  return `
    <article class="audit-item">
      <div class="actions" style="justify-content:space-between; align-items:center; margin-top:0;">
        <div>
          <h3 style="margin-bottom:0.35rem;">Requirement Group ${escapeHtml(group.group_id)}</h3>
          <div class="meta">Type: ${escapeHtml(group.group_type || 'ALL')} | Category: ${escapeHtml(group.category || 'Required')}</div>
        </div>
        <span class="badge ${badgeClass}">${group.satisfied ? 'Satisfied' : 'Not yet satisfied'}</span>
      </div>
      <p class="small">Required courses in this block: ${courses.map(c => escapeHtml(c.course_code)).join(', ') || 'None listed'}</p>
      <p class="small">Completed from block: ${taken.map(c => escapeHtml(c)).join(', ') || 'None yet'}</p>
      <p class="small">Missing from block: ${missing.map(c => escapeHtml(c)).join(', ') || 'None'}</p>
    </article>
  `;
}

function prettyJson(data) {
  return JSON.stringify(data, null, 2);
}
