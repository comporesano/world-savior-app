/** Рейтинг участников по эко-баллам. */

import { api } from '../api.js';
import { auth } from '../auth.js';
import { avatarHTML, errorBoxHTML, levelChipHTML } from '../components.js';
import { esc, fmtNum, plural } from '../utils.js';

const MEDALS = ['🥇', '🥈', '🥉'];

export async function leaderboardView() {
  try {
    const data = await api('/leaderboard?limit=20');

    const rows = data.items
      .map((entry) => {
        const isMe = auth.user?.id === entry.user.id;
        return `
          <div class="lb-row${isMe ? ' me' : ''}">
            <span class="lb-rank">${entry.rank <= 3 ? MEDALS[entry.rank - 1] : entry.rank}</span>
            <div class="lb-user">
              ${avatarHTML(entry.user.name)}
              <div style="min-width:0">
                <div class="lb-name">${esc(entry.user.name)}${isMe ? ' <span class="muted small">(это вы)</span>' : ''}</div>
                <div class="lb-sub">${entry.confirmedCount} ${plural(entry.confirmedCount, 'подтверждённое участие', 'подтверждённых участия', 'подтверждённых участий')}</div>
              </div>
            </div>
            ${levelChipHTML(entry.user.points)}
            <span class="lb-points">${esc(fmtNum(entry.user.points))}</span>
          </div>`;
      })
      .join('');

    const inTop = data.items.some((e) => e.user.id === auth.user?.id);
    const meCard = auth.user && !inTop
      ? `<div class="card" style="margin-bottom:16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap">
           ${avatarHTML(auth.user.name)}
           <div style="flex:1;min-width:0">
             <div style="font-weight:700">${esc(auth.user.name)}</div>
             <div class="muted small">Ваш результат (вне топ-${data.items.length})</div>
           </div>
           ${levelChipHTML(auth.user.points)}
           <span class="lb-points">${esc(fmtNum(auth.user.points))}</span>
         </div>`
      : '';

    return {
      html: `
        <div class="page-head">
          <div>
            <h1 class="page-title">Рейтинг эко-волонтёров</h1>
            <p class="page-sub">Баллы начисляются за подтверждённое участие в мероприятиях</p>
          </div>
        </div>
        ${meCard}
        <div class="card" style="padding:8px 20px">
          <div class="leaderboard">${rows || '<div class="muted" style="padding:20px">Пока никого нет — станьте первым!</div>'}</div>
        </div>`,
    };
  } catch (err) {
    return { html: errorBoxHTML(err) };
  }
}
