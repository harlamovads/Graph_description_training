"""Browser test for the profile page, reaching past submissions, and teacher annotations.

Needs playwright (pip install playwright && playwright install chromium).
"""
import base64, json, sys, time
import requests
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1"; API=f"{BASE}/api"; PW="Password123"
ts=str(int(time.time()))[-6:]
fails=[]
def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ')+name+(f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

png=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
tmail=f"pa{ts}t@e.com"; smail=f"pa{ts}s@e.com"
t=requests.post(f"{API}/auth/register",json={"username":f"pa{ts}t","email":tmail,"password":PW,"role":"teacher"},timeout=60).json()
th={"Authorization":f"Bearer {t['access_token']}"}
code=requests.post(f"{API}/auth/generate-invitation",headers=th,timeout=60).json()["code"]
st=requests.post(f"{API}/auth/register",json={"username":f"pa{ts}s","email":smail,"password":PW,
  "role":"student","experiment_consent":True,"invitation_code":code},timeout=60).json()
sh={"Authorization":f"Bearer {st['access_token']}"}
sid=st["user"]["id"]
tid=requests.post(f"{API}/tasks/",headers=th,data={"title":f"PA {ts}","description":"Describe it."},
   files={"image":("c.png",png,"image/png")},timeout=60).json()["task"]["id"]
requests.post(f"{API}/tasks/{tid}/assign",headers=th,json={"student_ids":[sid]},timeout=60)
essay="<p>The chart show the amount of money what was spend on food.</p>"
sub=requests.post(f"{API}/submissions/",headers=sh,json={"task_id":tid,"content":essay},timeout=600).json()["submission"]

# --- API level: profile payloads ---
tp=requests.get(f"{API}/auth/profile",headers=th,timeout=60).json()
check("teacher profile lists students", any(s["id"]==sid for s in tp.get("students",[])), str(tp)[:160])
check("teacher profile has the invitation code", tp.get("invitation_code") == code)
sp=requests.get(f"{API}/auth/profile",headers=sh,timeout=60).json()
check("student profile names their teacher",
      (sp.get("teacher") or {}).get("username") == f"pa{ts}t", str(sp)[:160])

# --- API level: annotations permissions ---
r=requests.put(f"{API}/submissions/{sub['id']}/annotations",headers=sh,
               json={"annotations":[]},timeout=60)
check("students cannot annotate", r.status_code == 403, f"status={r.status_code}")
r=requests.put(f"{API}/submissions/{sub['id']}/annotations",headers=th,
               json={"annotations":[{"id":"x","type":"bogus","start":0,"end":3,"content":"c"}]},timeout=60)
check("an unknown annotation type is rejected", r.status_code == 400, f"status={r.status_code}")
r=requests.put(f"{API}/submissions/{sub['id']}/annotations",headers=th,
               json={"annotations":[{"id":"x","type":"comment","start":5,"end":2,"content":"c"}]},timeout=60)
check("a backwards range is rejected", r.status_code == 400, f"status={r.status_code}")

def login(page, email, password=PW):
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.fill('input[name="email"]', email); page.fill('input[name="password"]', password)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)
    page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
    page.wait_for_load_state("networkidle")

with sync_playwright() as pw:
    b=pw.chromium.launch()

    # ---- teacher: sidebar -> profile -> student -> past submission ----
    page=b.new_page(viewport={"width":1400,"height":950})
    login(page, tmail)
    page.click('button[aria-label="open drawer"]')
    page.wait_for_timeout(600)
    acct = page.locator('a[href="/profile"]')
    check("the sidebar account row links to the profile", acct.count() > 0)
    acct.first.click()
    page.wait_for_url("**/profile", timeout=20000)
    page.wait_for_selector('text=My students', timeout=20000)
    body=page.inner_text("body")
    check("profile shows the student list", f"pa{ts}s" in body)
    check("profile shows the change-password button", "change password" in body.lower())
    check("profile shows the invitation code", code in body)

    page.click(f'a[href="/stats?student={sid}"]')
    page.wait_for_url("**/stats**", timeout=20000)
    page.wait_for_selector("text=Submitted Work", timeout=25000)
    check("the student's stats open directly from the profile",
          "Submitted Work" in page.inner_text("body"))
    link = page.locator(f'a[href="/submissions/{sub["id"]}/review"]')
    check("the submitted work links to the submission", link.count() > 0)
    link.first.click()
    page.wait_for_selector("text=Student's Response", timeout=25000)

    # ---- annotate: select a word and add a correction ----
    page.wait_for_timeout(800)
    added = page.evaluate("""() => {
        // MUI applies sx through a generated class, so the computed style is what to look at.
        const el = Array.from(document.querySelectorAll('div'))
          .find(e => getComputedStyle(e).whiteSpace === 'pre-wrap'
                     && e.textContent.includes('chart'));
        if (!el) return 'no container';
        const node = el.firstChild;
        const text = node.textContent;
        const i = text.indexOf('show');
        const range = document.createRange();
        range.setStart(node, i); range.setEnd(node, i + 4);
        const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
        el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: 200, clientY: 300}));
        return 'ok';
    }""")
    check("the text container is annotatable", added == "ok", str(added))
    page.wait_for_selector('div[role="presentation"] textarea', timeout=10000)
    page.fill('div[role="presentation"] textarea', 'should be "shows" - subject-verb agreement')
    page.click('div[role="presentation"] button:has-text("Add")')
    page.wait_for_timeout(2000)
    body = page.inner_text("body")
    check("the note appears in the notes list", 'subject-verb agreement' in body, body[:0])
    saved = requests.get(f"{API}/submissions/{sub['id']}",headers=th,timeout=60).json()
    anns = saved.get("teacher_annotations") or []
    check("the note was persisted", len(anns) == 1, str(anns))
    if anns:
        check("it quotes the selected words", anns[0]["quoted_text"] == "show", str(anns[0]))
        check("it is stored as a correction", anns[0]["type"] == "correction")

    # ---- review it, then confirm it is still reachable afterwards ----
    page.fill('textarea[placeholder="Enter your feedback here..."]', 'Good effort overall.')
    page.fill('input[placeholder="e.g. 9.5"]', '8.5')
    page.click('button:has-text("Submit Feedback")')
    page.wait_for_timeout(3000)
    page.goto(f"{BASE}/submissions/{sub['id']}/review", wait_until="networkidle")
    page.wait_for_timeout(2500)
    body = page.inner_text("body")
    check("a reviewed submission is still viewable", "already been reviewed" not in body, body[:120])
    check("it opens read-only", "Reviewed Submission" in body, body[:160])
    check("it shows the feedback that was given", "Good effort overall." in body)
    check("the annotation is still there", "subject-verb agreement" in body)
    page.close()

    # ---- student: sees the teacher's note, and their own profile ----
    page=b.new_page(viewport={"width":1400,"height":950})
    login(page, smail)
    page.goto(f"{BASE}/submissions/{sub['id']}", wait_until="networkidle")
    page.wait_for_timeout(2500)
    body = page.inner_text("body")
    check("the student sees the teacher's note", "subject-verb agreement" in body, body[:0])
    page.goto(f"{BASE}/profile", wait_until="networkidle")
    page.wait_for_timeout(1500)
    body = page.inner_text("body")
    check("the student's profile names their teacher", f"pa{ts}t" in body, body[:200])
    check("the student's profile has the change-password button", "change password" in body.lower())
    check("the student's profile does not list other students", "My students" not in body)
    page.close()
    b.close()

print('\n'+('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
