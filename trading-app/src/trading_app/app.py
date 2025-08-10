import asyncio
import logging
import subprocess
import signal
from typing import Optional

import zmq
import json

from .environment import TradingAppEnvironment, get_trading_app_environment
from .features.ui import UIClass
from .features.client import TradingClient
from .utils.task_manager import TaskManager

class TradingApp:
    """Trading app with async task coordination

    Args:
        env_config: TradingAppEnvironment
        logger: logging.Logger
        ui: UIClass
        client: TradingClient
    
    responsibilities:
        - ZMQ bridge between UI and external systems
        - run processes (called by entrypoint.py)
            - Run Streamlit UI
            - Run main loop
        - variables and handlers for `entrypoint.py`
            - provide `exit_handler`
                - for handling graceful shutdown
            - initializations:
                - `tm`
                - `ui_process`
                - `_ctx`
    """
    
    def __init__(self, 
                env_config: TradingAppEnvironment, 
                logger: logging.Logger, 
                task_manager: TaskManager,
                ui: UIClass,
                client: TradingClient):
        # params
        self.env_config = env_config or get_trading_app_environment()
        self.logger = logger or logging.getLogger(__name__)
        self.tm = task_manager
        self.client = client
        self.ui = ui
        # internal
        self._ctx = zmq.Context.instance() # for zmq sockets

    async def run_main_loop(self):
        """Main loop: ZMQ bridge between UI and external systems
        
        main purpose:
        - non-blocking message broker between 
            - UI (streamlit single-threaded process)
            - client 
        """
        self.logger.info("Starting ZMQ bridge")
        
        # Internal ZMQ PULL (from UI process)
        internal_addr = self.env_config.APP_ZMQ_ADDR  # tcp://127.0.0.1:5556
        internal_sock = self._ctx.socket(zmq.PULL)
        internal_sock.bind(internal_addr)
        
        try:
            while not self.tm.stop_signal.is_set():
                try:
                    # Non-blocking receive from UI
                    msg = internal_sock.recv_string(zmq.NOBLOCK)
                    self.logger.debug(f"Received from UI: {msg}")
                    
                    # Forward to external sidecar via client
                    result = self.client.publish_json(json.loads(msg))
                    if not result.ok:
                        self.logger.warning(f"Forward failed: {result.error}")
                        
                except zmq.Again:
                    pass  # No message available
                
                await asyncio.sleep(0.01)  # Small delay for async cooperation
                
        except asyncio.CancelledError:
            self.logger.info("Main loop cancelled")
        finally:
            internal_sock.close()

    async def run_streamlit_ui(self):
        """Run streamlit UI as async task - delegate to UIClass"""
        try:
            await self.ui.run()
        except asyncio.CancelledError:
            self.logger.info("Streamlit task cancelled")
        except Exception as e:
            self.logger.error(f"Streamlit error: {e}")
            self.tm.stop_signal.set()
            raise

    async def exit_handler(self, exc_type, exc_val, exc_tb):
        """Handle graceful shutdown"""
        self.logger.info("Exit handler called")
        
        # Cancel all tasks
        self.tm.cancel_all_tasks()
        
        self.logger.info("Shutdown complete")
