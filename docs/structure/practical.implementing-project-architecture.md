# Practical Implementation Guide: Async-First Project Architecture

This guide provides two practical implementations of the architectural patterns from `insights.pattern-of-project-architecture.md`:

1. **Minimal Version**: Using only standard Python libraries (for MVP projects outside caesari2)
2. **Caesari Version**: Leveraging caesari packages (for projects inside caesari2 repo)

---

## Version 1: Minimal Implementation (Standard Python Only)

### Project Structure
```
my-app/
├── src/
│   └── my_app/
│       ├── __init__.py
│       ├── entrypoint.py      # Lifecycle orchestration
│       ├── app.py             # Transport layer
│       ├── environment.py     # Configuration
│       ├── client.py          # Business logic
│       ├── task_manager.py    # Simple task coordination
│       └── graceful_exit.py   # Simple graceful exit
├── pyproject.toml
└── Dockerfile
```

### 1. Configuration Layer (`environment.py`)
```python
from dataclasses import dataclass
from enum import StrEnum
from os import environ as env


class AppMode(StrEnum):
    prod = "prod"
    dev = "dev"
    staging = "staging"


@dataclass
class AppEnvironment:
    MODE: AppMode
    SERVER_IP: str
    SERVER_PORT: int
    API_KEY: str
    LOG_LEVEL: str


def get_app_environment() -> AppEnvironment:
    mode_str = env.get("MODE")
    if mode_str is None:
        raise ValueError("MODE environment variable is required")

    mode = AppMode(mode_str)  # Enum validation

    api_key = env.get("API_KEY")
    if api_key is None:
        raise ValueError("API_KEY environment variable is required")

    return AppEnvironment(
        MODE=mode,
        SERVER_IP=env.get("SERVER_IP", "127.0.0.1"),
        SERVER_PORT=int(env.get("SERVER_PORT", "8000")),
        API_KEY=api_key,
        LOG_LEVEL=env.get("LOG_LEVEL", "INFO"),
    )
```

### 2. Simple Task Manager (`task_manager.py`)
```python
import asyncio
import logging
from typing import Dict


class SimpleTaskManager:
    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.stop_signal = asyncio.Event()
        self.logger = logging.getLogger(__name__)

    def add_task(self, coro, name: str) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self.tasks[name] = task
        self.logger.info(f"Added task: {name}")
        return task

    def cancel_all_tasks(self):
        for name, task in self.tasks.items():
            if not task.done():
                self.logger.info(f"Cancelling task: {name}")
                task.cancel()

    async def catch_breaking_errors(self):
        """Monitor for any unhandled exceptions in tasks"""
        try:
            while not self.stop_signal.is_set():
                await asyncio.sleep(1)
                # Check for failed tasks
                for name, task in self.tasks.items():
                    if task.done() and not task.cancelled():
                        try:
                            task.result()  # This will raise if task failed
                        except Exception as e:
                            self.logger.error(f"Task {name} failed: {e}")
                            self.stop_signal.set()
                            return
        except asyncio.CancelledError:
            pass
```

### 3. Simple Graceful Exit (`graceful_exit.py`)
```python
import asyncio
import signal
import sys
from typing import Any, Callable


class SimpleGracefulExit:
    def __init__(self, app: Any, exit_handler: Callable):
        self.app = app
        self.exit_handler = exit_handler
        self.original_handlers = {}

    async def __aenter__(self):
        # Set up signal handlers
        for sig in [signal.SIGTERM, signal.SIGINT]:
            self.original_handlers[sig] = signal.signal(sig, self._signal_handler)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Restore original signal handlers
        for sig, handler in self.original_handlers.items():
            signal.signal(sig, handler)

        # Call exit handler
        await self.exit_handler(exc_type, exc_val, exc_tb)

    def _signal_handler(self, signum, frame):
        # Convert signal to async event
        asyncio.create_task(self.exit_handler(None, None, None))


def wrap_in_system_exit(result: Any) -> None:
    """Simple wrapper that converts exceptions to system exit codes"""
    try:
        if result is not None:
            sys.exit(0)
    except Exception as e:
        print(f"Application error: {e}")
        sys.exit(1)
```

