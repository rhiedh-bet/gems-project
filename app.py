import streamlit as st
import google.generativeai as genai
import requests
import pandas as pd
from datetime import datetime
import re
from PIL import Image
import json
from fpdf import FPDF
import os

# --- 1. 페이지 설정 ---
st.set_page_config(layout="wide", page_title="GEMS: Pro Sports Analysis")

# 스타일 CSS
st.markdown("""
<style>
    .yang { background-color: #2c3e50; height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .yin { background: linear-gradient(to right, #2c3e50 42%, transparent 42%, transparent 58%, #2c3e50 58%); height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .hex-box { width: 50px; padding: 5px; border: 1px solid #ddd; background: #fff; margin: 0 auto; display: flex; flex-direction: column; justify-content: center; }
    
    /* 승률 바 */
    .win-rate-container { display: flex; width: 100%; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; font-size: 0.9rem; font-weight: bold; color: white; line-height: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .wr-home { background-color: #e74c3c; text-align: center; }
    .wr-draw { background-color: #95a5a6; text-align: center; }
    .wr-away { background-color: #3498db; text-align: center; }
    
    /* 현실 데이터 3단 박스 */
    .fact-box { background-color: #f1f3f5; padding: 15px; border-radius: 10px; border: 1px solid #e9ecef; text-align: center; height: 100%; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .fact-title { font-size: 0.85rem; color: #495057; margin-bottom: 8px; font-weight: bold; text-transform: uppercase; }
    .fact-value { font-size: 1.1rem; font-weight: 800; color: #212529; word-break: keep-all; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 및 유틸리티 ---
RAW_DATA = """111-111 중천건 111-112 택천쾌 111-121 화천대유 111-122 뇌천대장 111-211 풍천소축 111-212 수천수 111-221 산천대축 111-222 지천태 112-111 천택리 112-112 태위택 112-121 화택규 112-122 뇌택귀매 112-211 풍택중부 112-212 수택절 112-221 산택손 112-222 지택림 121-111 천화동인 121-112 택화혁 121-121 중화리 121-122 뇌화풍 121-211 풍화가인 121-212 수화기제 121-221 산화비 121-222 지화명이 122-111 천뢰무망 122-112 택뢰수 122-121 화뢰서합 122-122 진위뢰 122-211 풍뢰익 122-212 수뢰둔 122-221 산뢰이 122-222 지뢰복 211-111 천풍구 211-112 택풍대과 211-121 화풍정 211-122 뇌풍항 211-211 중풍손 211-212 수풍정 211-221 산풍고 211-222 지풍승 212-111 천수송 212-112 택수곤 212-121 화수미제 212-122 뇌수해 212-211 풍수환 212-212 감위수 212-221 산수몽 212-222 지수사 221-111 천산돈 221-112 택산함 221-121 화산려 221-122 뇌산소과 221-211 풍산점 221-212 수산건 221-221 간위산 221-222 지산겸 222-111 천지비 222-112 택지췌 222-121 화지진 222-122 뇌지예 222-211 풍지관 222-212 수지비 222-221 산지박 222-222 중지곤"""
HEX_DB = {}
tokens = RAW_DATA.split()
for i in range(0, len(tokens), 2): HEX_DB[tokens[i]] = tokens[i+1]
def get_hex_name(key): return HEX_DB.get(key, "미지")

# --- 3. 핵심 기능 함수들 ---

# (1) PDF 생성 클래스
class PDFReport(FPDF):
    def header(self):
        font_path = 'NanumGothic.ttf'
        if os.path.exists(font_path):
            self.add_font('Nanum', '', font_path, uni=True)
            self.set_font('Nanum', '', 10)
        else:
            self.set_font('Arial', '', 10)
        self.cell(0, 10, 'GEMS Sports Analysis Report', 0, 1, 'C')
        self.ln(5)

    def chapter_body(self, match_idx, t_a, t_b, wr_h, wr_d, wr_a, fact1, fact2, fact3, analysis_text):
        self.set_font_size(14)
        self.cell(0, 10, f'Match {match_idx}: {t_a} vs {t_b}', 0, 1, 'L')
        self.ln(2)
        
        # 승률 바
        total_w = 190
        w_h = total_w * (wr_h / 100)
        w_d = total_w * (wr_d / 100)
        w_a = total_w * (wr_a / 100)
        self.set_fill_color(231, 76, 60)
        self.cell(w_h, 8, f'{wr_h}%', 1, 0, 'C', 1)
        self.set_fill_color(149, 165, 166)
        self.cell(w_d, 8, f'{wr_d}%', 1