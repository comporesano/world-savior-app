/** Страница входа. */

import { auth } from '../auth.js';
import { go } from '../router.js';

export function loginView() {
  return {
    html: `
      <div class="auth-wrap">
        <div class="card auth-card">
          <h1 class="auth-title">С возвращением! 🌍</h1>
          <p class="auth-sub">Войдите, чтобы записываться на события и начислять баллы</p>
          <form id="login-form" novalidate>
            <div id="login-errors"></div>
            <div class="field">
              <label for="l-email">Email</label>
              <input id="l-email" type="email" required autocomplete="email" placeholder="you@example.com"/>
            </div>
            <div class="field">
              <label for="l-password">Пароль</label>
              <input id="l-password" type="password" required autocomplete="current-password" placeholder="••••••••"/>
            </div>
            <button class="btn btn-primary btn-block btn-lg" type="submit">Войти</button>
          </form>
          <div class="demo-hint">
            Демо-доступ организатора:<br/>
            <strong>anna@eco.dev</strong> / <strong>Demo1234!</strong>
          </div>
          <p class="small muted" style="text-align:center;margin:16px 0 0">Нет аккаунта? <a href="#/register">Зарегистрироваться</a></p>
        </div>
      </div>`,
    mount(el) {
      const form = el.querySelector('#login-form');
      const errorsBox = el.querySelector('#login-errors');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorsBox.innerHTML = '';
        const email = form['l-email'].value.trim();
        const password = form['l-password'].value;
        try {
          await auth.login(email, password);
          go('#/');
        } catch (err) {
          errorsBox.innerHTML = `<div class="error-box">⚠️ ${err.message}</div>`;
        }
      });
    },
  };
}
