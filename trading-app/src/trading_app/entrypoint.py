import asyncio
import uvloop

from .environment import get_trading_app_environment

from .app import TradingApp
from .features.ui import UIClass
from .features.client import TradingClient
from .utils.exit_handler import GracefulExit
from .utils.logging import setup_logging
from .utils.task_manager import TaskManager

async def main():
    """Async main with task coordination"""
    # Initialize configuration
    env_config = get_trading_app_environment()
    logger = setup_logging(env_config)
    
    logger.info(f"Starting trading app in {env_config.MODE} mode")

    task_manager = TaskManager()

    # Initialize business logic
    ui = UIClass(env_config, task_manager)
    client = TradingClient(env_config.WEBAPP_ZMQ_ADDR)
    
    # Initialize app
    app = TradingApp(env_config, logger, task_manager, ui, client)

    # Define shutdown coordination
    async def shutdown_trigger():
        await app.tm.stop_signal.wait()

    async def handle_shutdown(exc_type, exc_val, exc_tb):
        await app.exit_handler(exc_type, exc_val, exc_tb)

    async with GracefulExit(app=app, exit_handler=handle_shutdown):
        """ Run the trading app with uvloop using GracefulExit class.
        - `app.tm.add_task` to run concurrent tasks
        - `app.tm.stop_signal.wait` to wait for shutdown signal
        - `app.exit_handler` to handle graceful shutdown
        """
        ui_task = app.tm.add_task(app.run_streamlit_ui(), name="streamlit ui")
        main_task = app.tm.add_task(app.run_main_loop(), name="main loop")
        monitor_task = app.tm.add_task(app.tm.catch_breaking_errors(), name="error monitor")

        try:
            await asyncio.gather(ui_task, main_task, monitor_task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            """ Graceful shutdown on ctrl+c and error """

            logger.info("Received shutdown signal")
            app.tm.stop_signal.set()


def run():
    """Run the trading app with uvloop"""
    try:
        uvloop.run(main())
    except SystemExit:
        pass
    except Exception as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    run()
