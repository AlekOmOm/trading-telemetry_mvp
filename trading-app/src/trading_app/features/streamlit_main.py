"""Isolated Streamlit entry point - no asyncio context pollution"""
import streamlit as st
import streamlit_shadcn_ui as ui
from trading_app.environment import get_trading_app_environment
from trading_app.features.ui_components import StreamlitUI

if __name__ == "__main__":
    env = get_trading_app_environment()
    ui_instance = StreamlitUI(env)
    ui_instance.main()