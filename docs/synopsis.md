# Trading Telemetry MVP - Synopsis

## Technical Overview

A low-latency trading telemetry system demonstrating real-time data processing and analysis.

### 1. Frontend Architecture
- **Streamlit Framework**: Reactive web application with Python backend
- **Streamlit Shadcn Components**: Modern UI component library integration
- Real-time trade execution interface with immediate message dispatch

### 2. Data Analysis Metrics
- **NumPy**: Vectorized operations for latency calculations and statistical analysis
- **Pandas**: Time-series analysis of trade volumes and frequency patterns

**Key Points for Exam:**
1. **NumPy Usage**: `np.mean()`, `np.std()`, `np.max()` for vectorized calculations on trade quantities
2. **Pandas Usage**: DataFrame filtering (`df[df['side'] == 'buy']`) and aggregation (`.sum()`) 
3. **Integration**: Analysis runs automatically on each trade, exposing results as Prometheus metrics
4. **Real Data**: Processes actual ZMQ trade messages, not synthetic data

### 3. Message Transport Layer
- **PyZMQ**: Zero-copy message passing with PUSH/PULL pattern
- Asynchronous, non-blocking communication between services
- JSON serialization for structured trade event data

### 4. Application Architecture
- **pyproject.toml**: Dependency management and build configuration
- **entrypoint.py**: Application bootstrap with dependency injection
- **environment.py**: Configuration management with environment variables
- **app.py**: Core business logic and service orchestration

### 5. Concurrency Management
- **AsyncTaskManager**: Coordinated async task lifecycle management
- Non-blocking I/O operations for high-throughput message processing

### 6. Modern Toolchain
- **uv package manager**: Fast dependency resolution and virtual environment management
- Improved build times and reproducible environments

## Technical Value
- Demonstrates real-time data processing with scientific Python stack
- Scalable architecture for high-frequency trading systems
- Modern Python development practices and tooling