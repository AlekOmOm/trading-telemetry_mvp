from __future__ import annotations

import json
import subprocess
import time
import logging
import asyncio
from typing import Any, List, Optional

from trading_app.environment import TradingAppEnvironment, get_trading_app_environment

"""UI process manager - no Streamlit imports to avoid context warnings"""
import asyncio
import subprocess
import logging
from pathlib import Path

from trading_app.environment import TradingAppEnvironment

class UIClass:
    """UI process manager - launches isolated Streamlit subprocess"""

    def __init__(self, env_config: TradingAppEnvironment, task_manager=None):
        self.env = env_config
        self.tm = task_manager
        self.ui_process = None
        self.logger = logging.getLogger(__name__)

    async def run(self):
        """Launch Streamlit in isolated subprocess"""
        
        cmd = [
            "streamlit", "run", str(self.env.UI_PATH), # streamlit_main.py path
            "--server.address", self.env.WEBAPP_HTTP_HOST,
            "--server.port", str(self.env.WEBAPP_HTTP_PORT),
        ]
        
        self.logger.info(f"Starting Streamlit: {' '.join(cmd)}")
        self.ui_process = subprocess.Popen(cmd)

        try:
            while not self.tm.stop_signal.is_set():
                if self.ui_process.poll() is not None:
                    self.logger.error("Streamlit process died unexpectedly")
                    self.tm.stop_signal.set()
                    return
                await asyncio.sleep(1)
        finally:
            if self.ui_process and self.ui_process.poll() is None:
                self.logger.info("Terminating Streamlit process")
                self.ui_process.terminate()
                try:
                    self.ui_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.logger.warning("Force killing Streamlit process")
                    self.ui_process.kill()
