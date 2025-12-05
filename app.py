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
    .arrow { font-size: 1.2rem; color: #8e44ad; text-align: center; margin-top: 20px; }
    .win-rate-container { display: flex; width: 100%; height: 25px; border-radius: 12px; overflow: hidden; margin: 10px 0; font-size: 0.8rem; font-weight: bold; color: white; line-height: 25px; }
    .wr-home { background-color: #e74c3c; text-align: center; }
    .wr-draw { background-color: #95a5a6; text-align: center; }
    .wr-away { background-color: #3498db; text-align: center; }
    .stat-box { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #eee; text-align: center; height: 100%; }
    .stat-title { font-size: 0.8rem; color: #666; margin-bottom: 5px; }
    .stat-value { font-size: 1rem; font-weight: bold; color: #333; }
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
        # 폰트 로드 (NanumGothic.ttf 파일이 있어야 함)
        font_path = 'NanumGothic.ttf'
        if os.path.exists(font_path):
            self.add_font('Nanum', '', font_path, uni=True)
            self.set_font('Nanum', '', 10)
        else:
            self.set_font('Arial', '', 10) # 폰트 없으면 영어만 나옴
            
        self.cell(0, 10, 'GEMS Sports Analysis Report', 0, 1, 'C')
        self.ln(5)

    def chapter_body(self, match_idx, t_a, t_b, wr_h, wr_d, wr_a, analysis_text):
        self.set_font_size(14)
        self.cell(0, 10, f'Match {match_idx}: {t_a} vs {t_b}', 0, 1, 'L')
        self.ln(2)
        
        # 승률 바 그리기 (PDF 도형)
        total_w = 190 # 전체 너비
        w_h = total_w * (wr_h / 100)
        w_d = total_w * (wr_d / 100)
        w_a = total_w * (wr_a / 100)
        
        self.set_fill_color(231, 76, 60) # Red
        self.cell(w_h, 8, f'{wr_h}%', 1, 0, 'C', 1)
        self.set_fill_color(149, 165, 166) # Grey
        self.cell(w_d, 8, f'{wr_d}%', 1, 0, 'C', 1)
        self.set_fill_color(52, 152, 219) # Blue
        self.cell(w_a, 8, f'{wr_a}%', 1, 1, 'C', 1)
        self.ln(5)
        
        self.set_font_size(10)
        self.multi_cell(0, 5, analysis_text)
        self.ln(10)

def create_pdf(analysis_results):
    pdf = PDFReport()
    pdf.add_page()
    
    # 폰트 확인
    if not os.path.exists('NanumGothic.ttf'):
        st.warning("⚠️ 'NanumGothic.ttf' 폰트 파일이 없어 PDF 한글이 깨질 수 있습니다.")
    
    for res in analysis_results:
        pdf.chapter_body(
            res['idx'], res['t_a'], res['t_b'], 
            res['wr_h'], res['wr_d'], res['wr_a'], 
            res['text']
        )
    return pdf.output(dest='S').encode('latin1')

# (2) 이미지에서 경기 정보 추출 (Gemini Vision)
def extract_matches_from_image(image, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-pro')
    
    prompt = """
    이 이미지는 스포츠 경기 일정표다. 
    이미지에 있는 모든 매치업의 '홈팀 이름'과 '원정팀 이름'을 추출해서 
    다음과 같은 JSON 형식으로만 출력해. 다른 말은 하지 마.
    [{"team_a": "토트넘", "team_b": "아스날"}, {"team_a": "맨유", "team_b": "첼시"}]
    """
    try:
        response = model.generate_content([prompt, image])
        text = response.text
        # JSON 부분만 추출
        json_str = text[text.find('['):text.rfind(']')+1]
        return json.loads(json_str)
    except Exception as e:
        st.error(f"이미지 인식 실패: {e}")
        return []

# (3) 괘 계산 및 UI 함수들 (이전과 동일)
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
    try: api_key = st.secrets["GEMINI_API_KEY"]
    except: api_key = st.text_input("Gemini API Key", type="password")

st.title("💎 GEMS Pro: 승부예측 & 리포트")

# [세션 상태 관리] 이미지에서 추출한 매치 정보를 저장
if 'matches_from_image' not in st.session_state:
    st.session_state.matches_from_image = []

# 1. 이미지 업로드 섹션
with st.expander("📷 [NEW] 경기 일정 스크린샷으로 자동 입력하기", expanded=True):
    uploaded_file = st.file_uploader("경기 목록이 담긴 이미지를 올려주세요", type=["jpg", "png", "jpeg"])
    if uploaded_file is not None:
        if st.button("이미지 분석 및 자동 세팅"):
            if not api_key: st.error("API 키가 필요합니다.")
            else:
                with st.spinner("제미나이가 이미지를 읽고 있습니다..."):
                    img = Image.open(uploaded_file)
                    extracted_data = extract_matches_from_image(img, api_key)
                    if extracted_data:
                        st.session_state.matches_from_image = extracted_data
                        st.success(f"총 {len(extracted_data)}개의 경기를 찾았습니다! 아래 입력창이 자동으로 세팅됩니다.")
                    else:
                        st.warning("경기를 찾지 못했습니다. 이미지를 확인해주세요.")

# 2. 경기 수 및 팀명 세팅
default_count = len(st.session_state.matches_from_image) if st.session_state.matches_from_image else 1
num_matches = st.number_input("분석할 경기 수", min_value=1, max_value=20, value=default_count)

all_matches_data = []

st.divider()

for i in range(num_matches):
    with st.container(border=True):
        # 이미지에서 가져온 정보가 있으면 자동 입력, 없으면 빈칸
        default_a = st.session_state.matches_from_image[i]['team_a'] if i < len(st.session_state.matches_from_image) else ""
        default_b = st.session_state.matches_from_image[i]['team_b'] if i < len(st.session_state.matches_from_image) else ""
        
        st.subheader(f"Match {i+1}")
        c_name1, c_name2 = st.columns(2)
        with c_name1: team_a_name = st.text_input(f"홈팀", value=default_a, key=f"name_a_{i}")
        with c_name2: team_b_name = st.text_input(f"원정팀", value=default_b, key=f"name_b_{i}")

        c_hex1, c_hex2 = st.columns(2)
        with c_hex1: inputs_a = render_hex_input_ui(f"m{i}_a", f"🏠 {team_a_name or '홈팀'} 괘")
        with c_hex2: inputs_b = render_hex_input_ui(f"m{i}_b", f"✈️ {team_b_name or '원정팀'} 괘")
        
        all_matches_data.append({"idx": i+1, "team_a": team_a_name, "inputs_a": inputs_a, "team_b": team_b_name, "inputs_b": inputs_b})

# 3. 분석 및 PDF 저장
if st.button("🚀 GEMS 통합 분석 및 리포트 생성", type="primary"):
    if not api_key:
        st.error("API 키가 필요합니다.")
    else:
        genai.configure(api_key=api_key)
        final_results_for_pdf = [] # PDF용 데이터 저장소
        
        for match in all_matches_data:
            res_a = calculate_hex(match['inputs_a'])
            res_b = calculate_hex(match['inputs_b'])
            t_a = match['team_a'] or "홈팀"
            t_b = match['team_b'] or "원정팀"

            st.markdown(f"### 🏁 Match {match['idx']}: {t_a} vs {t_b}")
            
            with st.spinner(f"{t_a} vs {t_b} 분석 중..."):
                try:
                    tools = [{"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "dynamic", "dynamic_threshold": 0.7}}}]
                    model = genai.GenerativeModel('gemini-1.5-pro', tools=tools)
                    
                    prompt = f"""
                    GEMS 스포츠 분석가로서 '{t_a} vs {t_b}' 경기를 분석하라.
                    주역 데이터: {t_a}({res_a['o_name']}->{res_a['c_name']}), {t_b}({res_b['o_name']}->{res_b['c_name']})
                    
                    [응답 형식 - JSON]
                    {{
                        "win_rate_home": 45,
                        "win_rate_draw": 25,
                        "win_rate_away": 30,
                        "analysis_summary": "여기에 분석 내용을 300자 이내로 요약해서 작성. 현실 데이터와 주역 괘의 흐름을 종합하여 결론 도출."
                    }}
                    JSON 형식만 출력해.
                    """
                    response = model.generate_content(prompt).text
                    
                    # JSON 파싱 (간단 처리)
                    try:
                        import json
                        start = response.find('{')
                        end = response.rfind('}') + 1
                        data = json.loads(response[start:end])
                        wr_h, wr_d, wr_a = data.get('win_rate_home', 33), data.get('win_rate_draw', 33), data.get('win_rate_away', 34)
                        summary = data.get('analysis_summary', '분석 내용 없음')
                    except:
                        wr_h, wr_d, wr_a = 33, 33, 34
                        summary = response # 파싱 실패 시 원문

                    # 화면 표시
                    st.markdown(f"""
                    <div class="win-rate-container">
                        <div class="wr-home" style="width: {wr_h}%">{t_a} {wr_h}%</div>
                        <div class="wr-draw" style="width: {wr_d}%">무 {wr_d}%</div>
                        <div class="wr-away" style="width: {wr_a}%">{t_b} {wr_a}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.info(summary)
                    
                    # 시각화 (괘)
                    c1, c2 = st.columns(2)
                    with c1: 
                        st.caption(f"{t_a}: {res_a['o_name']} ➜ {res_a['c_name']}")
                        st.markdown(res_a['o_visual'], unsafe_allow_html=True)
                    with c2: 
                        st.caption(f"{t_b}: {res_b['o_name']} ➜ {res_b['c_name']}")
                        st.markdown(res_b['o_visual'], unsafe_allow_html=True)

                    # PDF 데이터 저장
                    final_results_for_pdf.append({
                        "idx": match['idx'], "t_a": t_a, "t_b": t_b,
                        "wr_h": wr_h, "wr_d": wr_d, "wr_a": wr_a,
                        "text": summary
                    })
                    
                except Exception as e:
                    st.error(f"Error: {e}")
            st.divider()

        # [PDF 다운로드 버튼]
        if final_results_for_pdf:
            st.success("🎉 모든 분석이 완료되었습니다!")
            pdf_bytes = create_pdf(final_results_for_pdf)
            st.download_button(
                label="📄 결과 리포트 PDF 다운로드",
                data=pdf_bytes,
                file_name="GEMS_Analysis_Report.pdf",
                mime="application/pdf"
            )