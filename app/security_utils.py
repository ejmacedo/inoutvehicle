"""Proteção contra força bruta: rastreia tentativas de login por IP."""
from datetime import datetime, timedelta
from collections import defaultdict

MAX_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# ip -> lista de datetimes das tentativas recentes
_attempts: dict[str, list] = defaultdict(list)


def _purge(ip: str):
    cutoff = datetime.now() - timedelta(minutes=LOCKOUT_MINUTES)
    _attempts[ip] = [t for t in _attempts[ip] if t > cutoff]


def is_blocked(ip: str) -> bool:
    _purge(ip)
    return len(_attempts[ip]) >= MAX_ATTEMPTS


def record_failure(ip: str):
    _purge(ip)
    _attempts[ip].append(datetime.now())


def clear(ip: str):
    _attempts[ip] = []


def remaining_lockout_minutes(ip: str) -> int:
    if not _attempts[ip]:
        return 0
    oldest = min(_attempts[ip])
    release = oldest + timedelta(minutes=LOCKOUT_MINUTES)
    delta = (release - datetime.now()).total_seconds()
    return max(0, int(delta // 60) + 1)
