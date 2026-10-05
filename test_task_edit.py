"""Covers two fixes:
  * PUT /api/tasks/<id> - the creator edits in place, another teacher gets a fork, and a task
    that is neither yours nor shared stays off limits.
  * a wrong current password on change-password must not look like an expired session.
Run against a running stack: python test_task_edit.py
"""
import base64, os, sys, time
import requests

BASE = os.environ.get("BASE_URL", "http://127.0.0.1")
API = f"{BASE}/api"
PW = "Password123"
ts = str(int(time.time()))[-6:]
fails = []

def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + (f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

png = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")

def teacher(tag):
    r = requests.post(f"{API}/auth/register", json={"username": f"te{ts}{tag}",
        "email": f"te{ts}{tag}@e.com", "password": PW, "role": "teacher"}, timeout=60).json()
    return {"Authorization": f"Bearer {r['access_token']}"}, r["user"]["id"], r["access_token"]

ha, ida, _ = teacher("a")
hb, idb, _ = teacher("b")

def make_task(h, title, shared):
    return requests.post(f"{API}/tasks/", headers=h,
        data={"title": title, "description": "Original description.",
              "is_from_database": "true" if shared else "false"},
        files={"image": ("c.png", png, "image/png")}, timeout=60).json()["task"]

shared = make_task(ha, f"Shared {ts}", True)
private = make_task(ha, f"Private {ts}", False)

# --- the creator edits in place ---
r = requests.put(f"{API}/tasks/{shared['id']}", headers=ha,
                 data={"title": "Edited by owner", "description": "New description."},
                 files={}, timeout=60)
check("creator can edit a shared task", r.status_code == 200, f"status={r.status_code} {r.text[:120]}")
if r.status_code == 200:
    body = r.json()
    check("edit in place is not a fork", body.get("forked") is False)
    check("same task id", body["task"]["id"] == shared["id"])
    check("title changed", body["task"]["title"] == "Edited by owner")
    check("image kept when none uploaded", body["task"]["image_url"] == shared["image_url"])
    check("stays in the shared database", body["task"]["is_from_database"] is True)

# --- another teacher forks instead ---
check("another teacher can open a shared task",
      requests.get(f"{API}/tasks/{shared['id']}", headers=hb, timeout=60).status_code == 200)
r = requests.put(f"{API}/tasks/{shared['id']}", headers=hb,
                 data={"title": "Edited by teacher B", "description": "B's description."},
                 files={}, timeout=60)
check("editing someone else's shared task forks it", r.status_code == 201,
      f"status={r.status_code} {r.text[:160]}")
if r.status_code == 201:
    body = r.json()
    copy = body["task"]
    check("response says it forked", body.get("forked") is True)
    check("the copy is a new task", copy["id"] != shared["id"])
    check("the copy belongs to the editor", copy["creator_id"] == idb)
    check("the copy has the edits", copy["title"] == "Edited by teacher B")
    check("the copy is private by default", copy["is_from_database"] is False)
    check("the copy has its own image file", copy["image_url"] != shared["image_url"],
          f"{copy['image_url']} vs {shared['image_url']}")
    img = requests.get(f"{BASE}{copy['image_url']}", timeout=60)
    check("the copied image is actually served", img.status_code == 200 and len(img.content) > 0,
          f"status={img.status_code}")
    orig = requests.get(f"{API}/tasks/{shared['id']}", headers=ha, timeout=60).json()
    check("the original is untouched", orig["title"] == "Edited by owner", orig["title"])

# --- a private task of someone else's is off limits ---
r = requests.put(f"{API}/tasks/{private['id']}", headers=hb,
                 data={"title": "Should not work", "description": "nope"}, files={}, timeout=60)
check("cannot edit another teacher's private task", r.status_code == 403, f"status={r.status_code}")

# --- students cannot edit tasks at all ---
code = requests.post(f"{API}/auth/generate-invitation", headers=ha, timeout=60).json()["code"]
st = requests.post(f"{API}/auth/register", json={"username": f"st{ts}", "email": f"st{ts}@e.com",
     "password": PW, "role": "student", "experiment_consent": True,
     "invitation_code": code}, timeout=60).json()
sh = {"Authorization": f"Bearer {st['access_token']}"}
r = requests.put(f"{API}/tasks/{shared['id']}", headers=sh,
                 data={"title": "student edit", "description": "nope"}, files={}, timeout=60)
check("students cannot edit tasks", r.status_code == 403, f"status={r.status_code}")

# --- validation still applies ---
r = requests.put(f"{API}/tasks/{shared['id']}", headers=ha,
                 data={"title": "   ", "description": "x"}, files={}, timeout=60)
check("blank title rejected", r.status_code == 400, f"status={r.status_code}")

# --- wrong current password must not look like an expired session ---
r = requests.post(f"{API}/auth/change-password", headers=sh,
                  json={"current_password": "WrongPassword1", "new_password": "Brandnew123"},
                  timeout=60)
check("wrong current password is 400, not 401", r.status_code == 400, f"status={r.status_code}")
check("and says why", "incorrect" in r.text.lower(), r.text[:120])
still = requests.get(f"{API}/tasks/", headers=sh, timeout=60)
check("the session still works afterwards", still.status_code == 200, f"status={still.status_code}")

r = requests.post(f"{API}/auth/change-password", headers=sh,
                  json={"current_password": PW, "new_password": "Brandnew123"}, timeout=60)
check("a correct current password still changes it", r.status_code == 200, f"status={r.status_code}")
r = requests.post(f"{API}/auth/login", json={"email": f"st{ts}@e.com", "password": "Brandnew123"}, timeout=60)
check("the new password logs in", r.status_code == 200, f"status={r.status_code}")

print('\n' + ('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
