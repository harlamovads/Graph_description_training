# Deploying to the VPS

Written for whoever administers the server — you, or a colleague with root on the box and no
prior knowledge of this codebase.

Target hardware: **8 GB RAM, 4-6 cores, 60-80 GB SSD/NVMe, KVM.** Everything below is measured
against that; §7 has the numbers and what to change if you have 6 cores rather than 4.

**Which Ubuntu?** Use **24.04 LTS**. The host OS barely matters here - the application, Python,
and every library it needs live inside containers, so the host only provides Docker, swap and a
firewall. That makes maturity worth more than a longer support runway: 24.04 is what Docker's
repository and essentially every guide assume. A newer release is fine too, with one thing to
check first (see below).

---

## 1. What you are deploying

Three containers, managed by one `docker compose` project:

| Container | Role | Notes |
|---|---|---|
| `nginx` | the only thing listening on the public internet (80/443) | terminates TLS, proxies everything to the app |
| `language-learning-app` | Flask + gunicorn, and the T5/ELECTRA grammar models | not published to the host at all; nginx reaches it over the compose network |
| `postgres` | the database | data lives in the `postgres_data` volume |

The app is a single gunicorn worker with 72 threads. One worker on purpose: each worker loads
its own ~2.4 GB copy of the models, so two workers would need ~5 GB before serving a single
request. Concurrency comes from threads, which share the one copy.

Expect **~2.5 GB resident when idle** and **~4.1 GB under a full class submitting at once**.

## 2. Prepare the server

If you chose an Ubuntu release newer than 24.04, check that Docker publishes packages for it
before running the block below - the line that adds Docker's repository derives the release
codename from the system, and if Docker has no directory for that codename yet, `apt update`
fails with a 404:

```bash
. /etc/os-release && echo "$VERSION_CODENAME" \
  && curl -sfI "https://download.docker.com/linux/ubuntu/dists/$VERSION_CODENAME/Release" \
     >/dev/null && echo "Docker publishes for this release" || echo "Docker does NOT yet publish for this release - use 24.04"
```

```bash
# as root
apt update && apt upgrade -y
apt install -y ca-certificates curl git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt update && apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

**Add swap.** The box has 8 GB and no swap by default. Swap is not there to be used — it is
there so that a brief spike degrades into slowness instead of the kernel killing Postgres:

```bash
fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

**Firewall.** Only 22, 80 and 443 need to be open. Postgres is published to the host on 5433 by
`docker-compose.yml`; if you do not need to connect to it from outside, delete that `ports:`
block, and in any case do not let the firewall expose it:

```bash
ufw allow 22 && ufw allow 80 && ufw allow 443 && ufw enable
```

## 3. Get the code and write the secrets

```bash
cd /opt
git clone <your-repo-url> language_learning_app
cd language_learning_app
```

Create `.env` in this directory. **The stack refuses to start without the first two** — that is
deliberate, so a real deployment can never silently run on a placeholder key that is committed
to the repository (anyone with repo access could otherwise forge a login token for any account):

```bash
cat > .env <<EOF
SECRET_KEY=$(openssl rand -hex 32)
JWT_SECRET_KEY=$(openssl rand -hex 32)
CORS_ORIGINS=https://your.domain
DEEPSEEK_API_KEY=
EOF
chmod 600 .env
```

* `CORS_ORIGINS` — comma-separated list of the origins the browser will load the app from. Set
  it to your real domain before going live; a wrong value shows up as requests failing in the
  browser console with a CORS error while `curl` works fine.
* `DEEPSEEK_API_KEY` — optional. It generates example sentences in practice sessions. Leave it
  blank and practice still works, just without examples.
* Change the Postgres password in `docker-compose.yml` from `app_password` while you are here,
  and keep `.env` out of git (it already is).

`.env.template` lists every other variable, including the capacity knobs in §7.

## 4. First start

```bash
docker compose build          # 15-40 min: it downloads the grammar models into the image
docker compose up -d
docker compose logs -f language-learning-app
```

On every start the container waits for Postgres, applies pending migrations (`flask db upgrade`),
seeds sample data **only if the database is empty**, then loads the models before accepting
traffic. Wait for `Models ready.` — roughly 1-2 minutes.

Check it:

```bash
curl -s localhost/health          # {"status":"healthy"}
curl -s localhost/health/load     # the live load picture, see §7
```

Then open `http://your.server.ip/` in a browser, register the first **teacher** account through
the normal sign-up form, and from the teacher dashboard generate the invitation code students
will use to register. Each teacher has one permanent code; students who sign up with it are
attached to that teacher.

## 5. HTTPS

Point an A record at the server first — certbot proves you own the domain over port 80, which is
already wired up (`/.well-known/acme-challenge/` is served from the `certbot_www` volume).

