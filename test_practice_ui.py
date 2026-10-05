"""Browser test for the practice page as a student sees it: no standing copy/paste notice (but
pasting still blocked), a deleted span shown struck through rather than labelled "remove",
DeepSeek examples present, and feedback worded for the round it belongs to.

Needs playwright (pip install playwright && playwright install chromium).
"""
import base64, json, re, sys, time
import requests
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1"; API=f"{BASE}/api"; PW="Password123"
ts=str(int(time.time()))[-6:]
fails=[]
def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ')+name+(f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

png=base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
t=requests.post(f"{API}/auth/register",json={"username":f"up{ts}t","email":f"up{ts}t@e.com","password":PW,"role":"teacher"},timeout=60).json()
th={"Authorization":f"Bearer {t['access_token']}"}
code=requests.post(f"{API}/auth/generate-invitation",headers=th,timeout=60).json()["code"]
mail=f"up{ts}s@e.com"
s=requests.post(f"{API}/auth/register",json={"username":f"up{ts}s","email":mail,"password":PW,
  "role":"student","experiment_consent":True,"invitation_code":code},timeout=60).json()
sh={"Authorization":f"Bearer {s['access_token']}"}
tid=requests.post(f"{API}/tasks/",headers=th,data={"title":f"UP {ts}","description":"d"},
   files={"image":("c.png",png,"image/png")},timeout=60).json()["task"]["id"]
requests.post(f"{API}/tasks/{tid}/assign",headers=th,json={"student_ids":[s["user"]["id"]]},timeout=60)
essay="<p>The chart show the amount of money what was spend on food.</p>"
sub=requests.post(f"{API}/submissions/",headers=sh,json={"task_id":tid,"content":essay},timeout=600).json()["submission"]
an=sub["analysis_result"]; an=json.loads(an) if isinstance(an,str) else an
sent=next(x for x in an["sentences"] if x.get("errant_edits"))
sess=requests.post(f"{API}/practice/start",headers=sh,
    json={"submission_id":sub["id"],"sentence_index":sent["id"]},timeout=600).json()
sid=sess.get("session",sess)["id"]
deletions=[e for e in sent["errant_edits"] if not e.get("corrected_text")]
print("deletion edits in the original:", [e.get("original_text") for e in deletions])

with sync_playwright() as pw:
    b=pw.chromium.launch(); page=b.new_page()
    page.goto(f"{BASE}/login", wait_until="networkidle")
    page.fill('input[name="email"]', mail); page.fill('input[name="password"]', PW)
    page.click('button[type="submit"]')
    page.wait_for_function("() => !!localStorage.getItem('token')", timeout=20000)
    page.goto(f"{BASE}/practice/{sid}", wait_until="networkidle")
    page.wait_for_selector("textarea", timeout=20000)

    # 1. the copy/paste notice is gone
    body = page.inner_text("body")
    check("the copy/paste notice is gone", "Copy and paste are disabled" not in body)

    # 2. a deletion is shown struck through, not labelled "remove"
    if deletions:
        struck = page.evaluate("""() => Array.from(document.querySelectorAll('span,div'))
            .filter(e => getComputedStyle(e).textDecorationLine === 'line-through')
            .map(e => e.textContent.trim()).filter(t => t.length && t.length < 60)""")
        check("no 'remove' label on the page", "remove" not in body.lower(), body[:0])
        check("the deleted span is shown struck through", len(struck) > 0, f"struck={struck}")
        check("the struck text is the error span itself",
              any(d.get("original_text","").strip() and d["original_text"].strip() in " ".join(struck)
                  for d in deletions), f"struck={struck} vs {[d.get('original_text') for d in deletions]}")

    # paste really is still blocked even though the notice is gone
    page.fill("textarea", "")
    page.evaluate("""() => { const ta = document.querySelector('textarea');
        const dt = new DataTransfer(); dt.setData('text/plain', 'pasted text');
        ta.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true})); }""")
    page.wait_for_timeout(400)
    check("pasting is still blocked", page.input_value("textarea") == "",
          repr(page.input_value("textarea")))

    # 3. rewrite the original -> reach a "create a sentence" round, then submit a flawed sentence
    page.fill("textarea", sent["corrected"])
    page.click('button:has-text("Submit")')
    page.wait_for_timeout(3000)
    check("reached the create-a-sentence round", "create a similar sentence" in page.inner_text("body").lower(),
          page.inner_text("body")[:140].replace("\n"," | "))
    ex = page.inner_text("body")
    check("example sentences are shown", "Example sentences for inspiration" in ex)

    page.fill("textarea", "The report show the number of cars.")
    page.click('button:has-text("Submit")')
    page.wait_for_timeout(8000)
    body = page.inner_text("body")
    check("the new-sentence feedback is not the 'target' wording",
          "difference between what you wrote and the target" not in body)
    check("it says the sentence itself needs fixing",
          "still has something to fix" in body, body[:200].replace("\n"," | "))
    b.close()

print('\n'+('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
