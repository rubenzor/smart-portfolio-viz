import os
import requests

API_BASE = os.getenv("API_BASE", "http://backend:8000/api/v1")

def api_get(path):
    return requests.get(API_BASE + path, timeout=15)

def api_post(path, **kwargs):
    return requests.post(API_BASE + path, timeout=15, **kwargs)

def api_patch(path, **kwargs):
    return requests.patch(API_BASE + path, timeout=15, **kwargs)

def api_put(path, **kwargs):
    return requests.put(API_BASE + path, timeout=15, **kwargs)