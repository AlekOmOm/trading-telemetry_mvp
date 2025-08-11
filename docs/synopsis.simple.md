# trading telemetry mvp – synopsis

## overview  
a prototype low-latency trading telemetry system demonstrating real-time market data ingestion, analysis, and metric exposure. architecture emphasizes minimal latency, scalability, and clarity of data flow from ingestion to analytics output.

---

## 1. frontend  
- **streamlit**: reactive web app for real-time data visualization and interaction.  
- **shadcn ui integration**: modern, responsive components for trade execution interface.  
- supports immediate dispatch of trade commands and instant feedback from backend.

---

## 2. analytics layer  
- **numpy**: vectorized computations for low-latency calculations (`mean`, `std deviation`, `max`) on trade quantities.  
- **pandas**: time-series analysis of trade activity — filtering (`df[df['side']=="buy"]`) and aggregation (`.sum()`) of volumes.  
- analysis is triggered automatically per incoming trade and exposed as **prometheus** metrics.

**exam focus**:  
1. streamlit process in subprocess with zmq messaging to main app (trading_app/app.py) with `ui_process` handling for graceful exitting.
2. data analysis: numpy for bulk operations, pandas for filtering/aggregation. 
3. architecture: zmq for decoupling, pydantic for structured messaging, task_manager.py for async task coordination.
4. integration point: metrics pipeline from raw trade → in-memory df → prometheus metrics.

---

## 3. message transport layer  
- **pyzmq**: high-performance zero-copy messaging, chosen push/pull message (pipeline) for service decoupling - aim was complete decoupling of ui (streamlit process) from main app (trading_app/app.py) which spawns the subprocess.
- asynchronous, non-blocking event flow (while loop with utils: `task_manager` and `exit_handler` for handling async graceful shutdowns).  
- trade events serialized to json for structured processing and interoperability (with pydantic models for validation)
- real zmq trade messages used, ensuring realistic latency data.
  - context: this is simple zmq project with async process handling, but in production environment that latency data and analysis would be more complex.

---

## 4. application structure  
- **pyproject.toml**: dependencies, build config.  
- **entrypoint.py**: bootstrap + dependency injection.  
- **environment.py**: env-var based configuration management.  
- **app.py**: orchestrates business logic and service coordination.

---

## 5. concurrency  
- **asynctaskmanager**: manages async tasks, startup/shutdown order, and error handling.  
- non-blocking i/o to sustain throughput under burst traffic.

---

## 6. toolchain  
- **uv**: fast dependency resolution, reproducible virtual envs, improved build times.

---

## technical value  
- demonstrates scientific python stack in real-time analytics context.  
- scalable design principles applicable to high-frequency trading.  
- integrates modern python dev practices: async, dependency injection, metrics-driven monitoring.