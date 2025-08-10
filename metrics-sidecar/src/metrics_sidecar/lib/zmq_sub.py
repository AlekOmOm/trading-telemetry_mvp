from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

import zmq
import zmq.asyncio

from .models import TradeMsg

logger = logging.getLogger(__name__)


class TradeSubscriber:
    """ZMQ PULL subscriber for trade messages."""

    def __init__(self, bind_addr: str, handler: Callable[[TradeMsg], None]) -> None:
        self.bind_addr = bind_addr
        self.handler = handler
        self._ctx: zmq.asyncio.Context | None = None
        self._sock: zmq.asyncio.Socket | None = None
        self._running = False

    async def start(self) -> None:
        """Start the ZMQ subscriber."""
        if self._running:
            return
            
        self._ctx = zmq.asyncio.Context()
        self._sock = self._ctx.socket(zmq.PULL)
        self._sock.bind(self.bind_addr)
        self._running = True
        
        logger.info(f"Trade subscriber started on {self.bind_addr}")
        
        # Start the message loop
        asyncio.create_task(self._message_loop())

    async def stop(self) -> None:
        """Stop the ZMQ subscriber."""
        if not self._running:
            return
            
        self._running = False
        
        if self._sock:
            self._sock.close()
        if self._ctx:
            self._ctx.term()
            
        logger.info("Trade subscriber stopped")

    async def _message_loop(self) -> None:
        """Main message processing loop."""
        while self._running and self._sock:
            try:
                # Non-blocking receive with timeout
                try:
                    raw_msg = await asyncio.wait_for(
                        self._sock.recv_string(), timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue
                    
                await self._process_message(raw_msg)
                
            except Exception as e:
                logger.error(f"Error in message loop: {e}")
                await asyncio.sleep(0.1)

    async def _process_message(self, raw_msg: str) -> None:
        """Process a single trade message."""
        try:
            payload = json.loads(raw_msg)
            trade_msg = TradeMsg(**payload)
            
            logger.debug(f"Received trade: {trade_msg}")
            
            # Call the handler
            self.handler(trade_msg)
            
        except Exception as e:
            logger.error(f"Failed to process message '{raw_msg}': {e}")


@asynccontextmanager
async def trade_subscriber_context(
    bind_addr: str, handler: Callable[[TradeMsg], None]
) -> AsyncGenerator[TradeSubscriber, None]:
    """Context manager for trade subscriber."""
    subscriber = TradeSubscriber(bind_addr, handler)
    try:
        await subscriber.start()
        yield subscriber
    finally:
        await subscriber.stop()