"""
Gunicorn configuration file
"""
import os
import json

# Load config from config.json if it exists
config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
host = "0.0.0.0"
port = 5000

if os.path.exists(config_file):
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            host = config.get('host', host)
            port = config.get('port', port)
    except Exception:
        pass

# Gunicorn configuration
bind = f"{host}:{port}"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 30
keepalive = 2
preload_app = True
daemon = False

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'