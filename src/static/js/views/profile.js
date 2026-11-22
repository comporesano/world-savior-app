/** Профиль текущего пользователя: уровень, статистика, история участия. */

import { api } from '../api.js';
import { auth } from '../auth.js';
import { avatarHTML, chipHTML, emptyHTML, errorBoxHTML, levelMeterHTML, statTileHTML, statusBadgeHTML } from '../components.js';
import { esc, fmtDate, fmtNum, levelForPoints, plural, rankTitle } from '../utils.js';

export async function profileView() {
  if (!auth.user) {
    return { html: '<div class="error-box">⚠️ Чтобы видеть профиль, нужно <a href="#/login">войти</a>.</div>' };
  }

  try {
    const [me, history] = await Promise.all([api('/auth/me'), api('/me/events')]);

    const confirmed = history.items.filter((i) => i.status === 'confirmed').length;
    const joined = history.items.filter((i) => i.status === 'joined').length;

    const historyRows = history.items.length
      ? history.items
          .map((item) => `
            <div class="participant-row">
              <div class="p-name" style="flex:1;min-width:0">
                <a href="#/events/${item.event.id}" style="font-weight:700;color:var(--text)">${esc(item.event.title)}</a>
                <div class="muted small">${esc(fmtDate(item.event.startsAt))} · ${esc(item.event.location)} · организатор: ${esc(item.event.organizerName)}</div>
              </div>
              ${chipHTML(item.event.type)}
              ${statusBadgeHTML(item.status)}
            </div>`)
          .join('')
      : emptyHTML('🌱', 'Пока нет участий', 'Запишитесь на первое событие из ленты — и оно появится здесь.');

    return {
      html: `
        <div class="page-head">
          <h1 class="page-title">Мой профиль</h1>
        </div>

        <div class="card profile-head">
          ${avatarHTML(me.user.name, 'avatar-lg')}
          <div style="flex:1;min-width:0">
            <h1 style="margin:0;font-size:1.5rem">${esc(me.user.name)}</h1>
            <div class="muted">${esc(me.user.email)}</div>
            <div class="muted small" style="margin-top:4px">${esc(me.user.bio || 'О себе пока ничего не рассказано.')}</div>
          </div>
          <div style="text-align:right">
            <div class="stat-value" style="font-size:1.9rem">🍀 ${esc(fmtNum(me.user.points))}</div>
            <div class="stat-label">эко-баллов · уровень ${me.user.level} · ${esc(rankTitle(me.user.level))}</div>
          </div>
        </div>

        <div class="profile-stats">
          ${statTileHTML('✅', 'Подтверждено участий', confirmed)}
          ${statTileHTML('⏳', 'Ожидают подтверждения', joined)}
          ${statTileHTML('🎯', 'Уровень', `${me.user.level} · ${rankTitle(me.user.level)}`)}
        </div>

        <div class="card" style="margin-bottom:24px">
          <h3 style="font-size:0.95rem">Прогресс до следующего уровня</h3>
          ${levelMeterHTML(me.user.points)}
        </div>

        <div class="card" style="padding:8px 20px">
          <h3 style="padding:12px 0 4px">История участия</h3>
          ${historyRows}
        </div>`,
    };
  } catch (err) {
    return { html: errorBoxHTML(err) };
  }
}
