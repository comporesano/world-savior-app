/** Список событий: фильтры (тип, поиск, период) + пагинация. */

import { api } from '../api.js';
import { emptyHTML, errorBoxHTML, eventCardHTML, paginationHTML } from '../components.js';
import { esc, EVENT_TYPES } from '../utils.js';

export async function eventsView({ query }) {
  const state = {
    type: query.get('type') ?? '',
    q: query.get('q') ?? '',
    scope: query.get('scope') ?? 'upcoming',
    page: Math.max(1, Number(query.get('page') ?? 1)),
  };

  const params = new URLSearchParams({ scope: state.scope, page: String(state.page), limit: '12' });
  if (state.type) params.set('type', state.type);
  if (state.q) params.set('q', state.q);

  try {
    const data = await api(`/events?${params}`);

    const typeOptions = Object.entries(EVENT_TYPES)
      .map(([value, meta]) => `<option value="${value}"${state.type === value ? ' selected' : ''}>${meta.icon} ${esc(meta.label)}</option>`)
      .join('');

    const scopes = [
      ['upcoming', 'Предстоящие'],
      ['past', 'Прошедшие'],
      ['all', 'Все'],
    ];

    const basePath = `#/events?scope=${state.scope}&type=${encodeURIComponent(state.type)}&q=${encodeURIComponent(state.q)}`;

    const cards = data.items.length
      ? `<div class="events-grid">${data.items.map(eventCardHTML).join('')}</div>`
      : emptyHTML('🔍', 'Ничего не найдено', 'Попробуйте изменить фильтры или создать своё событие.');

    return {
      html: `
        <div class="page-head">
          <div>
            <h1 class="page-title">События</h1>
            <p class="page-sub">${data.meta.total} ${esc(pluralRu(data.meta.total))}</p>
          </div>
          <a class="btn btn-primary" href="#/events/new">＋ Создать событие</a>
        </div>

        <form class="filters" id="filters">
          <div class="seg" id="scope-seg">
            ${scopes.map(([value, label]) => `<button type="button" data-scope="${value}" class="${state.scope === value ? 'active' : ''}">${label}</button>`).join('')}
          </div>
          <select class="filter-input" id="type-filter" aria-label="Тип события">
            <option value="">Все типы</option>
            ${typeOptions}
          </select>
          <input class="filter-input" id="q-filter" type="search" placeholder="Поиск: название или место…" value="${esc(state.q)}" aria-label="Поиск"/>
        </form>

        ${cards}
        ${paginationHTML(data.meta, basePath)}`,
      mount(el) {
        const apply = (patch) => {
          const next = { ...state, ...patch };
          if (!patch.type && patch.type !== '') next.page = 1;
          const p = new URLSearchParams({ scope: next.scope, page: String(next.page) });
          if (next.type) p.set('type', next.type);
          if (next.q) p.set('q', next.q);
          location.hash = `#/events?${p}`;
        };

        el.querySelector('#scope-seg').addEventListener('click', (e) => {
          const btn = e.target.closest('[data-scope]');
          if (btn) apply({ scope: btn.dataset.scope, page: 1 });
        });
        el.querySelector('#type-filter').addEventListener('change', (e) => apply({ type: e.target.value, page: 1 }));
        el.querySelector('#q-filter').addEventListener('change', (e) => apply({ q: e.target.value.trim(), page: 1 }));
      },
    };
  } catch (err) {
    return { html: errorBoxHTML(err) };
  }
}

function pluralRu(total) {
  const mod10 = total % 10;
  const mod100 = total % 100;
  if (mod10 === 1 && mod100 !== 11) return 'событие';
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 12 || mod100 > 14)) return 'события';
  return 'событий';
}
