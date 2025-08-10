from __future__ import annotations
from environment import get_sidecar_environment

"""
entrypoint for managing the metrics sidecar app

app lifecycle management:
- async startup
- async graceful shutdown
"""

env_config = get_sidecar_environment()


def main():
    import uvicorn
    from environment import sidecar_http_host, sidecar_http_port
    
    uvicorn.run(
        "metrics_sidecar.web:app",
        host=env_config.SIDECAR_HTTP_HOST,
        port=env_config.SIDECAR_HTTP_PORT,
        reload=env_config.DOCKER_MODE != True # reload breaks docker containers
    )


if __name__ == "__main__":
    main()
