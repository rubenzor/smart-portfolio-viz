import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
BACKEND_URL = BACKEND_URL.rstrip("/")  # evitar dobles //

API_BASE = f"{BACKEND_URL}/api/v1"


def api_get(path):
    return requests.get(API_BASE + path, timeout=15)

def api_post(path, **kwargs):
    return requests.post(API_BASE + path, timeout=15, **kwargs)

def api_patch(path, **kwargs):
    return requests.patch(API_BASE + path, timeout=15, **kwargs)

def api_put(path, **kwargs):
    return requests.put(API_BASE + path, timeout=15, **kwargs)