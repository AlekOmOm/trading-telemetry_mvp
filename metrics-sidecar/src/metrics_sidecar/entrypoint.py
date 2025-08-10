import asyncio
import logging
import uvicorn

from .app import MetricsSidecar
from .environment import get_sidecar_environment
from .utils.logging import setup_logging


async def main():
    """Async main with task coordination"""
    # Initialize configuration
    env_config = get_sidecar_environment()
    logger = setup_logging(env_config)
    
    logger.info(f"Starting metrics sidecar in {env_config.MODE} mode")

    # Initialize app
    app = MetricsSidecar(env_config, logger)

    # Run the FastAPI app with uvicorn
    config = uvicorn.Config(
        app.app, 
        host=env_config.SIDECAR_HTTP_HOST, 
        port=env_config.SIDECAR_HTTP_PORT,
        reload=not env_config.DOCKER_MODE
    )
    server = uvicorn.Server(config)
    
    try:
        await server.serve()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Received shutdown signal")
    finally:
        logger.info("Metrics sidecar shut down gracefully")


def run():
    """Run the metrics sidecar app"""
    try:
        asyncio.run(main())
    except SystemExit:
        pass
    except Exception as e:
        logging.error(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    run()
