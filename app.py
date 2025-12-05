import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from PIL import Image
import json

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="GEMS Lite", layout="wide")

# --- 2. CSS 디자인 (심플 & 모던) ---
st.markdown("""
<style>
    .report-box { background-color: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #e9ecef; margin-bottom: 20px; }
    .highlight { color: #d63384; font-weight: bold; }
    .win-bar { display: flex; height: 25px; border-radius: 12px; overflow: hidden; margin: 10px 0; color: white; font-size: 0.8rem; line-height: 25px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 3. 함수 정의 ---
def get_model(api_key):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-1.5-flash')

def analyze_match(api_key, home, away, h_hex, a_hex):
    model = get_model(api_key)
    prompt = f"""
    스포츠 경기 분석: {home} vs {away}
    주역 괘: {home}({h_hex}), {away}({a_hex})
    
    위 정보를 바탕으로 다음 JSON 형식으로만 답해 (마크다운 없이):
    {{
        "win_h": 40, "win_d": 30, "win_a": 30,
        "summary": "핵심 분석 내용 (3줄 요약)"
    }}
    """
    try:
        res = model.generate_content(prompt)
        return json.loads(res.text.replace("```json", "").replace("```", ""))
    except:
        return {"win_h":33, "win_d":33, "win_a":34, "summary": "분석 실패 (다시 시도해주세요)"}

def analyze_image(api_key, image):
    model = get_model(api_key)
    prompt = """
    이미지 속 경기 일정(팀 이름)을 추출해. 숫자 무시.
    JSON 형식: [{"home": "팀A", "away": "팀B"}, ...]
    """
    try:
        res = model.generate_content([prompt, image])
        return json.loads(res.text.replace("```json", "").replace("```", ""))
    except:
        return []

# --- 4. 메인 화면 ---
st.title("💎 GEMS Lite")
st.caption("가볍고 빠른 AI 승부예측")

with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Gemini API Key", type="password")
    
    st.divider()
    st.markdown("### 사용법")
    st.markdown("1. 키 입력\n2. 이미지 업로드 또는 수기 입력\n3. 분석 시작")

if 'matches' not in st.session_state:
    st.session_state.matches = []

# 입력 탭
tab1, tab2 = st.tabs(["📷 이미지로 자동 입력", "✍️ 직접 입력"])

with tab1:
    img_file = st.file_uploader("경기 일정표 이미지 업로드", type=['png', 'jpg'])
    if img_file and st.button("이미지 인식"):
        if not api_key: st.error("API 키 필요")
        else:
            with st.spinner("스캔 중..."):
                data = analyze_image(api_key, Image.open(img_file))
                if data:
                    st.session_state.matches = data
                    st.success(f"{len(data)}경기 인식 성공!")
                    st.rerun()

with tab2:
    if st.button("입력창 추가"):
        st.session_state.matches.append({"home": "", "away": ""})

# 리스트 출력 및 분석
if st.session_state.matches:
    st.divider()
    st.subheader(f"총 {len(st.session_state.matches)}개의 경기 분석")
    
    # 폼 데이터 수집을 위한 컨테이너
    inputs = []
    for i, m in enumerate(st.session_state.matches):
        with st.expander(f"Match {i+1}: {m.get('home','홈')} vs {m.get('away','원정')}", expanded=True):
            c1, c2 = st.columns(2)
            h = c1.text_input("홈팀", m.get('home',''), key=f"h{i}")
            a = c2.text_input("원정팀", m.get('away',''), key=f"a{i}")
            
            c3, c4 = st.columns(2)
            h_hex = c3.text_input("홈팀 괘 (예: 건위천)", key=f"hh{i}")
            a_hex = c4.text_input("원정팀 괘 (예: 곤위지)", key=f"ah{i}")
            
            inputs.append({"home": h, "away": a, "h_hex": h_hex, "a_hex": a_hex})

    if st.button("🚀 전체 분석 시작", type="primary"):
        if not api_key: st.error("API 키가 없습니다.")
        else:
            for idx, item in enumerate(inputs):
                if item['home'] and item['away']:
                    st.markdown(f"---")
                    st.markdown(f"### 🏁 Match {idx+1}: {item['home']} vs {item['away']}")
                    
                    with st.spinner("AI 분석 중..."):
                        res = analyze_match(api_key, item['home'], item['away'], item['h_hex'], item['a_hex'])
                        
                        # 결과 표시
                        st.markdown(f"""
                        <div class="win-bar">
                            <div style="width:{res['win_h']}%; background:#ff4b4b;">{item['home']} {res['win_h']}%</div>
                            <div style="width:{res['win_d']}%; background:#888;">무 {res['win_d']}%</div>
                            <div style="width:{res['win_a']}%; background:#4b4bff;">{item['away']} {res['win_a']}%</div>
                        </div>
                        <div class="report-box">
                            <b>📊 AI 분석 요약:</b><br>{res['summary']}
                        </div>
                        """, unsafe_allow_html=True)
            
            st.success("모든 분석이 완료되었습니다. (결과를 저장하려면 브라우저 인쇄 기능을 사용하세요)")