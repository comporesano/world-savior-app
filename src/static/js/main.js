/** Точка входа SPA. */

import { auth } from './auth.js';
import { navigate } from './router.js';
import { initTheme } from './utils.js';

initTheme();

(async () => {
  await auth.init();
  window.addEventListener('hashchange', navigate);
  await navigate();
})();
