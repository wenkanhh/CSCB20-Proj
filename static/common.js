// Find the first element that matches a CSS selector
function $(selector) {
  return document.querySelector(selector);
}

// Get a value from the page URL, for example ?code=MGTA01H3
function getQueryParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

// Change special characters into safe HTML text
// This helps stop broken HTML if text contains symbols like < or >
function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

// Show a message box inside a target element
// type can be: info, success, error, warning
function showAlert(target, type, message) {
  if (!target) return;

  target.innerHTML = `<div class="alert ${type}">${escapeHtml(message)}</div>`;
}

// Clear the message box
function clearAlert(target) {
  if (!target) return;
  target.innerHTML = '';
}

// Turn JavaScript data into pretty text
// Useful when debugging in the browser console or on a page
function prettyJson(data) {
  return JSON.stringify(data, null, 2);
}