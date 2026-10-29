import os

bind = "0.0.0.0:" + os.getenv("PORT", "8000")
workers = int(os.getenv("WEB_CONCURRENCY", "2"))
threads = int(os.getenv("GUNICORN_THREADS", "4"))
worker_class = "gthread"
timeout = 60
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
capture_output = True
max_requests = 1000
max_requests_jitter = 100
