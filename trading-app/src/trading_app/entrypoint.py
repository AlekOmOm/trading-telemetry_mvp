from __future__ import annotations

import logging
import subprocess

from .environment import get_trading_app_environment
from .app import TradingApp

env_config = get_trading_app_environment()

def setup_logging() -> logging.Logger:
    """Configure logging based on environment."""
    mode = env_config.MODE
    logging.basicConfig(
        level=logging.DEBUG if mode == "dev" else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)


def main():
    """Launch the Streamlit UI with configured host/port.

    Returns the process return code.
    """
    logger = setup_logging()

    logger.info(f"Starting trading app in {env_config.MODE} mode")

    cmd = [
        "streamlit",
        "run",
        str(env_config.UI_PATH),
        "--server.address",
        env_config.WEBAPP_HTTP_HOST,
        "--server.port",
        str(env_config.WEBAPP_HTTP_PORT),
    ]
    return subprocess.run(cmd, check=False).returncode

def run():
    """Run the trading app."""
    main()

if __name__ == "__main__":
    raise SystemExit(run())
