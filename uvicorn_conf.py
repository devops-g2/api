from uvicorn.workers import UvicornWorker

bind = "0.0.0.0:8000"
workers = 4
worker_class = UvicornWorker