```bash
docker compose run --rm --entrypoint "" \
  -v language_learning_app_certbot_www:/var/www/certbot \
  -v language_learning_app_certbot_conf:/etc/letsencrypt \
  certbot/certbot certonly --webroot -w /var/www/certbot \
  -d your.domain --email you@example.com --agree-tos --no-eff-email
```

Then in `docker/nginx.conf`: uncomment the 443 server block, replace `your.domain` in it (three
places), and add a redirect from 80 to 443. Uncomment `- "443:443"` in `docker-compose.yml`, set
`CORS_ORIGINS=https://your.domain` in `.env`, and `docker compose up -d`.

The 443 block contains an HSTS header. Leave it commented until you have confirmed HTTPS works —
once a browser has seen HSTS it refuses to load the site over HTTP, including to fix a mistake.

Renewal, as a weekly root cron entry:

```
0 3 * * 1 cd /opt/language_learning_app && docker compose run --rm --entrypoint "" -v language_learning_app_certbot_www:/var/www/certbot -v language_learning_app_certbot_conf:/etc/letsencrypt certbot/certbot renew --webroot -w /var/www/certbot --quiet && docker compose exec nginx nginx -s reload
```

## 6. Updating, and backups

```bash
cd /opt/language_learning_app
git pull
docker compose up -d --build
```

The server needs no Node: the built frontend (`backend/static/`) is committed to the repository,
so `git pull` brings it with everything else. Rebuilding it is a step on the **developer's**
machine, before committing:

```bash
cd frontend && npm ci && CI=false npm run build && cd ..
rsync -a --delete frontend/build/ backend/static/     # then commit backend/static/
```

Migrations apply themselves on start. Students see a few minutes of downtime while the models
reload — do it outside class hours.

**Reclaim disk after updating.** Each rebuild leaves the previous image (~3.6 GB) and a build
cache behind, and neither is removed automatically. On a 60 GB disk several months of updates
would eventually fill it — this is the only realistic way this application runs out of space:

```bash
docker image prune -f        # delete images no container uses
docker builder prune -f      # delete the build cache
df -h /                      # check where you stand
```

**Back up two things** — the database and the uploaded task images. Neither survives losing the
server on its own:

```bash
# database
docker compose exec -T postgres pg_dump -U app_user language_learning_app | gzip > /root/backups/db-$(date +%F).sql.gz
# uploaded images
docker run --rm -v language_learning_app_app_uploads:/data -v /root/backups:/out alpine \
  tar czf /out/uploads-$(date +%F).tar.gz -C /data .
```

Put that in a daily cron job and copy the files off the machine. To restore a dump:
`gunzip -c db-….sql.gz | docker compose exec -T postgres psql -U app_user language_learning_app`.

## 7. Capacity, and what to do when it is reached

The grammar model is the only expensive thing the app does: about **4 seconds of CPU per
submission**, and it uses all four cores. So the app deliberately runs only a few analyses at a
time (`MAX_CONCURRENT_ANALYSES=3`), queues the rest (`MAX_QUEUED_ANALYSES=60`), and answers
`503` with a `Retry-After` header once the queue is full, rather than letting everything pile up.

Measured in a container capped to exactly this hardware:

| Students pressing Submit at the same instant | Result | App memory peak |
|---|---|---|
| 20 | all 20 succeed, the last after 28 s | 3.1 GB |
| 40 | all 40 succeed, the last after 56 s | 3.9 GB |
| 60 | all 60 succeed, the last after 82 s | 4.1 GB |
| 80 | 63 succeed (85 s); the other 17 get an immediate, polite "the server is busy, try again in a few minutes - nothing has been lost". Nothing crashed, no worker was killed, no request hung. | 4.6 GB |

So: **a class of 20-30 is comfortable, 60 at the same instant all get served, and past that the
app sheds load on purpose instead of falling over.** The shed threshold is a setting
(`MAX_QUEUED_ANALYSES`), not a hardware limit — memory was still under 5 GB of 8 GB at 80.

While 57 submissions were queued, ordinary page loads still answered in **10 ms**. That is the
point of the design: a queue of essays must not make the rest of the site feel dead.

Watch it live (no authentication needed, and it exposes no student data):

```bash
curl -s localhost/health/load
# level: ok | busy | overloaded
# in_flight / queued / capacity / queue_limit, peaks, refused, avg_work_seconds, avg_wait_seconds
```

### Disk

Measured on a running instance: the application image is **3.6 GB**, the database **11 MB** after
573 submissions / 838 accounts / 7,481 logged errors, and uploaded task images under 1 MB. Steady
state including the OS is roughly **15 GB**. Student data grows at a few MB per thousand
submissions, so it is not what fills a disk — stale Docker images are (see §6).

