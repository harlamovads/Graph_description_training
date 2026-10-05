"""A practice session the student started from their own sentence has to be legible to the
teacher: listed with its origin, openable round by round, and counted in the statistics.

Needs playwright (pip install playwright && playwright install chromium).
"""
import sys, time
import requests
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1"; API = f"{BASE}/api"; PW = "Password123"
ts = str(int(time.time()))[-6:]
fails = []


def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + (f'   {extra}' if extra else ''))
    if not cond:
        fails.append(name)


tmail = f"ts{ts}t@e.com"; smail = f"ts{ts}s@e.com"
t = requests.post(f"{API}/auth/register", json={"username": f"ts{ts}t", "email": tmail,
                  "password": PW, "role": "teacher"}, timeout=60).json()
th = {"Authorization": f"Bearer {t['access_token']}"}
code = requests.post(f"{API}/auth/generate-invitation", headers=th, timeout=60).json()["code"]
st = requests.post(f"{API}/auth/register", json={"username": f"ts{ts}s", "email": smail,
                   "password": PW, "role": "student", "experiment_consent": True,
                   "invitation_code": code}, timeout=60).json()
sh = {"Authorization": f"Bearer {st['access_token']}"}
sid = st["user"]["id"]

SENT = "She go to school every day."
i = SENT.index("go")
sess = requests.post(f"{API}/practice/start-manual", headers=sh,
                     json={"sentence": SENT,
                           "marks": [{"start": i, "end": i + 2, "correction": "goes"}]},
                     timeout=600).json()
# play two rounds so there is history for the teacher to read
requests.post(f"{API}/practice/{sess['id']}/submit", headers=sh,
              json={"text": "She goes to school every day."}, timeout=600)
requests.post(f"{API}/practice/{sess['id']}/submit", headers=sh,
              json={"text": "He goes to work by bus."}, timeout=600)

rows = requests.get(f"{API}/practice/teacher", headers=th, timeout=60).json()["sessions"]
row = next((r for r in rows if r["id"] == sess["id"]), None)
check("the session reaches the teacher's list", row is not None)
if row:
    check("it is labelled as coming from the student's own sentence",
          row.get("source") == "manual", str(row.get("source")))
    check("the list carries the sentence practised",
          row.get("original_sentence") == SENT, repr(row.get("original_sentence")))

rev = requests.get(f"{API}/practice/{sess['id']}/review", headers=th, timeout=60).json()
check("the teacher can open it round by round",
      len(rev.get("history") or []) >= 2, str(len(rev.get("history") or [])))
check("the review says where it came from", rev.get("source") == "manual")

det = requests.get(f"{API}/stats/students/{sid}", headers=th, timeout=60).json()
ps = det.get("practice_sessions", {})
check("statistics count it as a session from an own sentence",
      ps.get("total_from_own_sentences") == 1, str(ps.get("total_from_own_sentences")))
check("and not as one from submitted work",
      ps.get("total_from_submissions") == 0, str(ps.get("total_from_submissions")))
listed = next((x for x in ps.get("sessions", []) if x["id"] == sess["id"]), None)
check("it is not mislabelled 'Unknown task'",
      listed and listed.get("task_title") is None, str(listed))
check("its errors are in the practice error distribution",
      sum((ps.get("error_distribution") or {}).values()) > 0, str(ps.get("error_distribution")))

with sync_playwright() as pw:
    b = pw.chromium.launch(); page = b.new_page(viewport={"width": 1500, "height": 1000})
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.fill('input[name="email"]', tmail); page.fill('input[name="password"]', PW)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)

    page.goto(f"{BASE}/practice-review", wait_until="networkidle")
    page.wait_for_selector("table", timeout=20000); page.wait_for_timeout(800)
    body = " ".join(page.inner_text("body").split())
    check("the list shows it as an own sentence", "Own sentence" in body, body[:220])
    check("the list shows what was practised", "She go to school every day." in body, body[:220])

    page.click(f'tr:has-text("{st["user"]["username"]}")')
    page.wait_for_url("**/practice-review/**", timeout=20000)
    page.wait_for_timeout(1500)
    body = " ".join(page.inner_text("body").split())
    check("the detail page explains the corrections are the student's own",
          "marked the errors in it" in body, body[:260])
    check("the detail page shows the sentence and the target",
          "She go to school every day." in body and "She goes to school every day." in body,
          body[:260])
    check("the rounds are shown", "Round 1" in body and "Round 2" in body, body[:260])
    check("it does not claim an unknown task", "Unknown task" not in body)

    page.goto(f"{BASE}/stats?student={sid}", wait_until="networkidle")
    page.wait_for_selector("text=Sentences practiced", timeout=25000); page.wait_for_timeout(1200)
    body = " ".join(page.inner_text("body").split())
    check("the statistics page shows the split", "From their own sentences: 1" in body,
          body[body.find("Sentences practiced"):][:240])
    b.close()

print('\n' + ('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
