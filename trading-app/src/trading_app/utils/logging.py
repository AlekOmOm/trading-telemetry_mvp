import logging

def setup_logging(env_config):
    """Configure logging based on environment."""
    mode = env_config.MODE
    logging.basicConfig(
        level=logging.DEBUG if mode == "dev" else logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger(__name__)