### 4. Business Logic (`client.py`)
```python
import asyncio
import logging
from .environment import AppEnvironment
from .task_manager import SimpleTaskManager


class MyAppClient:
    def __init__(self, environment: AppEnvironment, task_manager: SimpleTaskManager | None = None):
        self.env = environment
        self.logger = logging.getLogger(__name__)
        self.tm = task_manager or SimpleTaskManager()
        self.running = False

    async def initialize(self):
        """Initialize client resources"""
        self.logger.info("Initializing client")
        # Add your initialization logic here
        self.running = True

    async def stop(self):
        """Stop client and cleanup resources"""
        self.logger.info("Stopping client")
        self.running = False
        # Add your cleanup logic here


### 5. Transport Layer (`app.py`)
```python
import asyncio
from typing import Any
from .client import MyAppClient
from .environment import AppEnvironment, AppMode
from .task_manager import SimpleTaskManager


class MyAppServer:
    def __init__(self, env: AppEnvironment, client: MyAppClient):
        self.env = env
        self.client = client
        self.tm = SimpleTaskManager()
        self.logger = logging.getLogger(__name__)

    async def run_server(self):
        """Main server loop - replace with your actual server logic"""
        self.logger.info(f"Server starting on {self.env.SERVER_IP}:{self.env.SERVER_PORT}")

        try:
            while not self.tm.stop_signal.is_set():
                # Your server logic here (HTTP server, message processing, etc.)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Server task cancelled")
            self.tm.stop_signal.set()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self.tm.stop_signal.set()
            raise

    async def exit_handler(self, exc_type, exc_val, exc_tb) -> None:
        """Handle graceful shutdown"""
        self.logger.info("Exit handler called")

        # Send notifications in production
        if self.env.MODE != AppMode.dev:
            try:
                # Add your notification logic here
                self.logger.info(f"Would send notification: App shutdown - {exc_type}")
            except Exception as e:
                self.logger.error(f"Error sending notification: {e}")

        # Stop business logic
        await self.client.stop()

        # Cancel all tasks
        self.tm.cancel_all_tasks()

        self.logger.info("Shutdown complete")
```

### 6. Lifecycle Orchestration (`entrypoint.py`)
```python
import asyncio
import logging
import uvloop
from .app import MyAppServer
from .client import MyAppClient
from .environment import get_app_environment
from .graceful_exit import SimpleGracefulExit, wrap_in_system_exit


