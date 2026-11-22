/** Страница 404. */

import { emptyHTML } from '../components.js';

export function notFoundView() {
  return {
    html: `
      <div class="page-head"></div>
      ${emptyHTML('🧭', 'Страница не найдена', 'Такого маршрута нет. Вернитесь на главную или к списку событий.')}
      <div style="text-align:center">
        <a class="btn btn-primary" href="#/">На главную</a>
      </div>`,
  };
}
