from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry

from .environment import sidecar_zmq_bind
from lib.metrics import TradingMetrics
from lib.models import TradeMsg
from lib.zmq_sub import trade_subscriber_context, TradeSubscriber

logger = logging.getLogger(__name__)

# Global state
registry = CollectorRegistry()
metrics = TradingMetrics(registry)
subscriber: TradeSubscriber | None = None


def handle_trade_message(trade_msg: TradeMsg) -> None:
    """Handle incoming trade messages by updating metrics."""
    try:
        metrics.record_trade(
            side=trade_msg.side,
            qty=trade_msg.qty,
            ts=trade_msg.ts
        )
        logger.info(f"Recorded trade: {trade_msg.side} qty={trade_msg.qty}")
    except Exception as e:
        logger.error(f"Failed to record trade {trade_msg}: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """FastAPI lifespan events."""
    global subscriber
    
    # Startup
    bind_addr = sidecar_zmq_bind()
    logger.info(f"Starting trade subscriber on {bind_addr}")
    
    async with trade_subscriber_context(bind_addr, handle_trade_message) as sub:
        subscriber = sub
        logger.info("Metrics sidecar started")
        yield
        
    # Shutdown
    subscriber = None
    logger.info("Metrics sidecar stopped")


app = FastAPI(
    title="Trading Telemetry - Metrics Sidecar",
    description="ZMQ subscriber that exposes trading metrics for Prometheus",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/metrics", response_class=PlainTextResponse)
async def get_metrics():
    """Prometheus metrics endpoint."""
    return generate_latest(registry)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    is_healthy = subscriber is not None
    return {
        "status": "healthy" if is_healthy else "unhealthy",
        "subscriber_running": is_healthy,
        "zmq_bind_addr": sidecar_zmq_bind()
    }
