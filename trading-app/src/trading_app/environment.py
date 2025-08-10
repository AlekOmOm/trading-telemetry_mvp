from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings

class TradingAppEnvironment(BaseSettings):
    """Trading app environment configuration with automatic .env loading."""
    
    # webapp
    WEBAPP_ZMQ_ADDR: str = "tcp://localhost:5555"
    WEBAPP_HTTP_HOST: str = "0.0.0.0"
    WEBAPP_HTTP_PORT: int = 8501

    # run environment
    DOCKER_MODE: bool = False # this will be set in `entrypoint.sh`, since only Dockerfile will use entrypoint.sh

    # paths
    REPO_ROOT: Path = Path(__file__).parents[3]
    APP_DIR: Path = Path(__file__).resolve().parent # app = trading_app/
    UI_PATH: Path = next(APP_DIR.glob("**/ui.py"))

    # system env
    MODE: str = "dev"

    # env loading (using pydantic_settings)
    model_config = {
        # priority order: repo root, project root, current directory
        "env_file": [
            REPO_ROOT / ".env",
            APP_DIR / ".env"
        ],
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra env vars not defined in this model
    }

def get_trading_app_environment() -> TradingAppEnvironment:
    """Get environment configuration with automatic .env loading and validation."""
    return TradingAppEnvironment()