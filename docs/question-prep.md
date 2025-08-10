# Exam Question Preparation

## 1. "Explain the async context manager pattern"

**Answer:** The async context manager ensures proper resource lifecycle management in async applications.

**Code Example:**
```python
@asynccontextmanager
async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: Initialize resources
    async with trade_subscriber_context(bind_addr, self.handle_telemetry_message) as sub:
        self.subscriber = sub
        yield  # App runs here
    # Shutdown: Clean up resources automatically
    self.subscriber = None
```

**Key Points:**
- `yield` separates startup from shutdown logic
- Resources are guaranteed to be cleaned up even if errors occur
- FastAPI lifespan events manage the entire application lifecycle
- Async context managers work with `async with` statements

---

## 2. "How do you handle different message types safely?"

**Answer:** Using Pydantic models with type checking and isinstance validation.

**Code Example:**
```python
def handle_telemetry_message(self, msg: TelemetryMsg) -> None:
    try:
        if isinstance(msg, TradeMsg):
            self.metrics.record_trade(side=msg.side, qty=msg.qty, ts=msg.ts)
        elif isinstance(msg, BenchmarkMsg):
            self.metrics.record_benchmark(...)
    except Exception as e:
        self.logger.error(f"Failed to record message {msg}: {e}")
```

**Key Points:**
- `TelemetryMsg` is a Union type of different message types
- `isinstance()` checks ensure type safety at runtime
- Pydantic validates message structure automatically
- Error handling prevents one bad message from crashing the system

---

## 3. "Where do you use NumPy and Pandas?"

**Answer:** For real-time trade data analysis in the metrics pipeline.

**Code Example:**
```python
def get_numpy_stats(self) -> Dict[str, float]:
    quantities = np.array([t['qty'] for t in self.trades])
    return {
        'mean_qty': float(np.mean(quantities)),
        'std_qty': float(np.std(quantities)),
        'max_qty': float(np.max(quantities))
    }

def get_pandas_analysis(self) -> Dict[str, float]:
    df = pd.DataFrame(self.trades)
    buy_trades = df[df['side'] == 'buy']
    return {
        'buy_count': float(len(buy_trades)),
        'buy_volume': float(buy_trades['qty'].sum())
    }
```

**Key Points:**
- NumPy for vectorized mathematical operations on trade quantities
- Pandas for filtering and aggregating trade data by side (buy/sell)
- Analysis runs automatically on each trade message
- Results exposed as Prometheus metrics for monitoring

---

## 4. "How is configuration managed?"

**Answer:** Using Pydantic BaseModel with environment variable loading.

**Code Example:**
```python
class SidecarEnvironment(BaseModel):
    SIDECAR_ZMQ_BIND: str = "tcp://0.0.0.0:5555"
    SIDECAR_HTTP_HOST: str = "0.0.0.0"
    SIDECAR_HTTP_PORT: int = 8001

def get_sidecar_environment() -> SidecarEnvironment:
    load_dotenv()
    return SidecarEnvironment()
```

**Key Points:**
- Pydantic automatically validates types and provides defaults
- `load_dotenv()` reads from `.env` files
- Environment variables override defaults
- Type safety prevents configuration errors at startup

---

## 5. "Explain the ZMQ integration"

**Answer:** Using async context managers for ZMQ socket lifecycle management.

**Code Example:**
```python
@asynccontextmanager
async def trade_subscriber_context(bind_addr: str, handler) -> AsyncGenerator[TradeSubscriber, None]:
    subscriber = TradeSubscriber(bind_addr, handler)
    await subscriber.start()  # Bind socket, start message loop
    try:
        yield subscriber
    finally:
        await subscriber.stop()  # Clean shutdown
```

**Key Points:**
- ZMQ PULL socket binds to receive messages from PUSH publishers
- Async message loop processes incoming JSON trade data
- Context manager ensures socket cleanup even on errors
- Non-blocking I/O allows high-throughput message processing

---

## Technical Architecture Summary

**Data Flow:**
1. Streamlit UI → ZMQ PUSH → JSON message
2. Metrics sidecar → ZMQ PULL → Pydantic validation
3. NumPy/Pandas analysis → Prometheus metrics
4. Grafana visualization

**Modern Python Patterns:**
- Async/await for concurrency
- Type hints and Pydantic for safety
- Context managers for resource management
- Scientific computing with NumPy/Pandas
