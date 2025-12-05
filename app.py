import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
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
RAW_DATA = """111-111 중천건 111-112 택천쾌 111-121 화천대유 111-122 뇌천대장 111-211 풍천소축 111-212 수천수 111-221 산천대축 111-222 지천태 112-111 천택리 112-112 태위택 112-121 화택규 112-122 뇌택귀매 112-211 풍택중부 112-212 수택절 112-221 산택손 112-222 지택림 121-111 천화동인 121-112 택화혁 121-121 중화리 121-122 뇌화풍 121-211 풍화가인 121-212 수화기제 121-221 산화비 121-222 지화명이 122-111 천뢰무망 122-112 택뢰수 122-121 화뢰서합 122-122 진위뢰 122-211 풍뢰익 122-212 수뢰둔 122-221 산뢰이 122-222 지뢰복 211-111 천풍구 211-112 택풍대과 211-121 화풍정 211-122 뇌풍항 211-211 중풍손 211-212 수풍정 211-221 산풍고 211-222 지풍승 212-111 천수송 212-112 택수곤 212-121 화수미제 212-122 뇌수해 212-211 풍수환 212-212 감위수 212-221 산수몽 212-222 지수사 221-111 천산돈 221-112 택산함 221-121 화산려 221-122 뇌산소과 221-211 풍산점 221-212 수산건 221-221 간위산 221-222 지산겸 222-111 천지비 222-112 택지췌 222-121 화지진 222-122 뇌지예 222-211 풍지관 222-212 수지비 222-221 산지박 222-222 중지곤"""
HEX_DB = {}
tokens = RAW_DATA.split()
for i in range(0, len(tokens), 2): HEX_DB[tokens[i]] = tokens[i+1]
def get_hex_name(key): return HEX_DB.get(key, "미지")

# --- 4. 함수 정의 ---

def get_reality_check(api_key, team_a, team_b):
    genai.configure(api_key=api_key)
    tools = [{"google_search_retrieval": {"dynamic_retrieval_config": {"mode": "dynamic", "dynamic_threshold": 0.7}}}]
    # [수정] 모델명을 'gemini-1.5-flash'로 통일 (에러 해결 핵심)
    model = genai.GenerativeModel('gemini-1.5-flash', tools=tools)
    
    today_str = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"""
    기준 날짜: {today_str}. 축구 경기 '{team_a} vs {team_b}'
    기준 날짜 이후 가장 가까운 예정 경기의 일정(한국시간), 승부예측 배당률, 양팀 분위기를 조사해.
    JSON 응답: {{"match_time": "...", "win_rate_home": 45, "win_rate_draw": 25, "win_rate_away": 30, "fact_summary": "..."}}
    """
    try:
        res = model.generate_content(prompt)
        return json.loads(res.text.strip().replace("```json", "").replace("```", ""))
    except: return {"match_time": "미확인", "win_rate_home":33,"win_rate_draw":33,"win_rate_away":34,"fact_summary":"검색실패"}

def extract_matches_from_image(image, api_key):
    genai.configure(api_key=api_key)
    # [수정] 이미지 인식도 'gemini-1.5-flash' 사용
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    
    prompt = """
    이미지에서 '홈팀 vs 원정팀' 또는 표 안의 '홈팀', '원정팀' 텍스트를 추출해.
    숫자(배당률, 날짜)는 무시해.
    JSON 포맷: [{"home": "팀A", "away": "팀B"}, ...]
    """
    try:
        res = model.generate_content([prompt, image], safety_settings=safety_settings)
        text = res.text
        start = text.find('[')
        end = text.rfind(']') + 1
        return json.loads(text[start:end])
    except: return []

def draw_lines_html(lines_list):
    html = '<div class="hex-box">'
    for val in reversed(lines_list):
        cls = "yang" if val == '1' else "yin"
        html += f'<div class="{cls}"></div>'
    html += '</div>'
    return html

def calculate_hex(user_inputs):
    origin, changed, m_lines = [], [], []
    for i, item in enumerate(user_inputs):
        val, is_moving = item['val'], item['is_moving']
        origin.append(val)
        if is_moving:
            m_lines.append(str(i+1))
            changed.append('2' if val == '1' else '1')
        else: changed.append(val)
    k1 = "".join(origin[:3]) + "-" + "".join(origin[3:])
    k2 = "".join(changed[:3]) + "-" + "".join(changed[3:])
    
    moving_str = ",".join(m_lines) if m_lines else "0"
    
    return {
        "o_name": get_hex_name(k1), "c_name": get_hex_name(k2), 
        "o_code": k1, "c_code": k2, 
        "o_visual": draw_lines_html(origin), "c_visual": draw_lines_html(changed), 
        "moving_pos": moving_str
    }

def render_hex_input_ui(key_prefix, label):
    st.markdown(f"**{label}**")
    inputs = [] 
    temp_inputs = {} 
    for i in range(6, 0, -1):
        c1, c2, c3 = st.columns([0.8, 2.5, 1.5])
        with c1: st.caption(f"{i}효")
        with c2: val = st.radio(f"효{i}", ["양(1)", "음(2)"], horizontal=True, key=f"r_{key_prefix}_{i}", label_visibility="collapsed")
        with c3: move = st.checkbox("변효", key=f"c_{key_prefix}_{i}")
        temp_inputs[i] = {'val': '1' if "양" in val else '2', 'is_moving': move}
    for i in range(1, 7): inputs.append(temp_inputs[i])
    return inputs

# --- 5. 메인 앱 ---

