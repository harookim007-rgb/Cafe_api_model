"""CI 에서 띄운 컨테이너의 관리자 화면을 캡처 (README 스크린샷 갱신용)"""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("docs/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
BASE = "http://localhost:8080"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1280, "height": 860})
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))

    for view in ["home", "menus", "reviews", "vision", "chat"]:
        page.goto(f"{BASE}/#{view}")
        page.wait_for_timeout(800)
        if view == "home":
            page.click("#sentiment-form button")
            page.wait_for_timeout(500)
        page.screenshot(path=OUT / f"{view}.png", full_page=True)

    # 리뷰 등록 흐름
    page.goto(f"{BASE}/#reviews")
    page.wait_for_timeout(500)
    page.fill("#review-author", "ci")
    page.fill("#review-content", "커피가 너무 써서 별로였어요")
    page.click("#review-form button[type=submit]")
    page.wait_for_timeout(800)
    page.screenshot(path=OUT / "reviews_after_post.png", full_page=True)

    mobile = browser.new_page(viewport={"width": 390, "height": 844})
    mobile.goto(f"{BASE}/#menus")
    mobile.wait_for_timeout(800)
    mobile.screenshot(path=OUT / "mobile.png", full_page=True)

    browser.close()

if errors:
    raise SystemExit("page errors: " + "; ".join(errors))
print("ok")
