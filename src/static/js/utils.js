/** Вспомогательные функции: экранирование, форматирование, уровни. */

/** Экранирование HTML — ОБЯЗАТЕЛЬНО для любых данных из API */
export function esc(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

export function fmtDate(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' });
}

export function fmtDateTime(iso) {
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric' })
    + ', ' + new Date(iso).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

export function fmtTime(iso) {
  return new Date(iso).toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
}

export function daysUntil(iso) {
  const now = new Date();
  const target = new Date(iso);
  const startOfDay = (d) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const diffDays = Math.round((startOfDay(target) - startOfDay(now)) / 86_400_000);
  if (diffDays <= -1) return `завершилось ${fmtDate(iso)}`;
  if (diffDays === 0) return 'сегодня';
  if (diffDays === 1) return 'завтра';
  return `через ${diffDays} ${plural(diffDays, 'день', 'дня', 'дней')}`;
}

export function plural(n, one, few, many) {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return few;
  return many;
}

export function initials(name) {
  return String(name || '?')
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? '')
    .join('');
}

/** Автокомпакт чисел для KPI-тайлов: 1 284 / 12.9K */
export function fmtNum(n) {
  const num = Number(n);
  if (!Number.isFinite(num)) return String(n);
  if (Math.abs(num) >= 1_000_000) return `${(num / 1_000_000).toFixed(1).replace('.0', '')}M`;
  if (Math.abs(num) >= 10_000) return `${(num / 1000).toFixed(1).replace('.0', '')}K`;
  return num.toLocaleString('ru-RU');
}

/* ---------- Уровни (зеркало src/levels.py) ---------- */

export function levelForPoints(points) {
  return 1 + Math.floor(Math.sqrt(Math.max(0, points) / 100));
}

export function rankTitle(level) {
  if (level >= 6) return 'Хранитель планеты';
  if (level >= 4) return 'Эко-боец';
  if (level >= 2) return 'Активист';
  return 'Новичок';
}

export function levelProgress(points) {
  const level = levelForPoints(points);
  const prev = (level - 1) ** 2 * 100;
  const next = level ** 2 * 100;
  const span = next - prev;
  return { level, current: points, nextLevelAt: next, progress: span === 0 ? 1 : Math.min(1, (points - prev) / span) };
}

/* ---------- Метаданные типов событий ----------
   Цвета — валидированная категориальная палитра (см. tokens.css);
   идентичность никогда не передаётся одним цветом: всегда иконка + подпись. */

export const EVENT_TYPES = {
  cleanup:       { label: 'Субботник',        icon: '🧹', colorVar: '--type-cleanup' },
  tree_planting: { label: 'Посадка деревьев', icon: '🌳', colorVar: '--type-tree_planting' },
  recycling:     { label: 'Сбор вторсырья',   icon: '♻️', colorVar: '--type-recycling' },
  eco_lecture:   { label: 'Эко-лекция',       icon: '🎓', colorVar: '--type-eco_lecture' },
  water_cleanup: { label: 'Очистка водоёмов', icon: '💧', colorVar: '--type-water_cleanup' },
};

export function typeMeta(type) {
  return EVENT_TYPES[type] ?? { label: type, icon: '🌱', colorVar: '--type-cleanup' };
}

/* ---------- Тема ---------- */

const THEME_KEY = 'ecosavior.theme';

export function initTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  const theme = saved ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.dataset.theme = theme;
}

export function toggleTheme() {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  localStorage.setItem(THEME_KEY, next);
}
