/** Страница регистрации. */

import { auth } from '../auth.js';
import { go } from '../router.js';

export function registerView() {
  return {
    html: `
      <div class="auth-wrap">
        <div class="card auth-card">
          <h1 class="auth-title">Присоединяйтесь! 🌱</h1>
          <p class="auth-sub">Аккаунт нужен, чтобы записываться на события и копить эко-баллы</p>
          <form id="register-form" novalidate>
            <div id="register-errors"></div>
            <div class="field">
              <label for="r-name">Имя</label>
              <input id="r-name" type="text" required minlength="2" maxlength="60" autocomplete="name" placeholder="Как к вам обращаться"/>
            </div>
            <div class="field">
              <label for="r-email">Email</label>
              <input id="r-email" type="email" required autocomplete="email" placeholder="you@example.com"/>
            </div>
            <div class="field">
              <label for="r-password">Пароль</label>
              <input id="r-password" type="password" required minlength="8" maxlength="72" autocomplete="new-password" placeholder="Минимум 8 символов"/>
            </div>
            <button class="btn btn-primary btn-block btn-lg" type="submit">Создать аккаунт</button>
          </form>
          <p class="small muted" style="text-align:center;margin:16px 0 0">Уже есть аккаунт? <a href="#/login">Войти</a></p>
        </div>
      </div>`,
    mount(el) {
      const form = el.querySelector('#register-form');
      const errorsBox = el.querySelector('#register-errors');
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        errorsBox.innerHTML = '';
        const name = form['r-name'].value.trim();
        const email = form['r-email'].value.trim();
        const password = form['r-password'].value;
        try {
          await auth.register(name, email, password);
          go('#/');
        } catch (err) {
          const details = (err.details ?? []).map((d) => `<div>· ${d.message}</div>`).join('');
          errorsBox.innerHTML = `<div class="error-box">⚠️ ${err.message}${details}</div>`;
        }
      });
    },
  };
}
