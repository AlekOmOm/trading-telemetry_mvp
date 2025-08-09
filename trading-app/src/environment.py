from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Callable, TypeVar

T = TypeVar("T")


def _parse_dotenv(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        env[key.strip()] = val.strip()
    return env


def load_env() -> None:
    """
    load env variables from repo-level .env (fallback to project-level .env)

    nb: doesn't overwrite existing os.environ keys.
    """
    here = Path(__file__).resolve()
    project_root = here.parents[1]
    repo_root = here.parents[2]
    for candidate in (repo_root / ".env", project_root / ".env"):
        for k, v in _parse_dotenv(candidate).items():
            os.environ.setdefault(k, v)


def getenv(key: str, default: Optional[T] = None, cast: Optional[Callable[[str], T]] = None) -> Optional[T]:
    """Get env var with optional casting."""
    val = os.getenv(key)
    if val is None:
        return default
    return cast(val) if cast else val  # type: ignore[return-value]


# Convenience accessors for this project
def webapp_zmq_addr() -> str:
    load_env()
    return getenv("WEBAPP_ZMQ_ADDR", "tcp://localhost:5555")  # publisher connect addr


def webapp_http_host() -> str:
    load_env()
    return getenv("WEBAPP_HTTP_HOST", "0.0.0.0")


def webapp_http_port() -> int:
    load_env()
    return int(getenv("WEBAPP_HTTP_PORT", 8501))