async def main() -> None:
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize configuration
    env = get_app_environment()

    # Initialize business logic
    client = MyAppClient(environment=env)
    await client.initialize()

    # Initialize transport layer
    server = MyAppServer(env=env, client=client)

    # Define shutdown coordination
    async def shutdown_trigger() -> None:
        await server.tm.stop_signal.wait()

    async def handle_shutdown(exc_type, exc_val, exc_tb) -> None:
        await server.exit_handler(exc_type, exc_val, exc_tb)

    # Run with graceful shutdown
    async with SimpleGracefulExit(app=server, exit_handler=handle_shutdown):
        server_task = server.tm.add_task(server.run_server(), name="run server")
        monitor_task = server.tm.add_task(server.tm.catch_breaking_errors(), name="error monitor")

        try:
            await asyncio.gather(server_task, monitor_task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Received shutdown signal")
            server.tm.stop_signal.set()


def run() -> None:
    wrap_in_system_exit(uvloop.run(main()))


if __name__ == "__main__":
    run()
```

### 7. Package Configuration (`pyproject.toml`)
```toml
[project]
name = "my-app"
version = "0.1.0"
dependencies = [
    "uvloop",
    # Add your other dependencies
]

[project.scripts]
run-my-app = "my_app.entrypoint:run"
```

---

## Version 2: Caesari Implementation (For caesari2 repo projects)

### Project Structure
```
my_caesari_app/
├── src/
│   └── my_caesari_app/
│       ├── __init__.py
│       ├── entrypoint.py      # Lifecycle orchestration
│       ├── app.py             # Transport layer
│       ├── environment.py     # Configuration
│       └── client.py          # Business logic
└── pyproject.toml
```

### 1. Configuration Layer (`environment.py`)
```python
from dataclasses import dataclass
from enum import StrEnum
from os import environ as env


class MyAppMode(StrEnum):
    prod = "prod"
    dev = "dev"
    staging = "staging"


@dataclass
class MyAppEnvironment:
    MODE: MyAppMode
    SERVER_IP: str
    SERVER_PORT: int
    API_KEY: str


def get_my_app_environment() -> MyAppEnvironment:
    mode_str = env.get("MODE")
    if mode_str is None:
        raise ValueError("MODE environment variable is required")

    mode = MyAppMode(mode_str)

    api_key = env.get("API_KEY")
    if api_key is None:
        raise ValueError("API_KEY environment variable is required")

    return MyAppEnvironment(
        MODE=mode,
        SERVER_IP=env.get("SERVER_IP", "127.0.0.1"),
        SERVER_PORT=int(env.get("SERVER_PORT", "8000")),
        API_KEY=api_key,
    )
```

### 2. Business Logic (`client.py`)
```python
import asyncio
from caesari_aio import AsyncTaskManager
from caesari_logger.std_logger import get_logger
from .environment import MyAppEnvironment


class MyAppClient:
    def __init__(self, environment: MyAppEnvironment, task_manager: AsyncTaskManager | None = None):
        self.env = environment
        self.logger = get_logger(__name__)
        self.tm = task_manager or AsyncTaskManager()
        self.running = False

    async def initialize(self):
        """Initialize client resources"""
        self.logger.info("Initializing client")
        # Add your initialization logic here
        self.running = True

    async def stop(self):
        """Stop client and cleanup resources"""
        self.logger.info("Stopping client")
        self.running = False
        # Add your cleanup logic here
```

### 3. Transport Layer (`app.py`)
```python
import asyncio
from typing import Any
from caesari_aio import AsyncTaskManager
from caesari_logger.std_logger import get_logger
from .client import MyAppClient
from .environment import MyAppEnvironment, MyAppMode


class MyAppServer:
    def __init__(self, env: MyAppEnvironment, client: MyAppClient):
        self.env = env
        self.client = client
        self.tm = AsyncTaskManager()
        self.logger = get_logger(__name__)

    async def run_server(self):
        """Main server loop"""
        self.logger.info(f"Server starting on {self.env.SERVER_IP}:{self.env.SERVER_PORT}")

        try:
            while not self.tm.stop_signal.is_set():
                # Your server logic here
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("Server task cancelled")
            self.tm.stop_signal.set()
        except Exception as e:
            self.logger.error(f"Server error: {e}")
            self.tm.stop_signal.set()
            raise

    async def exit_handler(self, *args: tuple[Any, ...], **kwargs: dict[str, Any]) -> None:
        """Handle graceful shutdown"""
        self.logger.info("Exit handler called")

        # Production notifications
        if self.env.MODE != MyAppMode.dev:
            try:
                # Add notification logic (Slack, email, etc.)
                self.logger.info(f"Would send notification: App shutdown - {args}")
            except Exception as e:
                self.logger.error(f"Error sending notification: {e}")

        # Stop business logic
        await self.client.stop()

        # Cancel all tasks
        self.tm.cancel_all_tasks()

        self.logger.info("Shutdown complete")
```

### 4. Lifecycle Orchestration (`entrypoint.py`)
```python
import asyncio
import uvloop
from caesari_aio import AsyncTaskManager
from caesari_graceful_exit.helpers import wrap_in_system_exit
from caesari_graceful_exit.module import GracefulExit
from caesari_logger.std_logger import get_logger
from .app import MyAppServer
from .client import MyAppClient
from .environment import get_my_app_environment


async def main() -> None:
    logger = get_logger(__name__)

    # Initialize configuration
    env = get_my_app_environment()

    # Initialize task manager
    tm = AsyncTaskManager()

    # Initialize business logic
    client = MyAppClient(environment=env, task_manager=tm)
    await client.initialize()

    # Initialize transport layer
    server = MyAppServer(env=env, client=client)

    # Define shutdown coordination
    async def shutdown_trigger() -> None:
        await tm.stop_signal.wait()

    async def handle_shutdown(exc_type, exc_val, exc_tb) -> None:
        await server.exit_handler(exc_type, exc_val, exc_tb)

    # Run with graceful shutdown
    async with GracefulExit(app=server, exit_handler=handle_shutdown):
        server_task = tm.add_task(server.run_server(), name="run server")
        monitor_task = tm.add_task(tm.catch_breaking_errors(), name="error monitor")

        try:
            await asyncio.gather(server_task, monitor_task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            logger.info("Received shutdown signal")
            tm.stop_signal.set()


def run() -> None:
    wrap_in_system_exit(uvloop.run(main()))


if __name__ == "__main__":
    run()
```

### 5. Package Configuration (`pyproject.toml`)
```toml
[project]
name = "my-caesari-app"
version = "0.1.0"
dependencies = [
    "uvloop",
    "caesari-aio",
    "caesari-graceful-exit",
    "caesari-logger",
    # Add your other dependencies
]

[project.scripts]
run-my-caesari-app = "my_caesari_app.entrypoint:run"
```

---

## Key Implementation Notes

### Minimal Version Benefits
- **Zero external dependencies** for core architecture
- **Easy to understand** and modify
- **Portable** across different Python environments
- **Quick to implement** for MVPs

### Caesari Version Benefits
- **Battle-tested components** from production systems
- **Rich logging** and monitoring capabilities
- **Robust error handling** and task management
- **Consistent patterns** across caesari2 projects

### Common Implementation Steps

1. **Start with environment.py**: Validate configuration early
2. **Implement convergent shutdown**: All failure paths → stop_signal
3. **Use dependency injection**: Pass dependencies down, not up
4. **Test shutdown behavior**: Critical for production reliability
5. **Add console script**: Same entry point everywhere

### Critical Patterns to Maintain

#### Convergent Shutdown Flow
```python
# All these paths must lead to the same place:
signal.SIGTERM → tm.stop_signal.set()
KeyboardInterrupt → tm.stop_signal.set()
Task Exception → tm.stop_signal.set()
Internal Error → tm.stop_signal.set()
```

#### Dependency Injection Chain
```python
# entrypoint.py
env = get_app_environment()
client = MyAppClient(environment=env)
server = MyAppServer(env=env, client=client)

# Dependencies flow down, never up
```

### Testing Your Implementation

```python
# test_shutdown.py
import asyncio
import pytest
from my_app.entrypoint import main

@pytest.mark.asyncio
async def test_graceful_shutdown():
    """Test that shutdown completes within reasonable time"""
    task = asyncio.create_task(main())
    await asyncio.sleep(0.1)  # Let it start
    task.cancel()

    try:
        await asyncio.wait_for(task, timeout=5.0)
    except asyncio.CancelledError:
        pass  # Expected

    # Verify cleanup completed
    assert True  # Add your specific assertions

@pytest.mark.asyncio
async def test_configuration_validation():
    """Test that invalid configuration raises appropriate errors"""
    import os
    # Remove required env var
    if "MODE" in os.environ:
        del os.environ["MODE"]

    with pytest.raises(ValueError, match="MODE environment variable is required"):
        from my_app.environment import get_app_environment
        get_app_environment()
```

### Docker Integration

```dockerfile
# Dockerfile (works for both versions)
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .

# Same entry point as local development
ENTRYPOINT ["run-my-app"]
```

### Environment Variables Template

```bash
# .env.example
MODE=dev
SERVER_IP=127.0.0.1
SERVER_PORT=8000
API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

## Quick Start Commands

### Minimal Version
```bash
# 1. Create project structure
mkdir -p my_app/src/my_app
cd my_app

# 2. Copy the code examples above into respective files
# 3. Install dependencies
pip install uvloop

# 4. Set environment variables
export MODE=dev
export API_KEY=test_key

# 5. Run locally
python src/my_app/entrypoint.py
```

### Caesari Version
```bash
# 1. Create project structure in caesari2 repo
mkdir -p projects/my_caesari_app/src/my_caesari_app
cd projects/my_caesari_app

# 2. Copy the code examples above into respective files
# 3. Dependencies already available in caesari2

# 4. Set environment variables
export MODE=dev
export API_KEY=test_key

# 5. Run locally
python src/my_caesari_app/entrypoint.py
```

This practical guide provides concrete, copy-paste implementations that maintain the core architectural benefits while being immediately usable for new projects.
```