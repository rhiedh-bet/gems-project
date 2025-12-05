import streamlit as st
import google.generativeai as genai
import json
from datetime import datetime

# --- 1. 페이지 설정 ---
st.set_page_config(layout="wide", page_title="GEMS: Master Prompt Builder")

# --- 2. 스타일 CSS ---
st.markdown("""
<style>
    .yang { background-color: #2c3e50; height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .yin { background: linear-gradient(to right, #2c3e50 42%, transparent 42%, transparent 58%, #2c3e50 58%); height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .hex-box { width: 70px; padding: 10px; border: 1px solid #ddd; background: #fff; margin: 0 auto; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .win-bar-container { display: flex; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; color: white; font-weight: bold; line-height: 30px; text-align: center; font-size: 0.9rem; }
    .wb-home { background-color: #e74c3c; }
    .wb-draw { background-color: #95a5a6; }
    .wb-away { background-color: #3498db; }
    .guide-text { background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 (64괘 매핑) ---
RAW_DATA = """111-111 중천건 111-112 택천쾌 111