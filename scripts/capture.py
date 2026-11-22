"""Скриншоты и демо-видео приложения (Playwright, Python).

Запуск: .venv/bin/python scripts/capture.py
Требуется запущенный сервер (по умолчанию http://localhost:4000).
"""

import json
import os
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
BASE = os.getenv("BASE_URL", "http://localhost:4000")
SHOTS = ROOT / "docs" / "screenshots"
DEMO_DIR = ROOT / "docs" / "demo-recordings"
CHROME = str(Path.home() / ".cache" / "ms-playwright" / "chromium-1208" / "chrome-linux64" / "chrome")

ANNA = {"email": "anna@eco.dev", "password": "Demo1234!"}


def get_tokens(pw) -> dict:
    ctx = pw.request.new_context(base_url=BASE)
    res = ctx.post(
        "/api/v1/auth/login",
        data=json.dumps(ANNA),
        headers={"Content-Type": "application/json"},
    )
    body = res.json()
    ctx.dispose()
    assert res.ok, f"login failed: {res.status}: {body}"
    return body["tokens"]


def screenshot(page, name: str, full: bool = False):
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / name), full_page=full)
    print(f"  📸 {name}")


def idle(page):
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(400)


def take_screenshots(pw, browser) -> None:
    print("Скриншоты:")

    # --- Анонимные страницы ---
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE}/#/")
    idle(page)
    screenshot(page, "01-home.png", full=True)

    page.goto(f"{BASE}/#/events")
    idle(page)
    screenshot(page, "02-events.png")

    page.goto(f"{BASE}/#/login")
    idle(page)
    screenshot(page, "06-login.png")
    ctx.close()

    # --- Авторизованные страницы (Анна-организатор) ---
    # Вход только через UI: CSP приложения блокирует inline-скрипты Playwright
    # (add_init_script), поэтому localStorage напрямую не засеять.
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto(f"{BASE}/#/login")
    idle(page)
    page.fill("#l-email", ANNA["email"])
    page.fill("#l-password", ANNA["password"])
    page.click('#login-form button[type="submit"]')
    page.wait_for_selector(".nav-points", timeout=10_000)

    page.goto(f"{BASE}/#/events/1")
    idle(page)
    screenshot(page, "03-event-detail.png")

    page.goto(f"{BASE}/#/leaderboard")
    idle(page)
    screenshot(page, "04-leaderboard.png")

    page.goto(f"{BASE}/#/profile")
    idle(page)
    screenshot(page, "05-profile.png")

    page.goto(f"{BASE}/#/events/new")
    idle(page)
    screenshot(page, "07-event-form.png")
    ctx.close()

    # --- Мобильный вид ---
    mctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
    )
    mpage = mctx.new_page()
    mpage.goto(f"{BASE}/#/")
    idle(mpage)
    screenshot(mpage, "08-mobile-home.png")
    mctx.close()


def record_demo(browser) -> None:
    print("Демо-видео:")
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    ctx = browser.new_context(
        viewport={"width": 1440, "height": 900},
        record_video_dir=str(DEMO_DIR),
        record_video_size={"width": 1440, "height": 900},
    )
    page = ctx.new_page()

    # 1. Вход организатора (ждём признак успешного входа — счётчик баллов в шапке)
    page.goto(f"{BASE}/#/login")
    idle(page)
    page.wait_for_timeout(800)
    page.fill("#l-email", ANNA["email"])
    page.fill("#l-password", ANNA["password"])
    page.wait_for_timeout(900)
    page.click('#login-form button[type="submit"]')
    page.wait_for_selector(".nav-points", timeout=10_000)
    page.wait_for_timeout(2500)

    # 2. Лента событий
    page.goto(f"{BASE}/#/events")
    page.wait_for_selector("a.event-card", timeout=10_000)
    page.wait_for_timeout(3000)

    # 3. Событие организатора → подтверждение участия (начисление баллов)
    page.goto(f"{BASE}/#/events/1")
    page.wait_for_selector('[data-confirm]', timeout=10_000)
    page.wait_for_timeout(2500)
    page.click('[data-confirm] >> nth=0')
    page.wait_for_timeout(3000)

    # 4. Рейтинг
    page.goto(f"{BASE}/#/leaderboard")
    page.wait_for_selector(".lb-row", timeout=10_000)
    page.wait_for_timeout(3000)

    # 5. Создание события
    starts = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:00")
    page.goto(f"{BASE}/#/events/new")
    page.wait_for_selector("#f-title", timeout=10_000)
    page.wait_for_timeout(1500)
    page.fill("#f-title", "Субботник у набережной")
    page.wait_for_timeout(600)
    page.fill("#f-location", "Набережная реки, причал № 2")
    page.wait_for_timeout(600)
    page.fill("#f-starts", starts)
    page.wait_for_timeout(600)
    page.fill("#f-desc", "Приводим в порядок набережную после праздников: собираем мусор вдоль воды и в парковой зоне. Мешки и перчатки предоставим, берите друзей!")
    page.wait_for_timeout(2500)
    page.click('#event-form button[type="submit"]')
    page.wait_for_selector('h1:has-text("Субботник у набережной")', timeout=10_000)
    page.wait_for_timeout(3000)

    # 6. Профиль: уровень и история участия
    page.goto(f"{BASE}/#/profile")
    page.wait_for_selector(".avatar-lg", timeout=10_000)
    page.wait_for_timeout(3000)

    # 7. Главная
    page.click('a.brand[href="#/"]')
    page.wait_for_selector(".hero h1", timeout=10_000)
    page.wait_for_timeout(3000)

    ctx.close()
    videos = sorted(DEMO_DIR.glob("*.webm"), key=lambda p: p.stat().st_mtime)
    if not videos:
        print("  ⚠️ видео не записалось")
        return
    video = videos[-1]
    dest = ROOT / "docs" / "demo.mp4"
    converted = convert_to_mp4(video, dest)
    print(f"  🎬 {'docs/demo.mp4' if converted else 'docs/demo.webm (mp4 недоступен — см. README)'}")


def convert_to_mp4(src: Path, dest: Path) -> bool:
    """Конвертация webm → mp4. Сначала пробуем ffmpeg из пакета imageio-ffmpeg,
    затем бинарник из кэша Playwright, затем системный ffmpeg."""
    candidates = []
    try:
        import imageio_ffmpeg

        candidates.append(imageio_ffmpeg.get_ffmpeg_exe())
    except ImportError:
        pass
    for cached in Path.home().glob(".cache/ms-playwright/ffmpeg-*/ffmpeg-linux"):
        candidates.append(str(cached))
    candidates.append("ffmpeg")

    for ffmpeg in candidates:
        try:
            proc = subprocess.run(
                [
                    ffmpeg, "-y", "-i", str(src), "-c:v", "libx264",
                    "-preset", "veryfast", "-crf", "28", "-pix_fmt", "yuv420p", str(dest),
                ],
                capture_output=True,
                timeout=180,
            )
            if proc.returncode == 0 and dest.exists():
                return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    # mp4 не получился — оставляем webm
    dest.unlink(missing_ok=True)
    webm_dest = ROOT / "docs" / "demo.webm"
    if src != webm_dest:
        import shutil

        shutil.copy2(src, webm_dest)
    return False


def main() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=CHROME)
        take_screenshots(pw, browser)
        record_demo(browser)
        browser.close()


if __name__ == "__main__":
    main()
