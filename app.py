import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import json

# --- 1. 페이지 설정 ---
st.set_page_config(layout="wide", page_title="GEMS: Prompt Builder")

# --- 2. 스타일 CSS ---
st.markdown("""
<style>
    /* 괘 디자인 */
    .yang { background-color: #2c3e50; height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .yin { background: linear-gradient(to right, #2c3e50 42%, transparent 42%, transparent 58%, #2c3e50 58%); height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .hex-box { width: 60px; padding: 5px; border: 1px solid #ddd; background: #fff; margin: 0 auto; }
    
    /* 승률 바 */
    .win-bar-container { display: flex; height: 30px; border-radius: 15px; overflow: hidden; margin: 15px 0; color: white; font-weight: bold; line-height: 30px; text-align: center; font-size: 0.9rem; }
    .wb-home { background-color: #e74c3c; }
    .wb-draw { background-color: #95a5a6; }
    .wb-away { background-color: #3498db; }
    
    /* 프롬프트 박스 */
    .prompt-box { background-color: #f1f8e9; padding: 15px; border: 1px solid #c5e1a5; border-radius: 8px; color: #33691e; font-family: monospace; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 (64괘 매핑) ---
# (간결함을 위해 일부만 예시로 넣었습니다. 실제로는 64개 전체 데이터가 필요합니다.)
# 기존에 가지고 계신 전체 데이터를 여기에 넣으시면 됩니다.
RAW_DATA = """111-111 중천건 111-112 택천쾌 111-121 화천대유 111-122 뇌천대장 111-211 풍천소축 111-212 수천수 111-221 산천대축 111-222 지천태 112-111 천택리 112-112 태위택 112-121 화택규 112-122 뇌택귀매 112-211 풍택중부 112-212 수택절 112-221 산택손 112-222 지택림 121-111 천화동인 121-112 택화혁 121-121 중화리 121-122 뇌화풍 121-211 풍화가인 121-212 수화기제 121-221 산화비 121-222 지화명이 122-111 천뢰무망 122-112 택뢰수 122-121 화뢰서합 122-122 진위뢰 122-211 풍뢰익 122-212 수뢰둔 122-221 산뢰이 122-222 지뢰복 211-111 천풍구 211-112 택풍대과 211-121 화풍정 211-122 뇌풍항 211-211 중풍손 211-212 수풍정 211-221 산풍고 211-222 지풍승 212-111 천수송 212-112 택수곤 212-121 화수미제 212-122 뇌수해 212-211 풍수환 212-212 감위수 212-221 산수몽 212-222 지수사 221-111 천산돈 221-112 택산함 221-121 화산려 221-122 뇌산소과 221-211 풍산점 221-212 수산건 221-221 간위산 221-222 지산겸 222-111 천지비 222-112 택지췌 222-121 화지진 222-122 뇌지예 222-211 풍지관 222-212 수지비 222-221 산지박 222-222 중지곤"""
HEX_DB = {}
tokens = RAW_DATA.split()
for i in range(0, len(tokens), 2): HEX_DB[tokens[i]] = tokens[i+1]
def get_hex_name(key): return HEX_DB.get(key, "미지(Unknown)")

# --- 4. 함수 정의 ---

def get_reality_check(api_key, team_a, team_b):
    """구글 검색으로 현실 데이터 분석"""
    genai.configure(api_key=api_key)
    tools = [{"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "dynamic", "dynamic_threshold": 0.7}}}]
    model = genai.GenerativeModel('gemini-1.5-flash', tools=tools) # Flash로 빠르게 검색
    
    prompt = f"""
    축구 경기 분석: {team_a} vs {team_b}
    1. 최신 배당률 평균 (승/무/패 %)
    2. 양 팀의 최근 5경기 전적 및 분위기
    3. 상대 전적
    
    위 내용을 바탕으로 다음 JSON 형식으로만 답해 (마크다운 없이):
    {{
        "win_rate_home": 45,
        "win_rate_draw": 25,
        "win_rate_away": 30,
        "fact_summary": "여기에 3줄 요약. (예: 토트넘은 홈에서 강세이나 주전 부상. 아스날은 최근 5연승 중...)"
    }}
    """
    try:
        res = model.generate_content(prompt)
        text = res.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)
    except:
        return {"win_rate_home":33, "win_rate_draw":33, "win_rate_away":34, "fact_summary": "데이터 검색 실패. 직접 입력해주세요."}

def draw_hex(lines):
    html = '<div class="hex-box">'
    for val in reversed(lines):
        cls = "yang" if val == '1' else "yin"
        html += f'<div class="{cls}"></div>'
    html += '</div>'
    return html

def calc_hex(inputs):
    origin, changed, m_cnt = [], [], 0
    for x in inputs:
        origin.append(x['val'])
        if x['move']:
            m_cnt += 1
            changed.append('2' if x['val']=='1' else '1')
        else: changed.append(x['val'])
    
    k1 = "".join(origin[:3]) + "-" + "".join(origin[3:])
    k2 = "".join(changed[:3]) + "-" + "".join(changed[3:])
    return {
        "o_code": k1, "o_name": get_hex_name(k1), "o_html": draw_hex(origin),
        "c_code": k2, "c_name": get_hex_name(k2), "c_html": draw_hex(changed),
        "moving": m_cnt
    }

def render_hex_input(label, key):
    st.markdown(f"**{label}**")
    data = []
    # 6효 -> 1효 순서
    for i in range(6, 0, -1):
        c1, c2, c3 = st.columns([1, 3, 2])
        with c1: st.caption(f"{i}효")
        with c2: val = st.radio(f"v_{key}_{i}", ["양(1)", "음(2)"], horizontal=True, label_visibility="collapsed")
        with c3: move = st.checkbox("변효", key=f"m_{key}_{i}")
        data.append({'val': '1' if "양" in val else '2', 'move': move})
    # 데이터는 1효 -> 6효 순서로 뒤집어서 리턴
    return data[::-1]

# --- 5. 메인 앱 ---

with st.sidebar:
    st.header("⚙️ 설정")
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]
    else:
        api_key = st.text_input("Gemini API Key", type="password")

st.title("🏗️ GEMS: 프롬프트 빌더")
st.caption("현실 데이터 분석 + 주역 작괘 -> GEMS 전용 프롬프트 생성")

if 'reality_data' not in st.session_state:
    st.session_state.reality_data = None

# [1] 경기 정보 및 현실 분석
with st.container(border=True):
    st.subheader("1. 경기 정보 & 현실 데이터 분석")
    c1, c2 = st.columns(2)
    team_a = c1.text_input("홈팀", "토트넘")
    team_b = c2.text_input("원정팀", "아스날")
    
    if st.button("🔍 현실 데이터(배당/전적) 검색"):
        if not api_key: st.error("API 키 필요")
        else:
            with st.spinner("구글 검색 중..."):
                st.session_state.reality_data = get_reality_check(api_key, team_a, team_b)

    # 검색 결과 시각화
    if st.session_state.reality_data:
        d = st.session_state.reality_data
        st.markdown(f"""
        <div class="win-bar-container">
            <div class="wb-home" style="width:{d['win_rate_home']}%">{team_a} {d['win_rate_home']}%</div>
            <div class="wb-draw" style="width:{d['win_rate_draw']}%">무 {d['win_rate_draw']}%</div>
            <div class="wb-away" style="width:{d['win_rate_away']}%">{team_b} {d['win_rate_away']}%</div>
        </div>
        """, unsafe_allow_html=True)
        st.info(f"📊 **현실 팩트 요약:** {d['fact_summary']}")

# [2] 주역 작괘
with st.container(border=True):
    st.subheader("2. 주역 괘 입력")
    c3, c4 = st.columns(2)
    with c3:
        input_a = render_hex_input(f"🏠 {team_a} 괘", "A")
        res_a = calc_hex(input_a)
        # 시각화
        v1, v2, v3 = st.columns([1, 0.5, 1])
        with v1: st.markdown(res_a['o_html'], unsafe_allow_html=True); st.caption(res_a['o_name'])
        with v2: st.markdown("<div style='text-align:center; margin-top:20px'>➜</div>", unsafe_allow_html=True)
        with v3: st.markdown(res_a['c_html'], unsafe_allow_html=True); st.caption(res_a['c_name'])
        
    with c4:
        input_b = render_hex_input(f"✈️ {team_b} 괘", "B")
        res_b = calc_hex(input_b)
        # 시각화
        v4, v5, v6 = st.columns([1, 0.5, 1])
        with v4: st.markdown(res_b['o_html'], unsafe_allow_html=True); st.caption(res_b['o_name'])
        with v5: st.markdown("<div style='text-align:center; margin-top:20px'>➜</div>", unsafe_allow_html=True)
        with v6: st.markdown(res_b['c_html'], unsafe_allow_html=True); st.caption(res_b['c_name'])

# [3] 프롬프트 생성
st.divider()
st.subheader("3. GEMS 전용 프롬프트 생성")

if st.button("✨ 프롬프트 완성하기", type="primary"):
    # 현실 데이터가 없으면 기본값 처리
    fact_txt = st.session_state.reality_data['fact_summary'] if st.session_state.reality_data else "현실 데이터 검색을 수행하지 않았습니다."
    odds_txt = f"홈승 {st.session_state.reality_data['win_rate_home']}%, 무승부 {st.session_state.reality_data['win_rate_draw']}%, 원정승 {st.session_state.reality_data['win_rate_away']}%" if st.session_state.reality_data else "배당률 정보 없음"

    final_prompt = f"""
[GEMS 분석 요청]

1. 매치업: {team_a} vs {team_b}

2. 현실 데이터 (기준점):
- {fact_txt}
- 예상 승률: {odds_txt}

3. 주역 괘 데이터:
- {team_a} (홈): {res_a['o_name']}({res_a['o_code']}) -> {res_a['c_name']}({res_a['c_code']}) / 변효 {res_a['moving']}개
- {team_b} (원정): {res_b['o_name']}({res_b['o_code']}) -> {res_b['c_name']}({res_b['c_code']}) / 변효 {res_b['moving']}개

4. 요청 사항:
위 [현실 데이터]를 기준으로 삼고, [주역 괘]의 흐름(체용, 오행, 효사)을 대입하여 최종 승패를 예측하고 시나리오를 설명하시오.
"""
    st.success("아래 텍스트를 복사해서 GEMS(제미나이 챗봇)에 붙여넣으세요!")
    st.code(final_prompt, language='text')