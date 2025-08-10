from __future__ import annotations

import json
import subprocess
import time
import logging
import asyncio
from typing import Any, List, Optional

import streamlit as st
import streamlit_shadcn_ui as ui
import zmq

from trading_app.environment import TradingAppEnvironment, get_trading_app_environment
from trading_app.features.models import TradeMsg

class UIClass:
    """UI class for the trading app"""

    def __init__(self, env_config: TradingAppEnvironment):
        self.env = env_config
        self.app_socket = self._get_app_socket()


    async def run(self):
        cmd = [
                    "streamlit", "run", str(self.env.UI_PATH),
                    "--server.address", self.env.WEBAPP_HTTP_HOST,
                    "--server.port", str(self.env.WEBAPP_HTTP_PORT),
                ]
        
        self.logger.info(f"Starting Streamlit: {' '.join(cmd)}")
        
        self.ui_process = subprocess.Popen(cmd)

        while not self.tm.stop_signal.is_set(): # while loop on not stop signal
            """ Monitor the UI process """
            if self.ui_process.poll() is not None:
                self.logger.error("Streamlit process died unexpectedly")
                self.tm.stop_signal.set()
                return
            await asyncio.sleep(1) # small delay for async cooperation (simulating actual multi-threaded behavior)

    def _get_app_socket(self) -> zmq.Socket:
        """Get a ZMQ PUSH socket to send commands to the main app."""
        context = zmq.Context.instance()
        socket = context.socket(zmq.PUSH)
        socket.connect(self.env.APP_ZMQ_ADDR)
        return socket


    def _get_events(self) -> List[dict[str, Any]]:
        """Get the events from the UI"""
        if "_events" not in st.session_state:
            st.session_state["_events"] = []
        return st.session_state["_events"]


    def _ui_header(self) -> None:
        st.set_page_config(page_title="Trading Telemetry — Publisher", page_icon="📈", layout="centered")
        st.title("Trading Telemetry — Publisher")
        st.caption(f"UI → PUSH to ZMQ ({self.env.APP_ZMQ_ADDR})")


    def _ui_controls(self) -> None:
        """UI controls"""
        # using `streamlit-shadcn-ui` - no fallback -> error if not available
        try:
            import streamlit_shadcn_ui as ui  # type: ignore
        except Exception:  # pragma: no cover - best-effort styling only
            ui = None  # type: ignore

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            qty = st.number_input("Quantity", min_value=0.0, value=1.0, step=1.0, format="%0.2f", key="qty_input")

        # Buttons
        clicked_buy = False
        clicked_sell = False
        with col2:
            if ui:
                clicked_buy = ui.button("Buy", key="btn_buy", variant="default")
        with col3:
            if ui:
                clicked_sell = ui.button("Sell", key="btn_sell", variant="secondary")

        # Send on click
        side: Optional[str] = None
        if clicked_buy:
            side = "buy"
        elif clicked_sell:
            side = "sell"

        if side is not None:
            self._send_trade(side, float(qty))


    def _send_trade(self, side: str, qty: float) -> None:
        """Send the trade to the app"""
        ts = time.time()
        try:
            msg = TradeMsg(side=side, qty=qty, ts=ts)
        except Exception as e:
            st.error(f"Invalid trade payload: {e}")
            return

        self.app_socket.send_json(msg.model_dump())

        entry = {
            "sent": time.strftime("%H:%M:%S"),
            "payload": msg.model_dump(),
            "addr": self.env.APP_ZMQ_ADDR,
            "ok": True,  # Optimistic: fire-and-forget
        }
        self._get_events().append(entry)
        st.success(f"Sent {side} qty={qty:g} command to the app.")


    def _ui_status(self) -> None:
        st.caption(f"App is listening on: {self.env.APP_ZMQ_ADDR}")


    def _ui_events(self) -> None:
        st.subheader("Event Log")
        events = self._get_events()
        if not events:
            st.info("No events yet — click Buy/Sell above.")
            return

        # Show last 50 events, newest first
        for e in reversed(events[-50:]):
            ok = e.get("ok", False)
            prefix = "✅" if ok else "⚠️"
            st.write(f"{prefix} [{e['sent']}] → {json.dumps(e['payload'])}")


    def main(self):
        """Main function"""
        self._ui_header()
        self._ui_status()
        self._ui_controls()
        self._ui_events()


if __name__ == "__main__":
    env = get_trading_app_environment()
    ui_instance = UIClass(env)
    ui_instance.main()
