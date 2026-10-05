"""Unit checks for the admission-control logic, without the app or the model."""
import os, sys, threading, time
os.environ.update(MAX_CONCURRENT_ANALYSES='3', MAX_QUEUED_ANALYSES='12', ANALYSIS_QUEUE_TIMEOUT='2')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.services.load_manager import LoadManager, AtCapacity, MAX_CONCURRENT, MAX_QUEUED

fails = []
def check(name, cond, extra=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + (f'   {extra}' if extra else ''))
    if not cond: fails.append(name)

m = LoadManager()

# 1. snapshot() must not deadlock (the bug the 504 exposed).
done = threading.Event()
threading.Thread(target=lambda: (m.snapshot(), done.set()), daemon=True).start()
check('snapshot() returns without deadlocking', done.wait(3))

# 2. Never more than MAX_CONCURRENT inside the slot at once.
observed_max = [0]
lk = threading.Lock(); live = [0]
def work():
    with m.slot():
        with lk:
            live[0] += 1; observed_max[0] = max(observed_max[0], live[0])
        time.sleep(0.25)
        with lk: live[0] -= 1
ts = [threading.Thread(target=work) for _ in range(MAX_CONCURRENT * 3)]
[t.start() for t in ts]; [t.join() for t in ts]
check('concurrency is capped', observed_max[0] == MAX_CONCURRENT, f'peak={observed_max[0]} cap={MAX_CONCURRENT}')
check('all slots released after the burst', m.snapshot()['in_flight'] == 0)

# 3. An exception inside the slot must still release it.
m2 = LoadManager()
for _ in range(MAX_CONCURRENT + 2):
    try:
        with m2.slot():
            raise RuntimeError('boom')
    except RuntimeError:
        pass
check('a slot survives an exception in the body', m2.snapshot()['in_flight'] == 0)
ok = []
def probe():
    with m2.slot():
        ok.append(True)
t = threading.Thread(target=probe, daemon=True)
t.start(); t.join(2)
check('capacity is intact after exceptions', bool(ok))

# 4. Refuse (not hang) once the queue is full.
m3 = LoadManager()
hold = threading.Event()
def blocker():
    with m3.slot():
        hold.wait(10)
for _ in range(MAX_CONCURRENT + MAX_QUEUED):
    threading.Thread(target=blocker, daemon=True).start()
time.sleep(0.5)
refused = None
try:
    with m3.slot():
        pass
except AtCapacity as e:
    refused = e
check('refuses with AtCapacity when the queue is full', refused is not None)
if refused:
    check('refusal carries a Retry-After', refused.retry_after >= 5, f'retry_after={refused.retry_after}')
    check('refusal carries a snapshot', refused.snapshot.get('queued') == MAX_QUEUED, str(refused.snapshot))
hold.set(); time.sleep(0.5)

# 5. Waiting longer than the timeout is refused, not held forever.
m4 = LoadManager()
stuck = threading.Event()
def occupy():
    with m4.slot():
        stuck.wait(30)
for _ in range(MAX_CONCURRENT):
    threading.Thread(target=occupy, daemon=True).start()
time.sleep(0.3)
t0 = time.time(); timed_out = False
try:
    with m4.slot():
        pass
except AtCapacity:
    timed_out = True
waited = time.time() - t0
check('gives up after ANALYSIS_QUEUE_TIMEOUT', timed_out and 1.5 < waited < 5, f'waited={waited:.1f}s')
stuck.set()

print('\n' + ('ALL PASS' if not fails else f'FAILURES: {fails}'))
sys.exit(1 if fails else 0)
