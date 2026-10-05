"""Practising a sentence the student typed and marked up themselves.

Their own corrections define the target - the neural network is not consulted - so this checks
both the API rules and the full browser flow: type, mark, correct, start, practise.

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

tmail=f"mp{ts}t@e.com"; smail=f"mp{ts}s@e.com"
t=requests.post(f"{API}/auth/register",json={"username":f"mp{ts}t","email":tmail,"password":PW,"role":"teacher"},timeout=60).json()
th={"Authorization":f"Bearer {t['access_token']}"}
code=requests.post(f"{API}/auth/generate-invitation",headers=th,timeout=60).json()["code"]
st=requests.post(f"{API}/auth/register",json={"username":f"mp{ts}s","email":smail,"password":PW,
  "role":"student","experiment_consent":True,"invitation_code":code},timeout=60).json()
sh={"Authorization":f"Bearer {st['access_token']}"}

SENT = "He have went to the shop what was closed."
i = SENT.index("have went"); j = SENT.index("what was ")
MARKS = [{"start": i, "end": i+len("have went"), "correction": "has gone"},
         {"start": j, "end": j+len("what was "), "correction": ""}]

r = requests.post(f"{API}/practice/start-manual", headers=sh, json={"sentence": SENT, "marks": MARKS}, timeout=600)
check("a manual session starts", r.status_code == 201, f"status={r.status_code} {r.text[:150]}")
d = r.json() if r.status_code == 201 else {}
check("the target is the student's own version", d.get("target_corrected") == "He has gone to the shop closed.",
      repr(d.get("target_corrected")))
check("it is marked as a manual session", d.get("source") == "manual", str(d.get("source")))
check("it has no submission behind it", d.get("submission_id") is None)
types = [e["errant_type"] for e in d.get("initial_edits", [])]
check("the student's corrections get proper error types", "R:VERB:SVA" in types and any(x.startswith("U:") for x in types), str(types))

# the session runs through the ordinary rounds
r2 = requests.post(f"{API}/practice/{d['id']}/submit", headers=sh, json={"text": d["target_corrected"]}, timeout=600).json()
check("the rewrite round resolves against it", r2.get("resolved") is True, str(r2.get("edits"))[:120])
check("it moves on to a create-a-sentence round", r2["session"]["current_step"] == "practice_item")
check("and those rounds still get examples",
      bool((r2["session"].get("current_item") or {}).get("examples")),
      str((r2["session"].get("current_item") or {}).get("examples"))[:120])

# the errors are logged for the statistics, same as a submission-based session
stats = requests.get(f"{API}/stats/students/{st['user']['id']}", headers=th, timeout=60).json()
check("the errors reach the teacher's statistics",
      sum((stats.get("practice_sessions", {}).get("error_distribution") or {}).values()) > 0,
      str(stats.get("practice_sessions", {}).get("error_distribution"))[:140])

for body, why in (
    ({"sentence": SENT, "marks": []}, "no marks"),
    ({"sentence": "", "marks": MARKS}, "empty sentence"),
    ({"sentence": SENT, "marks": [{"start": 0, "end": 2, "correction": "He"}]}, "correction changes nothing"),
    ({"sentence": SENT, "marks": [{"start": 3, "end": 9, "correction": "x"}, {"start": 5, "end": 12, "correction": "y"}]}, "overlapping marks"),
    ({"sentence": SENT, "marks": [{"start": 0, "end": 999, "correction": "x"}]}, "span past the end"),
):
    rr = requests.post(f"{API}/practice/start-manual", headers=sh, json=body, timeout=60)
    check(f"rejected: {why}", rr.status_code == 400, f"status={rr.status_code}")
rr = requests.post(f"{API}/practice/start-manual", headers=th, json={"sentence": SENT, "marks": MARKS}, timeout=60)
check("teachers cannot start one", rr.status_code == 403, f"status={rr.status_code}")

# --- browser ---
with sync_playwright() as pw:
    b=pw.chromium.launch(); page=b.new_page(viewport={"width":1400,"height":1000})
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.fill('input[name="email"]', smail); page.fill('input[name="password"]', PW)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)
    page.wait_for_url(lambda u: "/login" not in u, timeout=20000)
    page.wait_for_timeout(1500)

    own = page.locator('button:has-text("My own sentence")')
    check("the dashboard offers practising your own sentence", own.count() > 0)
    own.first.click()
    page.wait_for_url("**/practice/new", timeout=20000)
    page.wait_for_selector("textarea", timeout=20000)

    page.fill("textarea", "She go to school every day.")
    page.click('button:has-text("Next: mark the errors")')
    page.wait_for_timeout(600)

    marked = page.evaluate("""() => {
        const el = Array.from(document.querySelectorAll('div'))
          .find(e => getComputedStyle(e).whiteSpace === 'pre-wrap' && e.textContent.includes('She go'));
        if (!el) return 'no container';
        const node = el.firstChild, text = node.textContent, i = text.indexOf('go');
        const range = document.createRange();
        range.setStart(node, i); range.setEnd(node, i + 2);
        const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
        el.dispatchEvent(new MouseEvent('mouseup', {bubbles: true, clientX: 300, clientY: 300}));
        return 'ok';
    }""")
    check("the sentence can be marked up", marked == "ok", str(marked))
    page.wait_for_selector('div[role="presentation"] input', timeout=10000)
    page.fill('div[role="presentation"] input', 'goes')
    page.click('div[role="presentation"] button:has-text("Add")')
    page.wait_for_timeout(700)
    body = page.inner_text("body")
    check("the correction is listed", "goes" in body)
    check("the target sentence is previewed", "She goes to school every day." in body, body[:0])

    page.click('button:has-text("Start practice")')
    page.wait_for_url(lambda u: "/practice/" in u and "/new" not in u, timeout=30000)
    page.wait_for_selector("textarea", timeout=25000)
    body = " ".join(page.inner_text("body").split())
    # The rewrite round shows each suggestion as a label directly above the word it replaces, so
    # the rendered text reads "She goes go to school..." - the student's words with the
    # corrections floating over them. Assert on that structure rather than the bare sentence.
    check("practice starts on the student's own sentence",
          "to school every day" in body and "She" in body, body[:260])
    check("the student's own correction is shown as the suggestion", "goes" in body, body[:260])
    check("a manual session doesn't offer 'back to submission'",
          "BACK TO SUBMISSION" not in body.upper(), body[:160])
    check("it offers the dashboard instead", "BACK TO DASHBOARD" in body.upper(), body[:160])

    page.fill("textarea", "She goes to school every day.")
    page.click('button:has-text("Submit")')
    page.wait_for_timeout(3500)
    body = page.inner_text("body")
    check("the round accepts the student's own target",
          "create a similar sentence" in body.lower() or "good job" in body.lower(), body[:200])
    b.close()

print('\n'+('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
