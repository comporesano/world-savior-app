/** Переиспользуемые UI-компоненты (генерация HTML + обработчики). */

import { auth } from './auth.js';
import { esc, fmtDateTime, fmtDate, fmtNum, initials, plural, typeMeta, levelForPoints, rankTitle, levelProgress } from './utils.js';

export function navbarHTML() {
  const links = [
    ['#/', 'Главная'],
    ['#/events', 'События'],
    ['#/leaderboard', 'Рейтинг'],
  ];
  const current = (location.hash || '#/').split('?')[0];
  const navLinks = links
    .map(([href, label]) => {
      const active = current === href || (href === '#/events' && current.startsWith('#/events'));
      return `<a class="nav-link${active ? ' active' : ''}" href="${href}">${label}</a>`;
    })
    .join('');

  let right = '';
  if (auth.user) {
    right = `
      <div class="nav-user">
        <a class="btn btn-outline btn-sm" href="#/events/new">＋ Создать</a>
        <span class="nav-points" title="Эко-баллы">🍀 ${esc(fmtNum(auth.user.points))}</span>
        <a href="#/profile" class="avatar" style="width:32px;height:32px;font-size:0.78rem" title="Профиль">${esc(initials(auth.user.name))}</a>
      </div>`;
  } else {
    right = `
      <div class="nav-user">
        <a class="btn btn-ghost btn-sm" href="#/login">Войти</a>
        <a class="btn btn-primary btn-sm" href="#/register">Регистрация</a>
      </div>`;
  }

  return `
    <nav class="navbar">
      <div class="navbar-inner">
        <a class="brand" href="#/">
          <span class="brand-mark">🌍</span>
          <span>EcoSavior</span>
        </a>
        <div class="nav-links">${navLinks}</div>
        <button class="icon-btn" id="theme-toggle" title="Переключить тему" aria-label="Переключить тему">${document.documentElement.dataset.theme === 'dark' ? '☀️' : '🌙'}</button>
        ${right}
      </div>
    </nav>`;
}

export function footerHTML() {
  return `
    <footer class="footer">
      <div class="footer-inner">
        <span>🌍 EcoSavior — платформа экологических инициатив</span>
        <span>FastAPI · SQLite · vanilla JS SPA</span>
      </div>
    </footer>`;
}

export function chipHTML(type) {
  const meta = typeMeta(type);
  return `<span class="chip" style="--type-color: var(${meta.colorVar})"><span class="chip-dot"></span>${meta.icon} ${esc(meta.label)}</span>`;
}

export function statusBadgeHTML(status) {
  if (status === 'confirmed') return '<span class="badge badge-good">✓ Подтверждено</span>';
  return '<span class="badge badge-warn">⏳ Запись ожидает подтверждения</span>';
}

export function avatarHTML(name, cls = '') {
  return `<span class="avatar ${cls}">${esc(initials(name))}</span>`;
}

export function eventCardHTML(event) {
  const start = new Date(event.startsAt);
  const month = start.toLocaleDateString('ru-RU', { month: 'short' }).replace('.', '');
  const day = start.getDate();
  const seats = event.capacity > 0
    ? `${event.participantsCount} из ${event.capacity} мест`
    : `${event.participantsCount} ${plural(event.participantsCount, 'участник', 'участника', 'участников')}`;
  const finished = new Date(event.endsAt ?? event.startsAt) < new Date();

  return `
    <a class="card card-hover event-card" href="#/events/${event.id}">
      <div class="event-card-head">
        <div class="event-date-block">
          <span class="event-date"><span class="d">${day}</span><span class="m">${esc(month)}</span></span>
          <div>
            <h3 class="event-title">${esc(event.title)}</h3>
          </div>
        </div>
        ${chipHTML(event.type)}
      </div>
      <p class="event-desc">${esc(event.description)}</p>
      <div class="event-meta">
        <span class="event-meta-row">🗓 ${esc(fmtDateTime(event.startsAt))}</span>
        <span class="event-meta-row">📍 ${esc(event.location)}</span>
      </div>
      <div class="event-card-foot">
        <span class="event-meta-row muted small">👥 ${esc(seats)}</span>
        <span class="badge badge-neutral">🍀 +${event.pointsReward} баллов</span>
        ${finished ? '<span class="badge badge-critical">Завершено</span>' : ''}
      </div>
    </a>`;
}

