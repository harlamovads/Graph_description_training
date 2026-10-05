"""Browser test for task editing and the change-password dialog.

Needs playwright (pip install playwright && playwright install chromium); it is not part of the
app's requirements, so this file is optional tooling rather than a build step.

Drives the two flows in a real browser, because both bugs were UI-level: a button with
no handler, and a redirect fired by an axios interceptor. Neither shows up in an API test."""
import base64, sys, time
import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1"; API = f"{BASE}/api"; PW = "Password123"
ts = str(int(time.time()))[-6:]
fails = []
def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + (f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
def teacher(tag):
    r = requests.post(f"{API}/auth/register", json={"username": f"ui{ts}{tag}",
        "email": f"ui{ts}{tag}@e.com", "password": PW, "role": "teacher"}, timeout=60).json()
    return {"Authorization": f"Bearer {r['access_token']}"}, f"ui{ts}{tag}@e.com"
ha, mail_a = teacher("a")
hb, mail_b = teacher("b")
shared = requests.post(f"{API}/tasks/", headers=ha,
    data={"title": f"UI shared {ts}", "description": "Describe the chart carefully.",
          "is_from_database": "true"},
    files={"image": ("c.png", png, "image/png")}, timeout=60).json()["task"]

def wait_for(page, selector, timeout=20000):
    """The task page fetches after mount, so 'networkidle' can land before the button exists."""
    try:
        page.wait_for_selector(selector, timeout=timeout, state="visible")
        return True
    except Exception:
        return False


def login(page, email, password=PW):
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    # Login is an async request that stores the token and then redirects. Without waiting for
    # that, the next navigation runs while localStorage is still empty and ProtectedRoute sends
    # us straight back to /login - which looks exactly like a broken page.
    page.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)
    page.wait_for_url(lambda url: "/login" not in url, timeout=20000)
    page.wait_for_load_state("networkidle")

with sync_playwright() as pw:
    browser = pw.chromium.launch()

    # ---- 1. the creator's Edit button now does something ----
    page = browser.new_page()
    login(page, mail_a)
    page.goto(f"{BASE}/tasks/{shared['id']}", wait_until="networkidle")
    found = wait_for(page, 'a:has-text("Edit Task")')
    btn = page.locator('a:has-text("Edit Task")').first
    check("creator sees an 'Edit Task' button", found)
    btn.click(); page.wait_for_load_state("networkidle")
    check("the button now navigates to the edit form",
          f"/tasks/{shared['id']}/edit" in page.url, page.url)
    wait_for(page, 'input[name="title"]')
    check("the form is prefilled with the task",
          page.input_value('input[name="title"]') == f"UI shared {ts}",
          page.input_value('input[name="title"]'))
    page.fill('input[name="title"]', "Owner edited in UI")
    page.click('button:has-text("Save Changes")')
    page.wait_for_load_state("networkidle")
    wait_for(page, 'a:has-text("Edit Task")')
    check("saving returns to the task page", f"/tasks/{shared['id']}" in page.url, page.url)
    check("the new title is shown", "Owner edited in UI" in page.content())
    page.close()

    # ---- 2. another teacher gets a copy ----
    page = browser.new_page()
    login(page, mail_b)
    page.goto(f"{BASE}/tasks/{shared['id']}", wait_until="networkidle")
    found = wait_for(page, 'a:has-text("Edit a Copy")')
    btn = page.locator('a:has-text("Edit a Copy")').first
    check("a non-creator is offered 'Edit a Copy'", found)
    btn.click(); page.wait_for_load_state("networkidle")
    wait_for(page, 'input[name="title"]')
    body = page.content()
    check("the form warns that a copy will be made", "belongs to another teacher" in body)
    page.fill('input[name="title"]', "Teacher B's version")
    page.click('button:has-text("Save as My Copy")')
    page.wait_for_load_state("networkidle")
    wait_for(page, 'a:has-text("Edit Task")')
    check("lands on a different task than the original",
          "/tasks/" in page.url and f"/tasks/{shared['id']}" not in page.url, page.url)
    check("the copy shows B's title", "Teacher B's version" in page.content())
    page.close()

    # the original is still the owner's version
    again = requests.get(f"{API}/tasks/{shared['id']}", headers=ha, timeout=60).json()
    check("the original kept the owner's title", again["title"] == "Owner edited in UI", again["title"])

    # ---- 3. a wrong current password must NOT bounce to /login ----
    page = browser.new_page()
    login(page, mail_b)
    start_url = page.url
    wait_for(page, 'button[aria-label="account of current user"]')
    page.click('button[aria-label="account of current user"]')
    page.click('li:has-text("Change password")')
    wait_for(page, 'div[role="dialog"] input[type="password"]')
    inputs = page.locator('div[role="dialog"] input[type="password"]')
    inputs.nth(0).fill("TotallyWrong1")
    inputs.nth(1).fill("Brandnew1234")
    inputs.nth(2).fill("Brandnew1234")
    page.click('div[role="dialog"] button:has-text("Change password")')
    page.wait_for_timeout(2500)
    check("still signed in, not redirected to /login", "/login" not in page.url, page.url)
    check("the dialog is still open", page.locator('div[role="dialog"]').count() > 0)
    check("it says the current password is wrong",
          "incorrect" in page.content().lower(), page.content()[:0])
    check("the token was not cleared",
          bool(page.evaluate("() => localStorage.getItem('token')")))
    page.close()
    browser.close()

print('\n' + ('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
