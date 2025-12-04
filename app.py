import streamlit as st
import google.generativeai as genai

# 페이지 설정
st.set_page_config(layout="wide", page_title="GEMS: 승부예측")

# --- 비밀번호(API Key) 처리 ---
# 1순위: 서버의 비밀 금고(Secrets)에서 찾는다.
# 2순위: 없으면 화면 왼쪽 사이드바에서 입력받는다.
try:
    api_key = st.secrets["GEMINI_API_KEY"]
except:
    with st.sidebar:
        api_key = st.text_input("Gemini API 키를 입력하세요", type="password")

# --- GEMS 분석 함수 ---
def run_gems_analysis(team_a, team_b, hex_a, hex_b, key):
    genai.configure(api_key=key)
    # 검색 도구 설정
    tools = [{"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "dynamic", "dynamic_threshold": 0.7}}}]
    model = genai.GenerativeModel('gemini-1.5-pro-002', tools=tools)
    
    prompt = f"""
    당신은 '주역 데이터 분석가 GEMS'입니다. 
    1. 현실 데이터 검색: 구글 검색을 통해 '{team_a} vs {team_b}'의 최신 배당률, 전적, 예상 라인업을 찾으세요.
    2. 주역 분석: A팀 괘({hex_a}), B팀 괘({hex_b})를 바탕으로 주역의 흐름을 분석하세요.
    3. 종합 결론: 현실 데이터와 주역 괘를 합쳐 승부를 예측하고 확률을 제시하세요.
    """
    return model.generate_content(prompt).text

# --- 화면 구성 ---
st.title("💎 GEMS: AI Sports Oracle")
st.info("현실 데이터(구글 검색) + 주역 점사(GEMS) 통합 분석기")

c1, c2 = st.columns(2)
with c1:
    team_a = st.text_input("홈 팀 (Team A)", "토트넘")
    hex_a = st.text_input("홈 팀 괘 (예: 111-111)", "건위천")
with c2:
    team_b = st.text_input("원정 팀 (Team B)", "아스날")
    hex_b = st.text_input("원정 팀 괘 (예: 222-222)", "곤위지")

if st.button("🚀 분석 시작", type="primary", use_container_width=True):
    if not api_key:
        st.error("API 키가 없습니다. 설정(Secrets)을 확인하거나 사이드바에 입력하세요.")
    else:
        with st.spinner("제미나이가 구글 검색 및 주역 분석 중입니다..."):
            try:
                result = run_gems_analysis(team_a, team_b, hex_a, hex_b, api_key)
                st.markdown(result)
            except Exception as e:
                st.error(f"오류 발생: {e}")