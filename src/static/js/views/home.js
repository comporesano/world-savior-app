/** Главная: hero, KPI-тайлы, распределение событий по типам, ближайшие события. */

import { api } from '../api.js';
import { auth } from '../auth.js';
import {
  attachChartTooltip, barsChartHTML, emptyHTML, errorBoxHTML, eventCardHTML, spinnerHTML, statTileHTML,
} from '../components.js';
import { esc, typeMeta, EVENT_TYPES } from '../utils.js';

export async function homeView() {
  try {
    const [stats, upcoming] = await Promise.all([
      api('/stats'),
      api('/events?scope=upcoming&limit=3'),
    ]);

    const chartRows = Object.entries(EVENT_TYPES).map(([type, meta]) => ({
      label: meta.label,
      icon: meta.icon,
      value: stats.eventsByType[type] ?? 0,
    }));

    const cta = auth.user
      ? '<a class="btn btn-white" href="#/events/new">＋ Создать событие</a><a class="btn btn-ghost-light" href="#/events">Найти событие</a>'
      : '<a class="btn btn-white" href="#/register">Присоединиться</a><a class="btn btn-ghost-light" href="#/events">Смотреть события</a>';

    const upcomingCards = upcoming.items.length
      ? upcoming.items.map(eventCardHTML).join('')
      : emptyHTML('🍃', 'Событий пока нет', 'Станьте первым организатором — создайте своё событие!');

    return {
      html: `
        <section class="hero">
          <span class="hero-badge">🌱 Экология — это командная работа</span>
          <h1>Меняем мир к лучшему — одно событие за раз</h1>
          <p>EcoSavior объединяет волонтёров и организаторов: субботники, посадки деревьев, сбор вторсырья и эко-лекции. Участвуйте, зарабатывайте эко-баллы и поднимайтесь в рейтинге.</p>
          <div class="hero-actions">${cta}</div>
        </section>

        <section class="stats-row" aria-label="Статистика платформы">
          ${statTileHTML('👥', 'Пользователей', stats.users)}
          ${statTileHTML('🗓', 'Мероприятий', stats.events)}
          ${statTileHTML('🤝', 'Волонтёров', stats.participants)}
          ${statTileHTML('🍀', 'Баллов начислено', stats.pointsAwarded)}
        </section>

        <section class="card bars-card">
          <h2 class="bars-title">Мероприятия по типам</h2>
          <div id="type-bars">${barsChartHTML(chartRows)}</div>
        </section>

        <section>
          <div class="section-title-row">
            <h2>Ближайшие события</h2>
            <a href="#/events">Все события →</a>
          </div>
          <div class="events-grid">${upcomingCards}</div>
        </section>

        <section style="margin-top:40px">
          <h2>Как это работает</h2>
          <div class="steps">
            <div class="step">
              <div class="step-num">1</div>
              <h3>Организуйте</h3>
              <p class="muted">Создайте эко-событие: субботник, посадку деревьев, сбор вторсырья или лекцию — за пару минут.</p>
            </div>
            <div class="step">
              <div class="step-num">2</div>
              <h3>Участвуйте</h3>
              <p class="muted">Запишитесь на событие рядом с домом. Организатор подтвердит ваше участие после мероприятия.</p>
            </div>
            <div class="step">
              <div class="step-num">3</div>
              <h3>Получайте баллы</h3>
              <p class="muted">Каждое подтверждённое участие приносит эко-баллы. Растите в уровнях и соревнуйтесь в рейтинге.</p>
            </div>
          </div>
        </section>`,
      mount(el) {
        attachChartTooltip(el.querySelector('#type-bars'));
      },
    };
  } catch (err) {
    return { html: errorBoxHTML(err) };
  }
}
