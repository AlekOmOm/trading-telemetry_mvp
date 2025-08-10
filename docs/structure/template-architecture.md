# Ultra-Simple Project Architecture Template

A minimal, highly reproducible project scaffolding template based on the core organizational insights from the Dammsugare architecture, stripped of complex async handling for quick project setup.

## Project Structure

```
my-simple-app/
├── src/
│   └── my_simple_app/
│       ├── __init__.py
│       ├── entrypoint.py      # Entry point and basic lifecycle
│       ├── app.py             # Main application logic
│       ├── environment.py     # Environment configuration
│       ├── features/          # Feature-based organization
│       │   ├── feature1/
│       │   │   ├── __init__.py
│       │   │   ├── something.py
│       │   │   └── something_else.py
│       │   └── ...
│       └── lib/               # Library (optional)
│           ├── client.py      # Business logic (optional, if you need to use it in app.py)
│           ├── utils.py       # Utility functions
│           └── __init__.py    # Library initialization (optional)
├── pyproject.toml
├── .env.example
├── .env
└── README.md
```

## Core Files

### 1. Environment Configuration (`environment.py`)

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
    HOST: str
    PORT: int
    DEBUG: bool


def get_app_environment() -> AppEnvironment:
    """Load and validate configuration from environment variables"""
    mode_str = env.get("MODE", "dev")
    mode = AppMode(mode_str)  # Enum validation

    return AppEnvironment(
        MODE=mode,
        HOST=env.get("HOST", "localhost"),
        PORT=int(env.get("PORT", "8000")),
        DEBUG=mode == AppMode.dev,
    )
```

### 2. Business Logic (`client.py`)

```python
import logging
from .environment import AppEnvironment


class AppClient:
    """Core business logic - isolated from transport concerns"""

    def __init__(self, config: AppEnvironment):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.running = False

    def start(self):
        """Initialize and start the client"""
        self.logger.info("Starting client")
        # Add your business logic initialization here
        self.running = True

    def stop(self):
        """Stop and cleanup the client"""
        self.logger.info("Stopping client")
        # Add your cleanup logic here
        self.running = False

    def process_data(self, data):
        """Example business method"""
        # Your core business logic here
        return f"Processed: {data}"
```

### 3. Application Layer (`app.py`)

```python
import logging
from .client import AppClient
from .environment import AppEnvironment, AppMode

class SimpleApp:
    """Transport/interface layer - handles external interactions"""

    def __init__(self, config: AppEnvironment, client: AppClient):
        self.config = config
        self.client = client
        self.logger = logging.getLogger(__name__)

    def run(self):
        """Main application loop"""
        self.logger.info(f"App starting on {self.config.HOST}:{self.config.PORT}")

        try:
            # Start business logic
            self.client.start()

            # Main application loop
            self._main_loop()

        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
        except Exception as e:
            self.logger.error(f"Application error: {e}")
            raise
        finally:
            self._cleanup()

    def _main_loop(self):
        """Main application logic - replace with your implementation"""
        import time

        self.logger.info("Application running (Ctrl+C to stop)")
        try:
            while True:
                # Your main application logic here
                # Example: HTTP server, message processing, etc.
                time.sleep(1)

                if self.config.DEBUG:
                    self.logger.debug("App tick")

        except KeyboardInterrupt:
            pass  # Handle gracefully in run()

    def _cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up...")

        # Send notifications in production
        if self.config.MODE != AppMode.dev:
            try:
                # Add notification logic here
                self.logger.info("Would send shutdown notification")
            except Exception as e:
                self.logger.error(f"Notification error: {e}")

        # Stop business logic
        self.client.stop()

        self.logger.info("Cleanup complete")
```

### 4. Entry Point (`entrypoint.py`)

```python
import logging
import sys
from .app import SimpleApp
from .client import AppClient
from .environment import AppEnvironment


def setup_logging(config):
    """Configure logging based on environment"""
    level = logging.DEBUG if config.DEBUG else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main entry point with basic error handling"""
    try:
        # Load configuration
        env_config = get_app_environment()

        # Setup logging
        setup_logging(env_config)
        logger = logging.getLogger(__name__)

        logger.info(f"Starting application in {env_config.MODE} mode")

        # Initialize components with dependency injection
        client = AppClient(config=env_config)
        app = SimpleApp(config=env_config, client=client)

        # Run application
        app.run()

    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


def run():
    """Console script entry point"""
    main()


if __name__ == "__main__":
    run()
```

### 5. Package Configuration (`pyproject.toml`)

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-simple-app"
version = "0.1.0"
description = "Simple app using minimal architecture pattern"
dependencies = [
    # Add your dependencies here
]

[project.scripts]
run-my-simple-app = "my_simple_app.entrypoint:run"

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-asyncio",
]
```

### 6. Environment Template (`.env.example`)

```bash
# Application mode
MODE=dev

# Server configuration
HOST=localhost
PORT=8000

# Add your environment variables here
API_KEY=your_api_key_here
DATABASE_URL=sqlite:///app.db
```

## Key Benefits Retained

### ✅ **Essential Patterns Preserved:**

- **Layer Separation**: environment → client → app → entrypoint
- **Dependency Injection**: Dependencies passed down explicitly
- **Configuration Validation**: Enum-based mode validation
- **Console Script**: Same entry point for all environments
- **Error Boundaries**: Each layer handles its own concerns

### ✅ **Simplified for Quick Use:**

- **No complex async coordination** - basic try/except handling
- **Standard library focus** - minimal external dependencies
- **Synchronous by default** - easier to understand and debug
- **Basic logging** - simple but effective
- **Straightforward testing** - easy to add tests

### ✅ **Still Production-Ready Path:**

- **Clear upgrade path** to full async version when needed
- **Same organizational structure** as production systems
- **Environment-aware** configuration
- **Proper separation of concerns** for maintainability

## When to Use This Template

**Perfect for:**

- 🚀 **Prototypes and MVPs**
- 📚 **Learning projects**
- 🔧 **Simple utilities and tools**
- 🏃‍♂️ **Quick proof-of-concepts**
- 🎯 **Projects that don't need complex async handling**

**Upgrade to full pattern when:**

- Multiple concurrent operations needed
- Production-grade error handling required
- Complex shutdown coordination necessary
- High-availability requirements

## Example Customizations

### Add HTTP Server

```python
# In app.py _main_loop method
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

app.run(host=self.config.HOST, port=self.config.PORT)
```

#### openapi fastapi

```python
from

This template gives you the **organizational benefits** of the Project architecture without the **complexity overhead**, making it perfect for getting projects started quickly while maintaining good structure.
```
