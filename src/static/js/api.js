/** Обёртка над fetch: Bearer-токены, авто-обновление access-токена (single-flight). */

const BASE = '/api/v1';
const ACCESS_KEY = 'ecosavior.access';
const REFRESH_KEY = 'ecosavior.refresh';

export class ApiError extends Error {
  constructor(status, code, message, details) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details ?? [];
  }
}

export const tokens = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set(access, refresh) {
    if (access) localStorage.setItem(ACCESS_KEY, access); else localStorage.removeItem(ACCESS_KEY);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh); else localStorage.removeItem(REFRESH_KEY);
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

let refreshPromise = null;

async function refreshAccess() {
  const refresh = tokens.getRefresh();
  if (!refresh) return false;
  try {
    const res = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refreshToken: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    tokens.set(data.tokens.accessToken, data.tokens.refreshToken);
    return true;
  } catch {
    return false;
  }
}

export async function api(path, { method = 'GET', body, skipAuth = false } = {}) {
  const buildHeaders = () => {
    const headers = { 'Content-Type': 'application/json' };
    const access = tokens.getAccess();
    if (access) headers.Authorization = `Bearer ${access}`;
    return headers;
  };

  const doFetch = (headers) => fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  let res = await doFetch(buildHeaders());

  // 401 на защищённом маршруте → пробуем обновить access-токен один раз
  if (res.status === 401 && !skipAuth && tokens.getAccess() && !path.startsWith('/auth/')) {
    refreshPromise ??= refreshAccess().finally(() => { refreshPromise = null; });
    const refreshed = await refreshPromise;
    if (refreshed) {
      res = await doFetch(buildHeaders());
    }
  }

  if (!res.ok) {
    let data = null;
    try { data = await res.json(); } catch { /* не JSON */ }
    throw new ApiError(
      res.status,
      data?.error?.code ?? 'UNKNOWN',
      data?.error?.message ?? `Ошибка ${res.status}`,
      data?.error?.details ?? [],
    );
  }
  if (res.status === 204) return null;
  return res.json();
}
