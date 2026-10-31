"""Giriş: tək istifadəçi parolu + HMAC imzalı cookie.

MONTAJ_PASSWORD      — giriş parolu (və ya MONTAJ_PASSWORD_SHA256 — parolun sha256 hex-i)
MONTAJ_SECRET        — cookie imza açarı (verilməsə data qovluğunda təsadüfi yaradılır)
MONTAJ_AUTH=off      — yalnız lokal test üçün girişi söndürür
MONTAJ_COOKIE_SECURE — 1 (susmaya görə) HTTPS arxasında Secure cookie
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import threading
import time

from montaj.config import data_dir

COOKIE = "montaj_sess"
TTL = 60 * 60 * 24 * 30
_fail: dict[str, list[float]] = {}
_lock = threading.Lock()


def enabled() -> bool:
    return os.environ.get("MONTAJ_AUTH", "on").lower() not in ("off", "0", "false")


def configured() -> bool:
    return bool(os.environ.get("MONTAJ_PASSWORD") or os.environ.get("MONTAJ_PASSWORD_SHA256"))


def _secret() -> bytes:
    s = os.environ.get("MONTAJ_SECRET")
    if s:
        return s.encode()
    f = data_dir() / ".secret"
    if not f.exists():
        f.write_text(secrets.token_hex(32))
        os.chmod(f, 0o600)
    return f.read_text().strip().encode()


def check_password(pw: str) -> bool:
    want = os.environ.get("MONTAJ_PASSWORD_SHA256")
    if want:
        return hmac.compare_digest(hashlib.sha256(pw.encode()).hexdigest(), want.lower())
    real = os.environ.get("MONTAJ_PASSWORD", "")
    return bool(real) and hmac.compare_digest(pw.encode(), real.encode())


def rate_limited(ip: str) -> bool:
    now = time.time()
    with _lock:
        hist = [t for t in _fail.get(ip, []) if now - t < 600]
        _fail[ip] = hist
        return len(hist) >= 10


def record_fail(ip: str) -> None:
    with _lock:
        _fail.setdefault(ip, []).append(time.time())


def make_token() -> str:
    exp = str(int(time.time()) + TTL)
    sig = hmac.new(_secret(), exp.encode(), hashlib.sha256).hexdigest()
    return f"{exp}.{sig}"


def valid_token(tok: str | None) -> bool:
    if not tok or "." not in tok:
        return False
    exp, sig = tok.split(".", 1)
    good = hmac.new(_secret(), exp.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, good) and exp.isdigit() and int(exp) > time.time()


def cookie_secure() -> bool:
    return os.environ.get("MONTAJ_COOKIE_SECURE", "1") not in ("0", "false", "off")
