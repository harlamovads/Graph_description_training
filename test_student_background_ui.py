"""Student background fields (age, gender, native language, English level) on the profile page.

Needs playwright (pip install playwright && playwright install chromium).
"""
import sys, time
import requests
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1"; API=f"{BASE}/api"; PW="Password123"
ts=str(int(time.time()))[-6:]
fails=[]
def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ')+name+(f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

tmail=f"bg{ts}t@e.com"; smail=f"bg{ts}s@e.com"
t=requests.post(f"{API}/auth/register",json={"username":f"bg{ts}t","email":tmail,"password":PW,"role":"teacher"},timeout=60).json()
th={"Authorization":f"Bearer {t['access_token']}"}
code=requests.post(f"{API}/auth/generate-invitation",headers=th,timeout=60).json()["code"]
st=requests.post(f"{API}/auth/register",json={"username":f"bg{ts}s","email":smail,"password":PW,
  "role":"student","experiment_consent":True,"invitation_code":code},timeout=60).json()
sh={"Authorization":f"Bearer {st['access_token']}"}
sid=st["user"]["id"]

# --- API level ---
r=requests.put(f"{API}/auth/profile",headers=sh,
    json={"age":21,"gender":"Female","native_language":"Russian","english_level":"B2"},timeout=60)
check("a student can save their background", r.status_code==200, f"status={r.status_code} {r.text[:120]}")
u=r.json().get("user",{}) if r.status_code==200 else {}
check("the values come back", (u.get("age"),u.get("gender"),u.get("native_language"),u.get("english_level"))
      == (21,"Female","Russian","B2"), str(u)[:200])

r=requests.put(f"{API}/auth/profile",headers=th,json={"age":40},timeout=60)
check("teachers have no background profile", r.status_code==403, f"status={r.status_code}")
r=requests.put(f"{API}/auth/profile",headers=sh,json={"age":"twenty"},timeout=60)
check("a non-numeric age is rejected", r.status_code==400, f"status={r.status_code}")
r=requests.put(f"{API}/auth/profile",headers=sh,json={"age":3},timeout=60)
check("an implausible age is rejected", r.status_code==400, f"status={r.status_code}")
r=requests.put(f"{API}/auth/profile",headers=sh,json={"gender":None},timeout=60)
check("a field can be cleared", r.status_code==200 and r.json()["user"]["gender"] is None, r.text[:120])
r=requests.put(f"{API}/auth/profile",headers=sh,json={"english_level":"C1"},timeout=60)
check("other fields survive a partial update",
      r.json()["user"]["native_language"]=="Russian" and r.json()["user"]["english_level"]=="C1",
      str(r.json().get("user"))[:160])

# the teacher's own student list carries the background, for analysis later
tp=requests.get(f"{API}/auth/profile",headers=th,timeout=60).json()
mine=next((s for s in tp.get("students",[]) if s["id"]==sid), None)
check("the teacher's student list carries it too", mine and mine.get("native_language")=="Russian",
      str(mine)[:160])

# --- browser ---
with sync_playwright() as pw:
    b=pw.chromium.launch(); page=b.new_page(viewport={"width":1400,"height":1000})
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.fill('input[name="email"]', smail); page.fill('input[name="password"]', PW)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)
    page.goto(f"{BASE}/profile", wait_until="networkidle")
    page.wait_for_selector("text=About you", timeout=20000)

    check("the form shows the saved age", page.input_value('input[type="number"]') == "21",
          page.input_value('input[type="number"]'))
    check("the native language is prefilled",
          page.get_by_label("Native language").input_value() == "Russian",
          page.get_by_label("Native language").input_value())

    page.get_by_label("Native language").fill("Tatar")
    page.fill('input[type="number"]', "22")
    # MUI renders a select as a combobox div, not a <select>; open it by its label.
    page.get_by_label("Gender").click()
    page.wait_for_selector('li[role="option"]', timeout=10000)
    # Exact match: has_text is a case-insensitive substring, and "Female" contains "male".
    page.get_by_role("option", name="Male", exact=True).click()
    page.wait_for_timeout(400)
    page.click('button:has-text("Save details")')
    page.wait_for_timeout(2500)
    check("saving confirms on screen", "saved" in page.inner_text("body").lower(),
          page.inner_text("body")[:0])

    after=requests.get(f"{API}/auth/profile",headers=sh,timeout=60).json()["user"]
    check("the edit persisted", after["age"] == 22, str(after)[:180])
    check("the gender choice persisted", after["gender"] == "Male", f'gender={after["gender"]!r}')
    check("a freely typed native language is kept", after["native_language"] == "Tatar",
          f'native_language={after["native_language"]!r}')

    # gender offers exactly two choices now
    page.get_by_label("Gender").click()
    page.wait_for_selector('li[role="option"]', timeout=10000)
    options = [o.strip() for o in page.locator('li[role="option"]').all_inner_texts()]
    page.keyboard.press("Escape")
    check("gender offers only Female and Male (plus leaving it unset)",
          [o for o in options if o.lower() not in ("not specified", "")] == ["Female", "Male"],
          str(options))

    # a teacher does not get this form
    page2=b.new_page()
    page2.goto(f"{BASE}/login", wait_until="networkidle")
    page2.fill('input[name="email"]', tmail); page2.fill('input[name="password"]', PW)
    page2.click('button[type="submit"]')
    page2.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)
    page2.goto(f"{BASE}/profile", wait_until="networkidle")
    page2.wait_for_timeout(1500)
    check("teachers don't see the background form", "About you" not in page2.inner_text("body"))
    b.close()

print('\n'+('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
