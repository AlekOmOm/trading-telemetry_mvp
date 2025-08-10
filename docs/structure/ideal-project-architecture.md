# Ideal Project Architecture Standard

This document defines the architectural patterns and standards used in the Ideal project, emphasizing the separation of concerns, lifecycle management, and deployment strategies that make this system robust and maintainable.

## Table of Contents

1. [Project Structure Pattern](#project-structure-pattern)
2. [Core Module Separation](#core-module-separation)
3. [Entrypoint Lifecycle Management](#entrypoint-lifecycle-management)
4. [Environment Configuration Pattern](#environment-configuration-pattern)
5. [Docker Containerization Strategy](#docker-containerization-strategy)
6. [Package Management and Scripts](#package-management-and-scripts)

---

## Project Structure Pattern

### Definition

The project follows a nested structure pattern: `<project-name>/src/<project_name>/` that provides clear separation between project metadata, source code, and deployment artifacts.

### Explanation

This structure separates concerns at the highest level:

- **Root level**: Contains project metadata, configuration, and deployment files
- **src/ level**: Contains the actual source code in a namespace package
- **docker/ level**: Contains containerization and deployment scripts

This pattern prevents namespace pollution, enables clean packaging, and supports multiple deployment targets while maintaining a clear development workflow.

### Example

```
<project-name>/                          # Project root
├── pyproject.toml                   # Package configuration & scripts
├── docker/                          # Deployment artifacts
│   ├── Dockerfile                   # Container definition
│   └── bin/entrypoint.sh           # Container entrypoint
├── src/<project_name>/                  # Source code namespace
│   ├── entrypoint.py               # Application lifecycle
│   ├── app.py                      # Web server & routing
│   ├── environment.py              # Configuration management
│   └── client.py                   # Business logic
└── tests/                          # Test suite
```

---

## Core Module Separation

### Definition

The application logic is separated into three core modules with distinct responsibilities: `entrypoint.py` (lifecycle), `app.py` (web layer), and `environment.py` (configuration).

### Explanation

This separation follows the Single Responsibility Principle and creates clear boundaries:

- **entrypoint.py**: Manages application lifecycle, dependency injection, and graceful shutdown
- **app.py**: Handles HTTP routing, request/response processing, and web-specific concerns
- **environment.py**: Centralizes configuration parsing, validation, and environment-specific logic

This pattern enables independent testing, clear dependency flow, and easier maintenance as each module has a single, well-defined purpose.

### Example

**entrypoint.py** - Application Lifecycle:

```python
async def main() -> None:
    # 1. Initialize dependencies
    env = get_<project_name>_environment()
    client = <project_name>Client(...)
    server = <project_name>WebServer(env=env, client=client, ...)

    # 2. Define lifecycle functions
    async def shutdown_trigger() -> None:
        await tm.stop_signal.wait()

    # 3. Manage graceful shutdown
    async with GracefulExit(app=server, exit_handler=handle_shutdown):
        await asyncio.gather(server_task, breaking_task)

def run() -> None:
    wrap_in_system_exit(uvloop.run(main()))
```

**app.py** - Web Layer:

```python
class <project_name>WebServer:
    def __init__(self, env, client, command_handler, interaction_handler):
        self.app = self._create_app()
        self._initialize_app()

    def _register_routes(self) -> None:
        @self.app.route("/decrease_position", methods=["POST"])
        @basic_auth_required()
        async def decrease_position_endpoint() -> Response:
            # Handle HTTP request/response
```

**environment.py** - Configuration:

```python
@dataclass
class <project_name>Environment:
    MODE: <project_name>Mode
    SERVER_IP: str
    EXCHANGE_TO_ACCOUNTS_DICT: dict[Exchange, list[AccountID]]
    # ... other config fields

def get_<project_name>_environment() -> <project_name>Environment:
    # Parse and validate environment variables
    # Return structured configuration object
```

---

## Entrypoint Lifecycle Management

### Definition

The entrypoint module implements a comprehensive async lifecycle management pattern using `GracefulExit`, `AsyncTaskManager`, and `uvloop` for robust startup and shutdown handling.

### Explanation

This pattern addresses the complexity of managing async applications with multiple concurrent tasks:

- **uvloop**: Provides high-performance event loop for async operations
- **GracefulExit**: Ensures clean shutdown even when exceptions occur
- **AsyncTaskManager**: Coordinates multiple async tasks and handles cancellation
- **shutdown_trigger**: Provides a clean way to signal shutdown across the application

The pattern prevents resource leaks, ensures proper cleanup, and provides predictable behavior during both normal and exceptional shutdown scenarios.

### Example

**Complete Lifecycle Pattern**:

```python
def run() -> None:
    """Entry point that wraps the async main in system exit handling."""
    wrap_in_system_exit(uvloop.run(main()))

async def main() -> None:
    # 1. Initialize all dependencies
    env = get_<project_name>_environment()
    tm = AsyncTaskManager()
    client = <project_name>Client(...)
    server = <project_name>WebServer(...)

    # 2. Define shutdown coordination
    async def shutdown_trigger() -> None:
        await tm.stop_signal.wait()

    async def run_server() -> None:
        try:
            await server.app.run_task(
                host=env.SERVER_IP,
                port=env.SERVER_PORT,
                shutdown_trigger=shutdown_trigger
            )
        except asyncio.CancelledError:
            tm.stop_signal.set()  # Propagate shutdown signal

    # 3. Define cleanup handler
    async def handle_shutdown(exc_type, exc_val, exc_tb) -> None:
        await server.exit_handler((exc_type, exc_val, exc_tb))

    # 4. Run with graceful exit management
    async with GracefulExit(app=server, exit_handler=handle_shutdown):
        server_task = tm.add_task(run_server(), name="run server")
        breaking_task = tm.add_task(tm.catch_breaking_errors(), name="catching breaking errors")

        try:
            await asyncio.gather(server_task, breaking_task)
        except (KeyboardInterrupt, asyncio.CancelledError):
            tm.stop_signal.set()
            server_task.cancel()
```

**Why This Pattern**:

- **Predictable Shutdown**: All tasks are properly cancelled and cleaned up
- **Exception Safety**: Unhandled exceptions trigger graceful shutdown
- **Resource Management**: Prevents connection leaks and orphaned processes
- **Signal Coordination**: Clean communication between components during shutdown

---

## Environment Configuration Pattern

### Definition

Environment configuration uses a dataclass-based pattern with centralized parsing, validation, and mode-specific behavior through enums and factory functions.

### Explanation

This pattern provides type safety, validation, and clear environment boundaries:

- **Dataclass Structure**: Provides type hints and immutable configuration
- **Mode Enums**: Ensures valid environment modes (dev/staging/prod)
- **Factory Function**: Centralizes parsing logic and validation
- **Environment Variables**: Single source of truth for configuration

The pattern prevents configuration errors, enables environment-specific behavior, and provides clear documentation of required settings.

### Example

**Environment Definition**:

```python
class <project_name>Mode(StrEnum):
    prod = "prod"
    dev = "dev"
    staging = "staging"

@dataclass
class <project_name>Environment:
    MODE: <project_name>Mode
    SERVER_IP: str
    SERVER_PORT: int
    EXCHANGE_TO_ACCOUNTS_DICT: dict[Exchange, list[AccountID]]
    APPROVED_USER_IDS: list[str]
    SLACK_OAUTH: str
    <project_name>_API_AUTH_USERNAME: str
    <project_name>_API_AUTH_PASSWORD: str
    QUART_SECRET_KEY: str
    SLACK_MODE: bool
    SLACK_CHANNEL: <project_name>SlackChannel
```

**Environment Factory**:

```python
def get_<project_name>_environment() -> <project_name>Environment:
    # 1. Parse mode with validation
    mode_str = env.get("MODE")
    if mode_str is None:
        raise ValueError("MODE is not set")
    mode = <project_name>Mode(mode_str)

    # 2. Mode-specific configuration
    if mode == <project_name>Mode.prod:
        slack_oauth = env.get("SLACK_OAUTH_MOTHER", None)
        slack_channel = <project_name>SlackChannel.prod
    elif mode == <project_name>Mode.dev:
        slack_oauth = env.get("SLACK_OAUTH_DEV_MOTHER", None)
        slack_channel = <project_name>SlackChannel.dev

    # 3. Parse complex structures
    exchange_to_account_dict: dict[Exchange, list[AccountID]] = {}
    if raw_bybit_account_ids := env.get("BYBIT_ACCOUNT_IDS", ""):
        exchange_to_account_dict[Exchange.bybit] = raw_bybit_account_ids.split(",")

    # 4. Return validated configuration
    return <project_name>Environment(...)
```

---

## Docker Containerization Strategy

### Definition

The Docker strategy uses multi-stage builds with a builder/runner pattern, integrating AWS Secrets Manager through Chamber, and UV package manager for fast, reproducible builds.

### Explanation

This containerization approach optimizes for:

- **Security**: Non-root user, minimal attack surface, secrets management
- **Performance**: Multi-stage builds reduce image size, UV provides fast installs
- **Reproducibility**: Pinned base images, locked dependencies
- **Production Readiness**: Secrets injection, proper signal handling

The pattern separates build-time dependencies from runtime requirements and integrates seamlessly with cloud deployment pipelines.

### Example

**Multi-stage Dockerfile**:

```dockerfile
# Base image with UV package manager
FROM python:3.12.9-slim AS base
COPY --from=ghcr.io/astral-sh/uv:0.7.2 /uv /uvx /bin/

# Builder stage - installs dependencies
FROM base AS builder_base
WORKDIR /repo
COPY packages /repo/packages
COPY $PROJECT_PATH /repo/$PROJECT_PATH
WORKDIR /repo/$PROJECT_PATH
RUN uv pip install . --system

# Runner stage - minimal runtime image
FROM base AS runner
# Create non-root user
RUN adduser --disabled-password --uid $UID --gid $GID $USERNAME
# Copy only runtime artifacts
COPY --from=builder_base /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder_base /usr/local/bin /usr/local/bin
COPY --from=chamber /chamber ${BIN}/chamber
USER $USERNAME
CMD ["/usr/local/bin/entrypoint.sh"]
```

**Container Entrypoint with Secrets**:

```bash
#!/bin/bash --login
set -e
export CHAMBER_AWS_REGION=${CHAMBER_AWS_REGION:-ap-east-1}
export AWS_SECRETS_NAMESPACE=${AWS_SECRETS_NAMESPACE:-projects/<project_name>/prod}
exec chamber exec $AWS_SECRETS_NAMESPACE -- run-<project_name>
```

**Why This Pattern**:

- **Secrets Security**: Chamber injects secrets at runtime, not build time
- **Image Optimization**: Multi-stage builds keep final image minimal
- **Fast Builds**: UV package manager significantly reduces build time
- **Signal Handling**: Proper process management for graceful shutdown

---

## Package Management and Scripts

### Definition

The project uses Hatch with UV installer and defines console scripts that create a clean interface between package management and application execution.

### Explanation

This approach provides:

- **Clean Interface**: Console scripts abstract the internal module structure
- **Development Efficiency**: UV installer provides fast dependency resolution
- **Environment Isolation**: Hatch manages different environments (dev/prod/test)
- **Deployment Consistency**: Same script works in development and production

The pattern ensures that deployment and development use identical entry points while supporting different optimization strategies for each environment.

### Example

**Package Configuration**:

```toml
[project.scripts]
run-<project_name> = "<project_name>.entrypoint:run"

[tool.hatch.envs.prod]
installer = "uv"

[tool.hatch.envs.dev]
installer = "uv"
extra-dependencies = ["mypy"]

[tool.hatch.envs.hatch-test]
parallel = true
retries = 2
extra-dependencies = ["pytest-asyncio", "pytest-cov", "fakeredis"]
```

**Script Flow**:

```
Container CMD → entrypoint.sh → chamber → run-<project_name> → <project_name>.entrypoint:run → main()
```

**Why This Pattern**:

- **Consistency**: Same entry point across all environments
- **Flexibility**: Environment-specific optimizations without changing code
- **Debugging**: Clear path from container to application code
- **Maintenance**: Single point of change for application startup

---

## Key Architectural Benefits

### Separation of Concerns

Each module has a single, well-defined responsibility:

- **entrypoint.py**: Application lifecycle and dependency coordination
- **app.py**: HTTP handling and routing logic
- **environment.py**: Configuration parsing and validation
- **client.py**: Business logic and trading operations

### Async-First Design

The architecture is built around async/await patterns:

- **uvloop**: High-performance event loop
- **AsyncTaskManager**: Coordinated task lifecycle
- **GracefulExit**: Async-aware shutdown handling
- **Quart**: Async web framework

### Production Readiness

The architecture supports enterprise deployment requirements:

- **Security**: Non-root containers, secrets management, authentication
- **Observability**: Structured logging, error tracking, Slack notifications
- **Reliability**: Graceful shutdown, error recovery, health checks
- **Scalability**: Stateless design, external dependencies, clean interfaces

### Development Experience

The pattern optimizes for developer productivity:

- **Fast Iteration**: UV package manager, hot reloading support
- **Clear Structure**: Predictable file organization and naming
- **Type Safety**: Full type hints and mypy integration
- **Testing**: Isolated components, async test support

This architecture pattern provides a robust foundation for async Python applications that need to handle complex lifecycle management, multiple external integrations, and production deployment requirements while maintaining developer productivity and code maintainability.