### Network bandwidth

The app is CPU-bound, not network-bound, and this is not close. Measured page weight: **444 KB
gzipped** for the whole frontend (cached permanently afterwards, since the filenames carry a
content hash), plus the task image, plus a few KB of JSON per action. A class of 30 arriving at
once on a first-ever visit moves about 29 MB — **1.2 s on a 200 Mbit/s link** — and about half
that on any later day, when only the images are fetched. Monthly traffic for 30 active students
is a few hundred MB, against the provider's typical 1 TB quota.

So **200 Mbit/s is ample**; the same money is far better spent on cores, which is what actually
limits how fast a class gets its feedback (4 s of CPU per submission). Revisit only if the app
ever starts serving audio or video.

### If the server has 6 cores rather than 4

The neural network runs single-threaded per analysis by default, which is correct on 4 cores
(3 analyses already fill them) but leaves the extra cores of a 6-core box idle. Measured on a
6-core budget:

| Setting | 20 students at once | one student submitting alone |
|---|---|---|
| `MAX_CONCURRENT_ANALYSES=3`, `TORCH_NUM_THREADS=1` (the 4-core default) | 30.2 s | 3.5 s |
| `MAX_CONCURRENT_ANALYSES=5`, `TORCH_NUM_THREADS=1` | 27.7 s | - |
| **`MAX_CONCURRENT_ANALYSES=3`, `TORCH_NUM_THREADS=2`** | **26.0 s** | **~2.2 s** |

So on 6 cores, put `TORCH_NUM_THREADS=2` in `.env` and leave the concurrency at 3. The everyday
case - one student pressing Submit with nobody else waiting - is what improves most, and that is
the wait students actually notice. Keep
`MAX_CONCURRENT_ANALYSES x TORCH_NUM_THREADS` at or below the core count.

Tuning, all via `.env` (see `.env.template` for the full list):

* More RAM or cores? Raise `MAX_CONCURRENT_ANALYSES` — but only up to about the core count.
  Above that, throughput stops improving and every student just waits longer.
* Bigger classes? Raise `MAX_QUEUED_ANALYSES`, and keep `GUNICORN_THREADS` comfortably above it
  (a waiting request holds a thread). `DB_POOL_SIZE + DB_MAX_OVERFLOW` must stay under
  Postgres' `max_connections`, which defaults to 100.
* Students seeing "server is busy" during a normal lesson means the queue limit is too low for
  how you actually use it, not that the server is failing.

## 8. Troubleshooting

| Symptom | Cause and fix |
|---|---|
| `502 Bad Gateway` right after a deploy | The app is still loading models (1-2 min). `docker compose logs language-learning-app` and wait for `Models ready.` If it persists, nginx may have cached a dead container IP — `docker compose restart nginx`. (The config resolves the app through Docker's DNS every 10 s specifically to avoid this, so it should heal itself.) |
| Students get "server is busy" | Working as designed, at capacity. See §7. |
| `429 Too Many Requests` on login | Ten failed logins for one account in 5 minutes locks that account's login for the rest of the window. It clears by itself. A teacher can reset a student's password from the student's row in the statistics page. |
| Task images stopped appearing | They live in the `app_uploads` volume. Check `UPLOAD_FOLDER=/app/uploads` is still set in `docker-compose.yml` — without it the app writes into the container's own filesystem and the images vanish on the next rebuild. |
| App restarting in a loop, `Killed` in the logs | Out of memory. Confirm swap exists (§2) and that nothing else large runs on the box. The app's limit is 6.5 GB of the 8 GB on purpose, so that Postgres and the OS keep theirs. |
| A student forgot their password | Their teacher resets it from the statistics page and hands them a one-time temporary password; the student sets their own from the account menu. There is no admin backdoor by design. |
| Migrations failed on start | `docker compose logs language-learning-app`, fix the cause, then `docker compose exec language-learning-app flask db upgrade`. Never edit the database by hand to "get past" a migration. |

## 9. Sanity checks you can re-run on the server

These live in the repository root and talk to a running stack:

```bash
python test_load_manager.py    # the admission-control logic, no app needed
python test_load_smoke.py      # end-to-end: submit, practice, analyse, error stats
python test_task_edit.py       # task editing permissions, and the change-password dialog
python test_task_edit_ui.py    # the same two flows in a browser (needs playwright, optional)
python test_practice_ui.py     # the practice round as a student sees it (needs playwright)
python test_profile_annotations_ui.py  # profile, past submissions, teacher annotations (playwright)
python test_student_background_ui.py   # the student background fields (playwright)
python test_manual_practice_ui.py      # practising a sentence the student typed (playwright)
python test_teacher_sees_manual_practice_ui.py  # the teacher's view of those sessions (playwright)
```