st.title("🧙‍♂️ GEMS: 마스터 프롬프트 생성기")
st.markdown("""
<div class="guide-text">
    <b>💡 데이터 관리 팁:</b><br>
    GEMS 분석 결과 맨 마지막 줄에 생성되는 <b>[데이터 코드]</b>를 복사하여 엑셀에 저장하세요.<br>
    변효 정보까지 상세하게 기록되어 나중에 정밀 복기가 가능합니다.
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ 설정")
    if "GEMINI_API_KEY" in st.secrets: api_key = st.secrets["GEMINI_API_KEY"]
    else: api_key = st.text_input("Gemini API Key", type="password")

if 'reality_data' not in st.session_state: st.session_state.reality_data = None
if 'matches_list' not in st.session_state: st.session_state.matches_list = []

# [입력 모드 선택]
input_mode = st.radio("입력 방식", ["✍️ 수기 입력", "📷 이미지 자동 인식"], horizontal=True)

if input_mode == "📷 이미지 자동 인식":
    with st.container(border=True):
        uploaded_file = st.file_uploader("일정표 이미지 업로드", type=["jpg", "png", "jpeg"])
        if uploaded_file and st.button("이미지 분석"):
            if not api_key: st.error("API 키 필요")
            else:
                with st.spinner("이미지 분석 중..."):
                    img = Image.open(uploaded_file)
                    data = extract_matches_from_image(img, api_key)
                    if data:
                        st.session_state.matches_list = data
                        st.success(f"{len(data)}경기 인식 성공!")
                    else:
                        st.error("인식 실패. 이미지를 확인해주세요.")
    default_cnt = len(st.session_state.matches_list) if st.session_state.matches_list else 1
else:
    default_cnt = 1

# 경기 수 및 입력창
num_matches = st.number_input("분석할 경기 수", 1, 20, default_cnt)
all_inputs = []

st.divider()

for i in range(num_matches):
    with st.container(border=True):
        # 자동 인식된 데이터가 있으면 채워넣기
        default_home = st.session_state.matches_list[i]['home'] if i < len(st.session_state.matches_list) else ""
        default_away = st.session_state.matches_list[i]['away'] if i < len(st.session_state.matches_list) else ""
        
        st.subheader(f"Match {i+1}")
        c1, c2 = st.columns(2)
        team_a = c1.text_input("홈팀", value=default_home, key=f"t_h_{i}")
        team_b = c2.text_input("원정팀", value=default_away, key=f"t_a_{i}")
        
        # 현실 데이터 검색 버튼 (개별)
        d = {"match_time": "미확인", "win_rate_home":0, "win_rate_draw":0, "win_rate_away":0, "fact_summary": "없음"}
        if st.button(f"🔍 현실 데이터 검색 (Match {i+1})", key=f"btn_{i}"):
             if not api_key: st.error("API 키 필요")
             else:
                 with st.spinner("검색 중..."):
                     d = get_reality_check(api_key, team_a, team_b)
                     st.session_state[f"reality_{i}"] = d
        
        # 저장된 데이터 불러오기
        if f"reality_{i}" in st.session_state:
            d = st.session_state[f"reality_{i}"]
            st.info(f"📅 일정: {d['match_time']} | 팩트: {d['fact_summary']}")

        c3, c4 = st.columns(2)
        with c3: inp_a = render_hex_input_ui(f"hex_h_{i}", f"🏠 {team_a or '홈'} 괘"); res_a = calculate_hex(inp_a)
        with c4: inp_b = render_hex_input_ui(f"hex_a_{i}", f"✈️ {team_b or '원정'} 괘"); res_b = calculate_hex(inp_b)
            
        all_inputs.append({"idx": i+1, "ta": team_a, "tb": team_b, "res_a": res_a, "res_b": res_b, "reality": d})

st.divider()

# [프롬프트 생성]
if st.button("🚀 전체 프롬프트 생성하기", type="primary", use_container_width=True):
    for m in all_inputs:
        d = m['reality']
        team_a, team_b = m['ta'], m['tb']
        res_a, res_b = m['res_a'], m['res_b']
        
        final_prompt = f"""
[GEMS 통합 분석 요청]

1. 경기: {team_a} vs {team_b} ({d['match_time']})
2. 현실 데이터: 홈승 {d['win_rate_home']}%, 무 {d['win_rate_draw']}%, 원정승 {d['win_rate_away']}%, 이슈: {d['fact_summary']}
3. 주역 데이터:
   - {team_a}: {res_a['o_name']} -> {res_a['c_name']} (변효: {res_a['moving_pos']})
   - {team_b}: {res_b['o_name']} -> {res_b['c_name']} (변효: {res_b['moving_pos']})

[분석 지침]
현실 데이터와 주역 괘의 흐름을 통합하여 승패를 예측하고 시나리오를 설명하시오.

[★★★ 매우 중요: 마지막 출력 양식 ★★★]
분석이 끝나면, 맨 마지막 줄에 반드시 아래 형식의 '데이터 코드' 한 줄만 출력하시오. (설명 없이 코드만)
이 코드는 엑셀에 저장하여 당신을 학습시키는 데 사용됩니다.

`DATA|{d['match_time']}|{team_a}|{team_b}|{res_a['o_name']}->{res_a['c_name']}|{res_a['moving_pos']}|{res_b['o_name']}->{res_b['c_name']}|{res_b['moving_pos']}|[GEMS의_최종예측결과]|[예측확률%]`
"""
        st.markdown(f"### 📝 Match {m['idx']} 프롬프트")
        st.code(final_prompt, language='text')