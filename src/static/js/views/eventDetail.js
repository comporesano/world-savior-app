/** Детальная страница события: участие, управление, подтверждение участников. */

import { api } from '../api.js';
import { auth } from '../auth.js';
import { navigate } from '../router.js';
import {
  avatarHTML, chipHTML, errorBoxHTML, meterHTML, spinnerHTML, statusBadgeHTML,
} from '../components.js';
import { esc, fmtDate, fmtDateTime, fmtTime, plural } from '../utils.js';

export async function eventDetailView({ params }) {
  const id = Number(params[0]);
  let event;

  try {
    event = (await api(`/events/${id}`)).event;
  } catch (err) {
    return { html: errorBoxHTML(err) };
  }

  const isUpcoming = !event.isFinished;
  const seats = event.capacity > 0
    ? `${event.participantsCount} из ${event.capacity} мест`
    : `${event.participantsCount} ${plural(event.participantsCount, 'участник', 'участника', 'участников')}`;

  const capacitySeverity = event.capacity > 0 && event.participantsCount >= event.capacity
    ? 'crit'
    : event.capacity > 0 && event.participantsCount / event.capacity >= 0.7
      ? 'warn'
      : '';
  const capacityRatio = event.capacity > 0 ? event.participantsCount / event.capacity : Math.min(1, event.participantsCount / 30);

  const datesHtml = `
    <div class="detail-dates">
      <div>🗓 <strong>${esc(fmtDateTime(event.startsAt))}</strong></div>
      ${event.endsAt ? `<div class="muted">до ${esc(fmtTime(event.endsAt))}</div>` : ''}
    </div>`;

  /* ---------- Боковая панель действий ---------- */

  let actionHtml = '';
  if (!auth.user) {
    actionHtml = `<a class="btn btn-primary btn-block btn-lg" href="#/login">Войти, чтобы участвовать</a>`;
  } else if (event.isOwner) {
    actionHtml = `
      <div class="muted small" style="text-align:center">Вы организатор этого события</div>
      <a class="btn btn-outline btn-block" href="#/events/${id}/edit">✏️ Редактировать</a>
      <button class="btn btn-danger btn-block" id="delete-event">🗑 Удалить событие</button>`;
  } else if (event.isFinished) {
    actionHtml = `<div class="badge badge-critical" style="justify-content:center">Завершено ${esc(fmtDate(event.startsAt))}</div>`;
  } else if (event.joined) {
    actionHtml = `
      <div style="text-align:center">${statusBadgeHTML(participantStatus())}</div>
      <button class="btn btn-outline btn-block" id="leave-event">Отменить запись</button>`;
  } else if (event.isFull) {
    actionHtml = `<button class="btn btn-primary btn-block btn-lg" disabled>Все места заняты</button>`;
  } else {
    actionHtml = `
      <div class="muted small" style="text-align:center">За участие: <strong>🍀 +${event.pointsReward} баллов</strong></div>
      <button class="btn btn-primary btn-block btn-lg" id="join-event">Участвовать</button>`;
  }

  /* ---------- Панель организатора ---------- */

  let ownerPanel = '';
  if (event.isOwner) {
    const rows = event.participants
      .map((p) => `
        <div class="participant-row">
          ${avatarHTML(p.user.name)}
          <div class="p-name">
            <div style="font-weight:700">${esc(p.user.name)}</div>
            <div class="muted small">🍀 ${p.user.points} баллов</div>
          </div>
          ${p.status === 'confirmed'
            ? '<span class="badge badge-good">✓ Подтверждено</span>'
            : `<button class="btn btn-primary btn-sm" data-confirm="${p.user.id}" data-name="${esc(p.user.name)}">Подтвердить</button>`}
        </div>`)
      .join('');

    ownerPanel = `
      <div class="card">
        <h3 style="margin-bottom:4px">Участники (${event.participants.length})</h3>
        <p class="muted small" style="margin-bottom:8px">Подтверждение начисляет участнику ${event.pointsReward} ${plural(event.pointsReward, 'балл', 'балла', 'баллов')}.</p>
        ${rows || '<div class="muted small">Пока никто не записался.</div>'}
      </div>`;
  } else if (event.participants.length > 0) {
    ownerPanel = `
      <div class="card">
        <h3 style="margin-bottom:12px">Участники (${event.participants.length})</h3>
        ${event.participants
          .slice(0, 8)
          .map((p) => `
            <div class="participant-row">
              ${avatarHTML(p.user.name)}
              <div class="p-name" style="font-weight:700">${esc(p.user.name)}</div>
              ${p.status === 'confirmed' ? '<span class="badge badge-good">✓</span>' : '<span class="badge badge-neutral">⏳</span>'}
            </div>`)
          .join('')}
      </div>`;
  }

  function participantStatus() {
    const me = event.participants.find((p) => p.user.id === auth.user?.id);
    return me?.status ?? 'joined';
  }

  return {
    html: `
      <div class="page-head">
        <a href="#/events">← Все события</a>
      </div>
      <div class="detail-layout">
        <div class="detail-main">
          <div class="card">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:12px">
              ${chipHTML(event.type)}
              ${event.isFinished ? '<span class="badge badge-critical">Завершено</span>' : ''}
              <span class="muted small">Организатор: <strong>${esc(event.organizer?.name ?? '—')}</strong></span>
            </div>
            <h1 style="margin-bottom:16px">${esc(event.title)}</h1>
            <div class="event-meta" style="gap:10px;font-size:0.95rem">
              ${datesHtml}
              <div>📍 <strong>${esc(event.location)}</strong></div>
              <div>👥 ${esc(seats)}${event.confirmedCount ? ` · подтверждено: ${event.confirmedCount}` : ''}</div>
            </div>
          </div>

          <div class="card">
            <h3>Описание</h3>
            <p style="white-space:pre-line;margin:0">${esc(event.description)}</p>
          </div>

          ${ownerPanel}
        </div>

        <aside class="detail-side">
          <div class="card" style="display:flex;flex-direction:column;gap:12px">
            ${event.capacity > 0 ? meterHTML(capacityRatio, seats, capacitySeverity) : ''}
            ${actionHtml}
          </div>
          <div class="card">
            <h3 style="font-size:0.95rem">Награда</h3>
            <div class="stat-value" style="font-size:1.3rem">🍀 +${event.pointsReward}</div>
            <div class="stat-label">баллов за подтверждённое участие</div>
          </div>
        </aside>
      </div>`,
    mount(el) {
      el.querySelector('#join-event')?.addEventListener('click', async () => {
        await api(`/events/${id}/join`, { method: 'POST' });
        await navigate();
      });
      el.querySelector('#leave-event')?.addEventListener('click', async () => {
        await api(`/events/${id}/join`, { method: 'DELETE' });
        await navigate();
      });
      el.querySelector('#delete-event')?.addEventListener('click', async () => {
        if (confirm('Удалить событие? Это действие необратимо.')) {
          await api(`/events/${id}`, { method: 'DELETE' });
          location.hash = '#/events';
        }
      });
      el.querySelectorAll('[data-confirm]').forEach((btn) => {
        btn.addEventListener('click', async () => {
          await api(`/events/${id}/participants/${btn.dataset.confirm}/confirm`, { method: 'POST' });
          await navigate();
        });
      });
    },
  };
}
