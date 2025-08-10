# Latency Isolation Architecture

This document outlines the multi-process architecture designed to isolate time-sensitive components from communication latency, particularly for metrics reporting.

## Core Architecture

The application is structured into three main components orchestrated by `entrypoint.py`:

1.  **Main Application (`app.py`)**: The central process that runs an `asyncio` event loop. It serves as a message broker.
2.  **UI/Bot Process (`features/ui.py`)**: A completely separate OS process launched via `subprocess.Popen`. In the current implementation, this runs the Streamlit UI (`streamlit_main.py`).
3.  **ZMQ Messaging Bridge**: Communication between the main application and the UI/Bot process occurs over a high-speed, local ZeroMQ (ZMQ) `PUSH`/`PULL` socket.

## How Latency is Managed

The key to this design is decoupling the user-facing (or latency-sensitive) process from the potentially slow, network-bound tasks.

1.  **Message Origination**: The UI/Bot process generates a message (e.g., a user action or a trade signal).
2.  **Fire-and-Forget Send**: It sends this message to the main application via a local ZMQ socket. This is an extremely fast, non-blocking operation. The UI/Bot process is immediately free to continue its work without waiting for the message to be processed or forwarded.
3.  **Asynchronous Forwarding**: The main application's `run_main_loop` receives the message and uses the `TradingClient` to forward it to the external `metrics-sidecar`.
4.  **Precise Measurement**: The latency of the external communication (`client.py`'s `_sock.send_string` call) is the only part that is measured. This is the primary source of unpredictable latency (network, receiver load).

This ensures that the performance of the UI/Bot is not affected by the performance of the metrics pipeline.

## Production Scenario: Trading Bot

This architecture is directly applicable to running a production trading bot.

- The `UIClass` would be replaced by a `TradingBot` class.
- This `TradingBot` class would launch the core trading algorithm in a separate process, just as the UI is launched now.
- The trading bot would publish critical events (e.g., "order placed," "signal detected") to the main application process via the same ZMQ bridge.
- The main application forwards these events to the `metrics-sidecar` for monitoring, logging, and analysis.

**Advantage**: The core trading bot's event loop is never blocked by I/O operations related to metrics. It can react to market data with the lowest possible latency, as the reporting is handled asynchronously and in a separate process.
