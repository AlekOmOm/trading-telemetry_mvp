from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class SidecarEnvironment(BaseSettings):
    """Metrics sidecar environment configuration with automatic .env loading."""
    
    SIDECAR_ZMQ_BIND: str = "tcp://0.0.0.0:5555"
    SIDECAR_HTTP_HOST: str = "0.0.0.0"
    SIDECAR_HTTP_PORT: int = 8001
    DOCKER_MODE: bool = False

    model_config = {
        # Look for .env files starting from repo root
        "env_file": [
            Path(__file__).parents[3] / ".env",  # repo root
            Path(__file__).parents[2] / ".env",  # project root
            ".env"  # current directory
        ],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra env vars not defined in this model
    }


def get_sidecar_environment() -> SidecarEnvironment:
    """Get environment configuration with automatic .env loading and validation."""
    return SidecarEnvironment()


# Convenience accessors retained for compatibility
def sidecar_zmq_bind() -> str:
    return get_sidecar_environment().SIDECAR_ZMQ_BIND


def sidecar_http_host() -> str:
    return get_sidecar_environment().SIDECAR_HTTP_HOST


def sidecar_http_port() -> int:
    return get_sidecar_environment().SIDECAR_HTTP_PORT

