# Trading Metrics Architecture

A low-latency, decoupled metrics collection system for trading bots using ZeroMQ message passing and the sidecar pattern.

## Architecture Overview

This project implements **out-of-process telemetry** - a pattern where trading bots emit metrics without any knowledge of collection, aggregation, or storage systems.

```
Trading Bot Instance
    ├── Bot Process (streamlit demo)
    │     ↓ [ipc://trading_metrics]  # fire-and-forget metrics
    ├── Broker Process (TradingApp)
    │     ↓ [tcp://localhost:5560]   # routing & enrichment
    └── Metrics Sidecar Process
          ↓
      [prometheus :8000]              # scrape endpoint
```

## Design Principles

### 1. Complete Separation of Concerns

**Bot Process**: Pure trading logic
- No metric libraries (no prometheus_client dependency)
- No blocking on metric operations
- Simple string messages: `socket.send_string("order_placed:AAPL:145.50")`
- Sub-microsecond metric emission (~1-5μs)

**Broker Process**: Message routing & buffering
- Protocol boundary management (IPC → TCP)
- Message enrichment (timestamps, sequence numbers)
- Failure isolation from downstream systems
- Hot-configurable routing rules

**Metrics Sidecar**: Telemetry complexity
- Prometheus metric registration
- Aggregation and windowing
- Label management
- Export endpoint hosting

### 2. Per-Bot Isolation

Each trading bot runs with its own dedicated metrics infrastructure:

```python
# Bot A → Broker A → Sidecar A → prometheus:8000
# Bot B → Broker B → Sidecar B → prometheus:8001
# No shared state, no contention, independent failure domains
```

Benefits:
- **Performance isolation**: One bot's metric volume doesn't affect another
- **Custom metrics**: Each bot can have unique metric definitions
- **Independent scaling**: Resource allocation per bot's needs
- **Fault isolation**: Sidecar crash doesn't affect trading logic

### 3. Low-Latency First

The architecture prioritizes non-blocking operations:

```python
# Traditional approach (blocking)
prometheus_counter.inc()  # 50-200μs with lock contention

# Our approach (non-blocking)
socket.send_string(msg, zmq.DONTWAIT)  # 1-5μs
```

## Implementation

### Bot Side (minimal footprint)
```python
import zmq
ctx = zmq.Context()
metrics = ctx.socket(zmq.PUSH)
metrics.connect("ipc://trading_metrics")

# In trading loop
metrics.send_string(f"latency:{order.symbol}:{exec_time}", zmq.DONTWAIT)
```

### Broker (TradingApp)
```python
class MetricsBroker:
    def __init__(self):
        self.collector = zmq.PULL  # from bot
        self.publisher = zmq.PUSH  # to sidecar
        
    def route_message(self, msg):
        enriched = {
            'raw': msg,
            'broker_timestamp': time.time_ns(),
            'bot_id': self.bot_id
        }
        self.publisher.send_json(enriched)
```

### Sidecar (metrics registration)
```python
from prometheus_client import Counter, Histogram

class MetricsProcessor:
    def __init__(self):
        self.order_counter = Counter('orders_total', ['symbol'])
        self.exec_histogram = Histogram('execution_time_ms', ['symbol'])
        
    def process(self, msg):
        metric_type, *data = msg.split(':')
        # Complex prometheus logic here, outside critical path
```

## Benefits for Trading Systems

1. **Zero-overhead metrics**: Bot performance unaffected by telemetry
2. **Hot-swappable monitoring**: Change metrics without restarting bots
3. **Protocol flexibility**: Switch from Prometheus to InfluxDB without touching bot code
4. **Grafana integration**: Sidecar can auto-provision dashboards based on registered metrics
5. **Testing isolation**: Run bots without metrics infrastructure in dev

## Project Structure

```
trading-metrics-mvp/
├── trading_app/
│   ├── ui.py              # Demo trading bot (streamlit)
│   ├── main.py            # Broker process launcher
│   └── trading_client.py  # Broker-to-sidecar client
├── metrics_sidecar/
│   ├── sidecar.py        # Metrics collection & prometheus
│   └── processors.py     # Metric type handlers
└── configs/
    └── metrics.yaml       # Metric definitions & routing
```

## Quick Start

```bash
# Terminal 1: Start metrics sidecar
python metrics_sidecar/sidecar.py

# Terminal 2: Start trading app with broker
python trading_app/main.py

# Terminal 3: View metrics
curl localhost:8000/metrics
```

## Future Optimizations

- **Shared memory**: Replace IPC with memory-mapped ring buffers
- **Binary protocol**: Struct packing instead of strings
- **Batch processing**: Accumulate metrics before Prometheus updates
- **Dynamic provisioning**: Auto-generate Grafana dashboards from metric definitions

## Why This Architecture?

Traditional metrics libraries couple your trading logic to monitoring infrastructure. A simple `counter.inc()` can introduce locks, network calls, and unpredictable latency spikes.

This architecture treats metrics as **first-class events** that flow through a dedicated pipeline, ensuring your trading bot maintains consistent, predictable performance while still providing rich telemetry data.

The pattern scales from single-bot development to multi-bot production deployments without code changes - just deploy more sidecar instances.