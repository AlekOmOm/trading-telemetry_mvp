from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from fastapi import FastAPI, APIRouter
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, CollectorRegistry

from .environment import SidecarEnvironment, get_sidecar_environment
from .lib.metrics import TradingMetrics
from .lib.models import TradeMsg
from .lib.zmq_sub import trade_subscriber_context, TradeSubscriber


class MetricsSidecar:
    """Metrics sidecar with async task coordination
    
    Args:
        env_config: SidecarEnvironment
        logger: logging.Logger
        
    responsibilities:
        - ZMQ subscriber for trade messages
        - Expose Prometheus metrics
        - FastAPI app management
    """
    
    def __init__(self, env_config: SidecarEnvironment, logger: logging.Logger):
        self.env_config = env_config
        self.logger = logger
        self.registry = CollectorRegistry()
        self.metrics = TradingMetrics(self.registry)
        self.subscriber: Optional[TradeSubscriber] = None
        self.app = self.create_app()

    def handle_trade_message(self, trade_msg: TradeMsg) -> None:
        """Handle incoming trade messages by updating metrics."""
        try:
            self.metrics.record_trade(
                side=trade_msg.side,
                qty=trade_msg.qty,
                ts=trade_msg.ts
            )
            self.logger.info(f"Recorded trade: {trade_msg.side} qty={trade_msg.qty}")
        except Exception as e:
            self.logger.error(f"Failed to record trade {trade_msg}: {e}")

    @asynccontextmanager
    async def lifespan(self, app: FastAPI) -> AsyncGenerator[None, None]:
        """FastAPI lifespan events."""
        bind_addr = self.env_config.SIDECAR_ZMQ_BIND
        self.logger.info(f"Starting trade subscriber on {bind_addr}")
        
        async with trade_subscriber_context(bind_addr, self.handle_trade_message) as sub:
            self.subscriber = sub
            self.logger.info("Metrics sidecar started")
            yield
            
        self.subscriber = None
        self.logger.info("Metrics sidecar stopped")

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI app instance."""
        app = FastAPI(
            title="Trading Telemetry - Metrics Sidecar",
            description="ZMQ subscriber that exposes trading metrics for Prometheus",
            version="0.1.0",
            lifespan=self.lifespan
        )
        
        router = APIRouter()
        
        @router.get("/metrics", response_class=PlainTextResponse)
        async def get_metrics():
            return generate_latest(self.registry)

        @router.get("/health")
        async def health_check():
            is_healthy = self.subscriber is not None
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "subscriber_running": is_healthy,
                "zmq_bind_addr": self.env_config.SIDECAR_ZMQ_BIND
            }
            
        app.include_router(router)
        return app


env_config = get_sidecar_environment()
logger = logging.getLogger(__name__)
sidecar = MetricsSidecar(env_config, logger)
app = sidecar.app
