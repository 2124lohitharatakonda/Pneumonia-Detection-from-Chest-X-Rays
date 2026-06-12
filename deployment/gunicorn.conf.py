# ============================================================
# Gunicorn configuration for PneumoDetect (Linux/Mac)
# Usage: gunicorn -c deployment/gunicorn.conf.py wsgi:app
# ============================================================
import multiprocessing

# Bind address and port
bind = "0.0.0.0:5000"

# Number of worker processes
# Rule of thumb: (2 x CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class — use sync for TF model (thread-safety)
worker_class = "sync"

# Timeout: ML inference can take several seconds
timeout = 120

# Keep-alive connections
keepalive = 5

# Logging
accesslog = "logs/gunicorn_access.log"
errorlog  = "logs/gunicorn_error.log"
loglevel  = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# Restart workers after this many requests (memory leak protection)
max_requests = 1000
max_requests_jitter = 100

# Preload app (loads TF model once in master, shared with workers via fork)
preload_app = True
