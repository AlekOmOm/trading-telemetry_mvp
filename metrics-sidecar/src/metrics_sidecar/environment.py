from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings


class SidecarEnvironment(BaseSettings):
    """Metrics sidecar environment configuration with automatic .env loading."""
    
    SIDECAR_ZMQ_BIND: str = "tcp://0.0.0.0:5555"
    SIDECAR_HTTP_HOST: str = "0.0.0.0"
    SIDECAR_HTTP_PORT: int = 8001
    
    # run environment
    DOCKER_MODE: bool = False
    
    # paths
    REPO_ROOT: Path = Path(__file__).parents[3]
    APP_DIR: Path = Path(__file__).resolve().parent # app = metrics_sidecar/

    # system env
    MODE: str = "dev"
    
    model_config = {
        "env_file": [
            REPO_ROOT / ".env",
        ],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra env vars not defined in this model
    }


def get_sidecar_environment() -> SidecarEnvironment:
    """Get environment configuration with automatic .env loading and validation."""
    return SidecarEnvironment()

