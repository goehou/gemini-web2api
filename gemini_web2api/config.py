"""Configuration management."""
import json
import os

DEFAULT_CONFIG = {
    "port": 8081,
    "host": "0.0.0.0",
    "retry_attempts": 3,
    "retry_delay_sec": 2,
    "request_timeout_sec": 180,
    "gemini_bl": "boq_assistant-bard-web-server_20260716.08_p0",
    "auth_user": None,
    "xsrf_token": None,
    "default_model": "gemini-3.6-flash",
    "log_requests": True,
    "cookie_file": None,
    "proxy": None,
    "cache_db_path": "./gemini-web2api-cache.sqlite3",
    "cache_default_ttl_sec": 3600,
    "cache_max_ttl_sec": 604800,
    "auto_cache": True,
    "api_keys": [],
    "temporary_chats": False,
    "session_hashes": {},
}

CONFIG = dict(DEFAULT_CONFIG)

_ENV_KEYS = {
    "PORT": "port", "HOST": "host", "COOKIE_FILE": "cookie_file",
    "PROXY": "proxy", "GEMINI_BL": "gemini_bl", "XSRF_TOKEN": "xsrf_token",
    "AUTH_USER": "auth_user", "DEFAULT_MODEL": "default_model",
    "API_KEYS": "api_keys", "LOG_REQUESTS": "log_requests",
    "TEMPORARY_CHATS": "temporary_chats", "RETRY_ATTEMPTS": "retry_attempts",
    "RETRY_DELAY_SEC": "retry_delay_sec", "REQUEST_TIMEOUT_SEC": "request_timeout_sec",
}
_ENV_INT = {"port", "retry_attempts", "retry_delay_sec", "request_timeout_sec"}
_ENV_BOOL = {"log_requests", "temporary_chats"}
_ENV_NULLABLE = {"cookie_file", "proxy", "xsrf_token", "auth_user"}


def load_env(path: str):
    """Load KEY=VALUE overrides from a .env-style file onto CONFIG."""
    if not path or not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            field = _ENV_KEYS.get(key.strip().upper())
            if not field:
                continue
            val = val.strip().strip('"').strip("'")
            if field in _ENV_INT:
                CONFIG[field] = int(val)
            elif field in _ENV_BOOL:
                CONFIG[field] = val.lower() in ("1", "true", "yes", "on")
            elif field == "api_keys":
                CONFIG[field] = [k.strip() for k in val.split(",") if k.strip()]
            elif field in _ENV_NULLABLE:
                CONFIG[field] = val or None
            elif val:
                CONFIG[field] = val


def load_config(path: str = None):
    """Load config from JSON file."""
    if path and os.path.exists(path):
        with open(path) as f:
            CONFIG.update(json.load(f))
    return CONFIG


def find_config():
    """Search for config file in standard locations."""
    for p in ["./config.json", os.path.expanduser("~/.config/gemini-web2api/config.json")]:
        if os.path.exists(p):
            return p
    return None
