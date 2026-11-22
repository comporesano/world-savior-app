/** Состояние авторизации на клиенте. */

import { api, tokens } from './api.js';

export const auth = {
  user: null, // { id, name, email, bio, points, level, rankTitle } | null
  loaded: false,

  async init() {
    if (!tokens.getAccess()) {
      this.loaded = true;
      return;
    }
    try {
      const res = await api('/auth/me');
      this.user = res.user;
    } catch {
      tokens.clear();
      this.user = null;
    }
    this.loaded = true;
  },

  async login(email, password) {
    const res = await api('/auth/login', { method: 'POST', body: { email, password }, skipAuth: true });
    tokens.set(res.tokens.accessToken, res.tokens.refreshToken);
    this.user = { ...res.user, level: 1, rankTitle: 'Новичок' };
    // точные уровень/ранг подтянем из /auth/me
    const me = await api('/auth/me');
    this.user = me.user;
  },

  async register(name, email, password) {
    const res = await api('/auth/register', { method: 'POST', body: { name, email, password }, skipAuth: true });
    tokens.set(res.tokens.accessToken, res.tokens.refreshToken);
    const me = await api('/auth/me');
    this.user = me.user;
  },

  async logout() {
    const refresh = tokens.getRefresh();
    if (refresh) {
      try {
        await api('/auth/logout', { method: 'POST', body: { refreshToken: refresh }, skipAuth: true });
      } catch { /* сервер недоступен — локально всё равно выходим */ }
    }
    tokens.clear();
    this.user = null;
  },

  async refreshUser() {
    if (!tokens.getAccess()) return;
    try {
      const me = await api('/auth/me');
      this.user = me.user;
    } catch {
      this.user = null;
    }
  },
};
