/** Форма создания/редактирования события. */

import { api } from '../api.js';
import { auth } from '../auth.js';
import { spinnerHTML } from '../components.js';
import { esc, EVENT_TYPES } from '../utils.js';

function toLocalInputValue(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export async function eventFormView({ params }) {
  if (!auth.user) {
    return { html: '<div class="error-box">⚠️ Чтобы создавать события, нужно <a href="#/login">войти</a>.</div>' };
  }

  const editId = params[0] ? Number(params[0]) : null;
  let existing = null;

  if (editId) {
    try {
      existing = (await api(`/events/${editId}`)).event;
      if (!existing.isOwner) {
        return { html: '<div class="error-box">⚠️ Редактировать может только организатор.</div>' };
      }
    } catch (err) {
      return { html: `<div class="error-box">⚠️ ${esc(err.message)}</div>` };
    }
  }

  const typeOptions = Object.entries(EVENT_TYPES)
    .map(([value, meta]) => `<option value="${value}"${existing?.type === value ? ' selected' : ''}>${meta.icon} ${esc(meta.label)}</option>`)
    .join('');

  return {
    html: `
      <div class="page-head">
        <h1 class="page-title">${editId ? 'Редактировать событие' : 'Новое событие'}</h1>
      </div>
      <div class="card" style="max-width:680px">
        <form id="event-form" novalidate>
          <div id="form-errors"></div>
          <div class="field">
            <label for="f-title">Название</label>
            <input id="f-title" type="text" maxlength="120" required minlength="3" value="${esc(existing?.title ?? '')}" placeholder="Например: Субботник в городском парке"/>
          </div>
          <div class="form-row">
            <div class="field">
              <label for="f-type">Тип события</label>
              <select id="f-type">${typeOptions}</select>
            </div>
            <div class="field">
              <label for="f-location">Место проведения</label>
              <input id="f-location" type="text" maxlength="160" required value="${esc(existing?.location ?? '')}" placeholder="Парк, аллея, школа…"/>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label for="f-starts">Начало</label>
              <input id="f-starts" type="datetime-local" required value="${esc(toLocalInputValue(existing?.startsAt))}"/>
            </div>
            <div class="field">
              <label for="f-ends">Окончание (необязательно)</label>
              <input id="f-ends" type="datetime-local" value="${esc(toLocalInputValue(existing?.endsAt))}"/>
            </div>
          </div>
          <div class="form-row">
            <div class="field">
              <label for="f-capacity">Вместимость</label>
              <input id="f-capacity" type="number" min="0" max="10000" value="${existing?.capacity ?? 20}"/>
              <span class="hint">0 — без ограничения</span>
            </div>
            <div class="field">
              <label for="f-points">Баллы за участие</label>
              <input id="f-points" type="number" min="0" max="1000" value="${existing?.pointsReward ?? 10}"/>
              <span class="hint">Начисляются после подтверждения</span>
            </div>
          </div>
          <div class="field">
            <label for="f-desc">Описание</label>
            <textarea id="f-desc" required minlength="10" maxlength="3000" placeholder="Что будем делать, что взять с собой, где встречаемся…">${esc(existing?.description ?? '')}</textarea>
          </div>
          <div style="display:flex;gap:12px">
            <button class="btn btn-primary btn-lg" type="submit">${editId ? 'Сохранить' : 'Создать событие'}</button>
            <a class="btn btn-ghost" href="${editId ? `#/events/${editId}` : '#/events'}">Отмена</a>
          </div>
        </form>
      </div>`,
    mount(el) {
      const form = el.querySelector('#event-form');
      const errorsBox = el.querySelector('#form-errors');

      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorsBox.innerHTML = '';

        const startsAt = new Date(form['f-starts'].value).toISOString();
        const endsRaw = form['f-ends'].value;
        const payload = {
          title: form['f-title'].value.trim(),
          type: form['f-type'].value,
          location: form['f-location'].value.trim(),
          startsAt,
          endsAt: endsRaw ? new Date(endsRaw).toISOString() : null,
          capacity: Number(form['f-capacity'].value) || 0,
          pointsReward: Number(form['f-points'].value) || 0,
          description: form['f-desc'].value.trim(),
        };

        try {
          let targetId = editId;
          if (editId) {
            await api(`/events/${editId}`, { method: 'PATCH', body: payload });
          } else {
            const created = await api('/events', { method: 'POST', body: payload });
            targetId = created.id;
          }
          location.hash = `#/events/${targetId}`;
        } catch (err) {
          const details = (err.details ?? [])
            .map((d) => `<div>· ${esc(d.field)}: ${esc(d.message)}</div>`)
            .join('');
          errorsBox.innerHTML = `<div class="error-box">⚠️ ${esc(err.message)}${details ? `<div style="margin-top:6px;font-weight:500">${details}</div>` : ''}</div>`;
          window.scrollTo(0, 0);
        }
      });
    },
  };
}
