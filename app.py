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
    .win-rate-container { display: flex; width: 100%; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; font-size: 0.9rem; font-weight: bold; color: white; line-height: 30px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .wr-home { background-color: #e74c3c; text-align: center; }
    .wr-draw { background-color: #95a5a6; text-align: center; }
    .wr-away { background-color: #3498db; text-align: center; }
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

# (1) PDF 생성 클래스 (괄호 오류 수정됨)
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
        
        # 승률 바 그리기
        total_w = 190
        w_h = total_w * (wr_h / 100)
        w_d = total_w * (wr_d / 100)
        w_a = total_w * (wr_a / 100)
        
        self.set_fill_color(231, 76, 60)
        self.cell(w_h, 8, f'{wr_h}%', 1, 0, 'C', 1)
        
        self.set_fill_color(149, 165, 166)
        self.cell(w_d, 8, f'{wr_d}%', 1, 0, 'C', 1)
        
        self.set_fill_color(52, 152, 219)
        self.cell(w_a, 8, f'{wr_a}%', 1, 1, 'C', 1)
        self.ln(10)

        # 팩트 요약
        self.set_font_size(10)
        self.multi_cell(0, 6, f"[상대전적] {fact1}\n[홈팀기세] {fact2}\n[원정기세] {fact3}")
        self.ln(5)
        
        # 상세 분석
        self.multi_cell(0, 6, analysis_text)
        self.ln(10)

def create_pdf(analysis_results):
    pdf = PDFReport()
    pdf.add_page()
    if not os.path.exists('NanumGothic.ttf'):
        st.warning("⚠️ 'NanumGothic.ttf' 폰트가 없어 PDF 한글이 깨질 수 있습니다.")
    for res in analysis_results:
        pdf.chapter_body(
            res['idx'], res['t_a'], res['t_b'], 
            res['wr_h'], res['wr_d'], res['wr_a'],
            res['fact1'], res['fact2'], res['fact3'],
            res['text']
        )
    return pdf.output(dest='S').encode('latin1')

# (2) 이미지 인식 (모델명 Flash로 고정)
def extract_matches_from_image(image, api_key):
    genai.configure(api_key=api_key)
    # [수정] Pro-002 대신 Flash 사용
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    이 이미지는 경기 일정표다. 홈팀과 원정팀 이름을 JSON으로 추출해.
    형식: [{"team_a": "팀명", "team_b": "팀명"}, ...]
    """
    try:
        response = model.generate_content([prompt, image])
        text = response.text
        json_str = text[text.find('['):text.rfind(']')+1]
        return json.loads(json_str)
    except: return []

# (3) 괘 계산 및 UI
def draw_lines_html(lines_list):
    html = '<div class="hex-box">'
    for val in reversed(lines_list):
        cls = "yang" if val == '1' else "yin"
        html += f'<div class="{cls}"></div>'
    html += '</div>'
    return html

def calculate_hex(user_inputs):
    origin, changed, moving_cnt = [], [], 0
    for item in user_inputs:
        val = item['val']
        is_moving = item['is_moving']
        origin.append(val)
        if is_moving:
            moving_cnt += 1
            changed.append('2' if val == '1' else '1')
        else: changed.append(val)
    def make_key(ls): return "".join(ls[0:3]) + "-" + "".join(ls[3:6])
    o_key, c_key = make_key(origin), make_key(changed)
    return {"o_name": get_hex_name(o_key), "c_name": get_hex_name(c_key), "o_visual": draw_lines_html(origin), "c_visual": draw_lines_html(changed), "moving": moving_cnt}

def render_hex_input_ui(key_prefix, label):
    st.markdown(f"**{label}**")
    inputs = [] 
    temp_inputs = {} 
    for i in range(6, 0, -1):
        c1, c2, c3 = st.columns([0.8, 2.5, 1.5])
        with c1: st.caption(f"{i}효")
        with c2: val = st.radio(f"음양_{key_prefix}_{i}", ["양(1)", "음(2)"], horizontal=True, key=f"r_{key_prefix}_{i}", label_visibility="collapsed")
        with c3: move = st.checkbox("변효", key=f"c_{key_prefix}_{i}")
        temp_inputs[i] = {'val': '1' if "양" in val else '2', 'is_moving': move}
    for i in range(1, 7): inputs.append(temp_inputs[i])
    return inputs

# --- 4. 메인 앱 ---

with st.sidebar:
    st.header("⚙️ 설정")
    # API 키 처리 (문법 오류 수정됨)
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

st.title("💎 GEMS Pro: 승부예측 & 리포트")

if 'matches_from_image' not in st.session_state:
    st.session_state.matches_from_image = []

# 1. 이미지 업로드
with st.expander("📷 경기 일정 스크린샷으로 자동 입력 (Click)", expanded=True):
    uploaded_file = st.file_uploader("경기 목록 이미지 업로드", type=["jpg", "png", "jpeg"])
    if uploaded_file and st.button("이미지 분석"):
        if not api_key: st.error("API 키 필요")
        else:
            with st.spinner("이미지 분석 중..."):
                img = Image.open(uploaded_file)
                data = extract_matches_from_image(img, api_key)
                if data:
                    st.session_state.matches_from_image = data
                    st.success(f"{len(data)}경기 인식 완료!")
                else:
                    st.warning("인식된 경기가 없습니다.")

# 2. 입력창 생성
count = len(st.session_state.matches_from_image) if st.session_state.matches_from_image else 1
num_matches = st.number_input("분석할 경기 수", 1, 20, count)
all_matches = []

st.divider()

for i in range(num_matches):
    with st.container(border=True):
        da = st.session_state.matches_from_image[i]['team_a'] if i < len(st.session_state.matches_from_image) else ""
        db = st.session_state.matches_from_image[i]['team_b'] if i < len(st.session_state.matches_from_image) else ""
        
        st.subheader(f"Match {i+1}")
        c1, c2 = st.columns(2)
        ta = c1.text_input("홈팀", da, key=f"ta_{i}")
        tb = c2.text_input("원정팀", db, key=f"tb_{i}")
        
        c3, c4 = st.columns(2)
        # [수정됨] 문법 오류 수정 (with 구문 분리)
        with c3:
            inp_a = render_hex_input_ui(f"ma_{i}", f"🏠 {ta} 괘")
        with c4:
            inp_b = render_hex_input_ui(f"mb_{i}", f"✈️ {tb} 괘")
        
        all_matches.append({"idx": i+1, "ta": ta, "tb": tb, "inp_a": inp_a, "inp_b": inp_b})

# 3. 분석 실행
if st.button("🚀 GEMS 통합 분석 시작", type="primary"):
    if not api_key: st.error("API 키 필요")
    else:
        genai.configure(api_key=api_key)
        pdf_data = []
        
        for m in all_matches:
            ra = calculate_hex(m['inp_a'])
            rb = calculate_hex(m['inp_b'])
            ta, tb = m['ta'] or "홈", m['tb'] or "원정"
            
            st.markdown(f"### 🏁 Match {m['idx']}: {ta} vs {tb}")
            
            with st.spinner("구글 검색 및 주역 분석 중..."):
                try:
                    tools = [{"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "dynamic", "dynamic_threshold": 0.7}}}]
                    # [수정] Pro-002 대신 Flash 사용
                    model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
                    
                    prompt = f"""
                    GEMS 분석가로서 '{ta} vs {tb}' 경기를 구글 검색하고 주역 데이터({ra['o_name']}->{ra['c_name']}, {rb['o_name']}->{rb['c_name']})와 통합 분석하라.
                    
                    반드시 아래 JSON 포맷으로만 응답할 것 (마크다운 코드블럭 없이 텍스트로만):
                    {{
                        "wr_h": 45, "wr_d": 25, "wr_a": 30,
                        "fact_h2h": "상대전적 요약 (예: 최근 5전 2승 3패)",
                        "fact_home": "홈팀 최근 기세 요약 (예: 3연승 중)",
                        "fact_away": "원정팀 최근 기세 요약 (예: 부상자 다수)",
                        "summary": "종합 분석 내용 (300자 내외)"
                    }}
                    """
                    resp = model.generate_content(prompt).text
                    
                    try:
                        import json
                        json_str = resp.strip()
                        if "```" in json_str:
                            json_str = json_str.split("```")[1].replace("json", "").strip()
                        data = json.loads(json_str)
                    except:
                        data = {"wr_h": 33, "wr_d": 33, "wr_a": 34, "fact_h2h": "-", "fact_home": "-", "fact_away": "-", "summary": resp}

                    # 1. 현실 데이터 시각화
                    c1, c2, c3 = st.columns(3)
                    c1.markdown(f"<div class='fact-box'><div class='fact-title'>🆚 상대전적</div><div class='fact-value'>{data.get('fact_h2h','-')}</div></div>", unsafe_allow_html=True)
                    c2.markdown(f"<div class='fact-box'><div class='fact-title'>📈 {ta} 기세</div><div class='fact-value'>{data.get('fact_home','-')}</div></div>", unsafe_allow_html=True)
                    c3.markdown(f"<div class='fact-box'><div class='fact-title'>📉 {tb} 기세</div><div class='fact-value'>{data.get('fact_away','-')}</div></div>", unsafe_allow_html=True)

                    # 2. 승률 바
                    wh, wd, wa = data.get('wr_h',33), data.get('wr_d',33), data.get('wr_a',34)
                    st.markdown(f"""
                    <div class="win-rate-container">
                        <div class="wr-home" style="width:{wh}%">{ta} {wh}%</div>
                        <div class="wr-draw" style="width:{wd}%">무 {wd}%</div>
                        <div class="wr-away" style="width:{wa}%">{tb} {wa}%</div>
                    </div>
                    """, unsafe_allow_html=True)

                    # 3. 분석글 및 괘 시각화
                    st.info(data.get('summary', ''))
                    
                    cv1, cv2 = st.columns(2)
                    with cv1: 
                        st.caption(f"{ta}: {ra['o_name']} ➜ {ra['c_name']}")
                        st.markdown(ra['o_visual'], unsafe_allow_html=True)
                    with cv2: 
                        st.caption(f"{tb}: {rb['o_name']} ➜ {rb['c_name']}")
                        st.markdown(rb['o_visual'], unsafe_allow_html=True)

                    pdf_data.append({
                        "idx": m['idx'], "t_a": ta, "t_b": tb,
                        "wr_h": wh, "wr_d": wd, "wr_a": wa,
                        "fact1": data.get('fact_h2h','-'),
                        "fact2": data.get('fact_home','-'),
                        "fact3": data.get('fact_away','-'),
                        "text": data.get('summary','')
                    })

                except Exception as e: st.error(f"오류: {e}")
            st.divider()

        if pdf_data:
            st.success("완료! 리포트를 다운로드하세요.")
            st.download_button("📄 PDF 리포트 다운로드", create_pdf(pdf_data), "GEMS_Report.pdf", "application/pdf")