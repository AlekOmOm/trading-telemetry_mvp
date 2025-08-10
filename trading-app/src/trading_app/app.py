from __future__ import annotations

from .launcher import run as _run
from .environment import get_trading_app_environment

def main() -> int:
    return _run()


if __name__ == "__main__":
    raise SystemExit(main())


def run() -> None:
    import uvicorn
    env_config = get_trading_app_environment()

    uvicorn.run(
        "trading_app.entrypoint:run",
        host=env_config.WEBAPP_HTTP_HOST,
        port=env_config.WEBAPP_HTTP_PORT,
        reload=env_config.DOCKER_MODE != True, # setting reload to false in docker mode, since it's not supported in docker
    )


if __name__ == "__main__":
    run()
