"""Functional smoke test after wiring admission control into the three NN entry points:
submission, practice round, and /api/analysis/text. Checks they still work AND that the load
manager actually saw the work (so the slot is really being taken, not bypassed)."""
import base64, json, sys, time
import requests

BASE = "http://127.0.0.1"; API = f"{BASE}/api"; PW = "Password123"
ts = str(int(time.time()))[-6:]
fails = []
def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + (f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
before = requests.get(f"{BASE}/health/load", timeout=10).json()

t = requests.post(f"{API}/auth/register", json={"username": f"sm{ts}t", "email": f"sm{ts}t@e.com",
                  "password": PW, "role": "teacher"}, timeout=60).json()
th = {"Authorization": f"Bearer {t['access_token']}"}
code = requests.post(f"{API}/auth/generate-invitation", headers=th, timeout=60).json()["code"]
s = requests.post(f"{API}/auth/register", json={"username": f"sm{ts}s", "email": f"sm{ts}s@e.com",
                  "password": PW, "role": "student", "experiment_consent": True,
                  "invitation_code": code}, timeout=60).json()
sh = {"Authorization": f"Bearer {s['access_token']}"}
sid = s["user"]["id"]

tid = requests.post(f"{API}/tasks/", headers=th, data={"title": f"Smoke {ts}",
      "description": "Describe the chart."}, files={"image": ("c.png", png, "image/png")},
      timeout=60).json()["task"]["id"]
requests.post(f"{API}/tasks/{tid}/assign", headers=th, json={"student_ids": [sid]}, timeout=60)

essay = ("<p>The chart show the amount of money what was spend on food. "
         "Families was spending about 20 percent of their budget for vegetables.</p>")
r = requests.post(f"{API}/submissions/", headers=sh, json={"task_id": tid, "content": essay}, timeout=600)
check("submission accepted", r.status_code == 201, f"status={r.status_code} {r.text[:200]}")
sub = r.json()["submission"]
analysis = json.loads(sub["analysis_result"]) if isinstance(sub.get("analysis_result"), str) else sub.get("analysis_result")
sents = (analysis or {}).get("sentences", [])
check("analysis produced sentences", len(sents) >= 2, f"n={len(sents)}")
check("analysis found errors", sum(len(x.get("errant_edits", [])) for x in sents) > 0)

# error stats got logged for the STUDENT
stats = requests.get(f"{API}/stats/students/{sid}", headers=th, timeout=60)
check("error stats reachable", stats.status_code == 200, f"status={stats.status_code}")
if stats.status_code == 200:
    body = stats.json()
    tags = json.dumps(body)
    check("errors were logged against the student", '"count"' in tags or 'error' in tags, tags[:160])

# practice session on the first errored sentence
idx = next((x["id"] for x in sents if x.get("errant_edits")), None)
r = requests.post(f"{API}/practice/start", headers=sh,
                  json={"submission_id": sub["id"], "sentence_index": idx}, timeout=600)
check("practice session starts", r.status_code in (200, 201), f"status={r.status_code} {r.text[:200]}")
if r.status_code in (200, 201):
    body = r.json()
    sess = body.get("session", body)
    target = sess.get("target_corrected") or body.get("target")
    rr = requests.post(f"{API}/practice/{sess['id']}/submit", headers=sh,
                       json={"text": target or "The chart shows the money."}, timeout=600)
    check("practice round accepted", rr.status_code == 200, f"status={rr.status_code} {rr.text[:200]}")
    if rr.status_code == 200:
        check("rewriting the target resolves the round", rr.json().get("resolved") is True,
              str(rr.json().get("edits"))[:120])
        # a practice_item round runs the NN -> must go through a slot
        r2 = requests.post(f"{API}/practice/{sess['id']}/submit", headers=sh,
                           json={"text": "I has went to the shop yesterday."}, timeout=600)
        check("practice_item round accepted", r2.status_code == 200, f"status={r2.status_code}")

r = requests.post(f"{API}/analysis/text", headers=sh, json={"text": "He go to school every day."}, timeout=600)
check("analysis endpoint works", r.status_code == 200, f"status={r.status_code} {r.text[:150]}")

after = requests.get(f"{BASE}/health/load", timeout=10).json()
grew = after["completed"] - before["completed"]
# Three slots, not four: the 'rewrite_original' round is a pure string diff against a target the
# submission already computed, so by design it never touches the model. The slots are the
# submission, the practice_item round, and /api/analysis/text.
check("load manager counted every NN call", grew == 3, f"completed +{grew}")
check("no slots leaked", after["in_flight"] == 0, str(after))
print(f"\nload after: {json.dumps(after)}")
print('\n' + ('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
