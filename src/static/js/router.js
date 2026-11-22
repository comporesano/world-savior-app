/** Хеш-роутер SPA: #/events, #/events/3, #/events?type=cleanup … */

import { auth } from './auth.js';
import { footerHTML, navbarHTML } from './components.js';
import { toggleTheme } from './utils.js';
import { homeView } from './views/home.js';
import { eventsView } from './views/events.js';
import { eventDetailView } from './views/eventDetail.js';
import { eventFormView } from './views/eventForm.js';
import { leaderboardView } from './views/leaderboard.js';
import { profileView } from './views/profile.js';
import { loginView } from './views/login.js';
import { registerView } from './views/register.js';
import { notFoundView } from './views/notFound.js';

const routes = [
  { pattern: /^#\/$/, view: homeView },
  { pattern: /^#\/events\/new$/, view: eventFormView },
  { pattern: /^#\/events\/(\d+)\/edit$/, view: eventFormView },
  { pattern: /^#\/events\/(\d+)$/, view: eventDetailView },
  { pattern: /^#\/events$/, view: eventsView },
  { pattern: /^#\/leaderboard$/, view: leaderboardView },
  { pattern: /^#\/profile$/, view: profileView },
  { pattern: /^#\/login$/, view: loginView },
  { pattern: /^#\/register$/, view: registerView },
];

export async function navigate() {
  const app = document.getElementById('app');
  const hash = location.hash || '#/';
  const [pathPart, queryPart = ''] = hash.split('?');
  const query = new URLSearchParams(queryPart);

  window.scrollTo(0, 0);
  app.innerHTML = navbarHTML() + '<main class="page container"></main>' + footerHTML();
  const main = app.querySelector('main');
  const themeBtn = app.querySelector('#theme-toggle');
  themeBtn?.addEventListener('click', () => {
    toggleTheme();
    themeBtn.textContent = document.documentElement.dataset.theme === 'dark' ? '☀️' : '🌙';
  });

  for (const route of routes) {
    const match = pathPart.match(route.pattern);
    if (match) {
      const view = await route.view({ params: match.slice(1), query });
      main.innerHTML = view.html;
      view.mount?.(main, app);
      return;
    }
  }

  const view = notFoundView();
  main.innerHTML = view.html;
  view.mount?.(main, app);
}

export function go(hash) {
  location.hash = hash;
}
