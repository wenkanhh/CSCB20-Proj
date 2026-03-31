# Frontend Requirements Labeled

This is a separate frontend starter that matches your checklist:

- Layout: `base.html` + navbar
- Auth Pages: `login.html`, `register.html`
- User Pages: `profile.html`
- Course Pages: `courses.html`, `course-details.html`
- Recommendation UI: `recommendations.html`, `dashboard.html`

## How to use

1. Put these files inside your `Frontend` folder.
2. Start your Flask backend on `http://127.0.0.1:5000`.
3. Open `login.html` or `dashboard.html` with Live Server or in your browser.
4. All requests go to `/api/...` on the Flask backend.

## Main frontend files

- `base.html` = shared layout example
- `css/styles.css` = all page styling
- `js/api.js` = fetch helpers and API calls
- `js/common.js` = navbar, alerts, cards, and page helpers

## Important note

`base.html` is included because your checklist asked for it. In plain static HTML, other pages cannot truly "extend" it the way Jinja does. So the pages use the same shared structure, CSS, and JS. If you later move this into Flask templates, those pages can extend `base.html` properly.
