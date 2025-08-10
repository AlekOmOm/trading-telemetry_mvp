from __future__ import annotations

import json
import time
from typing import Any, List, Optional

import streamlit as st

from trading_app.environment import get_trading_app_environment
from trading_app.models import TradeMsg
from trading_app.zmq_pub import TradePublisher


def _get_publisher() -> TradePublisher:
    if "_publisher" not in st.session_state:
        addr = get_trading_app_environment().WEBAPP_ZMQ_ADDR
        st.session_state["_publisher"] = TradePublisher(addr)
    return st.session_state["_publisher"]


def _get_events() -> List[dict[str, Any]]:
    if "_events" not in st.session_state:
        st.session_state["_events"] = []
    return st.session_state["_events"]


def _ui_header() -> None:
    st.set_page_config(page_title="Trading Telemetry — Publisher", page_icon="📈", layout="centered")
    st.title("Trading Telemetry — Publisher")
    st.caption("Streamlit UI → ZMQ PUSH → Sidecar (Prometheus)")


def _ui_controls() -> None:
    # Prefer streamlit-shadcn-ui if available; fall back to native widgets.
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
        else:
            clicked_buy = st.button("Buy", key="btn_buy")
    with col3:
        if ui:
            clicked_sell = ui.button("Sell", key="btn_sell", variant="secondary")
        else:
            clicked_sell = st.button("Sell", key="btn_sell")

    # Send on click
    side: Optional[str] = None
    if clicked_buy:
        side = "buy"
    elif clicked_sell:
        side = "sell"

    if side is not None:
        _send_trade(side, float(qty))


def _send_trade(side: str, qty: float) -> None:
    ts = time.time()
    try:
        msg = TradeMsg(side=side, qty=qty, ts=ts)
    except Exception as e:
        st.error(f"Invalid trade payload: {e}")
        return

    pub = _get_publisher()
    result = pub.publish_json(json.loads(msg.model_dump_json()))

    entry = {
        "sent": time.strftime("%H:%M:%S"),
        "payload": msg.model_dump(),
        "addr": pub.addr,
        "ok": result.ok,
        "error": result.error,
        "elapsed_ms": result.elapsed_ms,
    }
    _get_events().append(entry)

    if result.ok:
        st.success(f"Sent {side} qty={qty:g} to {pub.addr}")
    else:
        st.warning(f"Send failed: {result.error}")


def _ui_status() -> None:
    pub = _get_publisher()
    st.caption(f"ZMQ address: {pub.addr}")


def _ui_events() -> None:
    st.subheader("Event Log")
    events = _get_events()
    if not events:
        st.info("No events yet — click Buy/Sell above.")
        return

    # Show last 50 events, newest first
    for e in reversed(events[-50:]):
        ok = e.get("ok", False)
        prefix = "✅" if ok else "⚠️"
        st.write(f"{prefix} [{e['sent']}] → {json.dumps(e['payload'])}")


def main() -> None:
    _ui_header()
    _ui_status()
    _ui_controls()
    _ui_events()


if __name__ == "__main__":
    main()
