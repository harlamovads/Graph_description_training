"""Gunicorn config for production.

Why these numbers, specifically:

* ONE worker. Each worker loads its own copy of the T5 + ELECTRA stack (~2.4 GB), so 2 workers
  would need ~5 GB of an 8 GB server before serving a single request. Concurrency comes from
  threads instead, which share the one model. (The HF-Spaces supervisord path still says
  --workers 2 --timeout 120; don't copy those numbers here.)
* gthread worker class, because the default sync worker ignores --threads.
* Many threads (72), but only a few analyses at a time. Threads used to be the only brake on
  neural-network concurrency, which meant 8 was both "how many analyses run at once" and "how
  many requests the app can hold" - so a class submitting together made the whole site
  unresponsive. backend/services/load_manager.py now bounds the analyses (3 at a time) on its
  own, so threads only need to be numerous enough to HOLD the waiting requests plus everyone
  else's page loads. A waiting request costs little more than its thread - it releases its DB
  connection before queueing - but the pool still has to cover the threads that ARE working;
  see SQLALCHEMY_ENGINE_OPTIONS in backend/config.py, sized against this number.
* A very long timeout. A submission runs the neural network inline and can legitimately take
  minutes when a class submits at once; the default 30 s would kill every one of them.
* Warm-up in post_worker_init, NOT at import. Loading the models before the worker accepts
  traffic is what stops a burst of first requests each building their own copy and OOMing the
  box. It runs inside the worker (rather than via preload_app) to avoid forking a process that
  already has PyTorch's thread pools running.
"""
import os

bind = f"0.0.0.0:{os.environ.get('PORT', '5001')}"

workers = int(os.environ.get('GUNICORN_WORKERS', '1'))
worker_class = 'gthread'
threads = int(os.environ.get('GUNICORN_THREADS', '72'))

timeout = int(os.environ.get('GUNICORN_TIMEOUT', '1800'))
graceful_timeout = 60
keepalive = 5

accesslog = '-'
errorlog = '-'
loglevel = os.environ.get('GUNICORN_LOGLEVEL', 'info')


def post_worker_init(worker):
    """Load the NN + ERRANT before this worker serves anything."""
    try:
        from app import app
        with app.app_context():
            from backend.services.neural_network_service import get_model, configure_cpu_threads
            from backend.services import errant_service
            configure_cpu_threads()
            worker.log.info("Warming up neural network and ERRANT ...")
            get_model()
            errant_service.get_annotator()
            worker.log.info("Models ready.")
    except Exception as exc:
        worker.log.warning(f"Model warm-up failed ({exc}); will load on first request.")