export function statTileHTML(icon, label, value) {
  return `
    <div class="stat-tile">
      <div class="stat-icon" aria-hidden="true">${icon}</div>
      <div class="stat-value">${esc(fmtNum(value))}</div>
      <div class="stat-label">${esc(label)}</div>
    </div>`;
}

/**
 * Рейтинговые горизонтальные бары (один оттенок, сравнение величин).
 * rows: [{ label, icon, value }] — сортируются по убыванию.
 */
export function barsChartHTML(rows) {
  const sorted = [...rows].sort((a, b) => b.value - a.value);
  const max = Math.max(1, ...sorted.map((r) => r.value));
  const bars = sorted
    .map((r) => {
      const width = Math.max(4, Math.round((r.value / max) * 100));
      return `
        <div class="bar-row" data-tip="${esc(r.label)}: ${esc(r.value)} ${esc(plural(r.value, 'мероприятие', 'мероприятия', 'мероприятий'))}">
          <span class="bar-label">${r.icon} ${esc(r.label)}</span>
          <span class="bar-track"><span class="bar-fill" style="width:${width}%"></span></span>
          <span class="bar-value">${esc(r.value)}</span>
        </div>`;
    })
    .join('');
  return `<div class="bars-chart">${bars}</div>`;
}

/** Делегированный тултип для баров: категория + значение. */
export function attachChartTooltip(container) {
  const tip = document.createElement('div');
  tip.className = 'chart-tip';
  tip.setAttribute('role', 'tooltip');
  document.body.appendChild(tip);

  container.addEventListener('mouseover', (e) => {
    const row = e.target.closest('[data-tip]');
    if (!row) return;
    tip.textContent = row.dataset.tip ?? '';
    tip.classList.add('visible');
  });
  container.addEventListener('mousemove', (e) => {
    const row = e.target.closest('[data-tip]');
    if (!row) return;
    tip.style.left = `${Math.min(e.clientX + 14, window.innerWidth - 240)}px`;
    tip.style.top = `${e.clientY + 14}px`;
  });
  container.addEventListener('mouseout', (e) => {
    if (e.target.closest('[data-tip]')) tip.classList.remove('visible');
  });
}

/** Метр: одно отношение к лимиту (заполненность, прогресс уровня). */
export function meterHTML(ratio, metaText, severity = '') {
  const pct = Math.min(100, Math.max(0, Math.round(ratio * 100)));
  return `
    <div class="meter">
      <div class="meter-track"><div class="meter-fill ${severity}" style="width:${pct}%"></div></div>
      <div class="meter-meta"><span>${metaText}</span><span class="tnum">${pct}%</span></div>
    </div>`;
}

export function paginationHTML(meta, basePath) {
  if (meta.totalPages <= 1) return '';
  const parts = [];
  const pageHref = (p) => `${basePath}&page=${p}`;
  if (meta.page > 1) parts.push(`<a class="btn btn-outline btn-sm" href="${pageHref(meta.page - 1)}">← Назад</a>`);
  parts.push(`<span>Стр. ${meta.page} из ${meta.totalPages}</span>`);
  if (meta.page < meta.totalPages) parts.push(`<a class="btn btn-outline btn-sm" href="${pageHref(meta.page + 1)}">Вперёд →</a>`);
  return `<div class="pagination">${parts.join('')}</div>`;
}

export function emptyHTML(icon, title, text) {
  return `
    <div class="empty">
      <span class="empty-icon">${icon}</span>
      <h3>${esc(title)}</h3>
      <p>${esc(text)}</p>
    </div>`;
}

export function spinnerHTML() {
  return '<div class="spinner" role="status" aria-label="Загрузка…"></div>';
}

export function errorBoxHTML(err) {
  return `<div class="error-box">⚠️ ${esc(err.message || 'Что-то пошло не так')}</div>`;
}

export function levelChipHTML(points) {
  const level = levelForPoints(points);
  return `<span class="badge badge-neutral" title="${esc(rankTitle(level))}">Ур. ${level} · ${esc(rankTitle(level))}</span>`;
}

/** Прогресс до следующего уровня. */
export function levelMeterHTML(points) {
  const lp = levelProgress(points);
  const left = Math.max(0, lp.nextLevelAt - lp.current);
  return meterHTML(lp.progress, `До уровня ${lp.level + 1}: ещё ${left} ${plural(left, 'балл', 'балла', 'баллов')}`);
}
