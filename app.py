import streamlit as st

# --- 1. 페이지 설정 ---
st.set_page_config(layout="wide", page_title="GEMS: Master Prompt Builder")

# --- 2. 스타일 CSS ---
st.markdown("""
<style>
    /* 괘 막대 스타일 */
    .yang { background-color: #2c3e50; height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .yin { background: linear-gradient(to right, #2c3e50 42%, transparent 42%, transparent 58%, #2c3e50 58%); height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .hex-box { width: 70px; padding: 10px; border: 1px solid #ddd; background: #fff; margin: 0 auto; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    
    /* 프롬프트 출력 박스 */
    .prompt-area { background-color: #f1f8e9; border: 2px solid #aed581; padding: 20px; border-radius: 10px; color: #33691e; font-family: 'Courier New', monospace; white-space: pre-wrap; margin-top: 20px; }
    
    .guide-text { background-color: #e3f2fd; padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 5px solid #2196f3; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 (64괘 매핑 - 전체 데이터) ---
RAW_DATA = """111-111 중천건 111-112 택천쾌 111-121 화천대유 111-122 뇌천대장 111-211 풍천소축 111-212 수천수 111-221 산천대축 111-222 지천태 112-111 천택리 112-112 태위택 112-121 화택규 112-122 뇌택귀매 112-211 풍택중부 112-212 수택절 112-221 산택손 112-222 지택림 121-111 천화동인 121-112 택화혁 121-121 중화리 121-122 뇌화풍 121-211 풍화가인 121-212 수화기제 121-221 산화비 121-222 지화명이 122-111 천뢰무망 122-112 택뢰수 122-121 화뢰서합 122-122 진위뢰 122-211 풍뢰익 122-212 수뢰둔 122-221 산뢰이 122-222 지뢰복 211-111 천풍구 211-112 택풍대과 211-121 화풍정 211-122 뇌풍항 211-211 중풍손 211-212 수풍정 211-221 산풍고 211-222 지풍승 212-111 천수송 212-112 택수곤 212-121 화수미제 212-122 뇌수해 212-211 풍수환 212-212 감위수 212-221 산수몽 212-222 지수사 221-111 천산돈 221-112 택산함 221-121 화산려 221-122 뇌산소과 221-211 풍산점 221-212 수산건 221-221 간위산 221-222 지산겸 222-111 천지비 222-112 택지췌 222-121 화지진 222-122 뇌지예 222-211 풍지관 222-212 수지비 222-221 산지박 222-222 중지곤"""
HEX_DB = {}
tokens = RAW_DATA.split()
for i in range(0, len(tokens), 2): HEX_DB[tokens[i]] = tokens[i+1]
def get_hex_name(key): return HEX_DB.get(key, "미지(Unknown)")

# --- 4. 함수 정의 ---

def draw_lines_html(lines_list):
    """0/1 리스트를 HTML 막대로 변환"""
    html = '<div class="hex-box">'
    for val in reversed(lines_list): # 6효가 위로 가도록 역순
        cls = "yang" if val == '1' else "yin"
        html += f'<div class="{cls}"></div>'
    html += '</div>'
    return html

def calculate_hex(user_inputs):
    """사용자 입력을 괘 이름과 코드로 변환"""
    origin = []
    changed = []
    moving_lines = [] # 변효 위치 (1~6)
    
    # user_inputs: index 0(1효) ~ index 5(6효)
    for i, item in enumerate(user_inputs):
        val = item['val']
        is_moving = item['is_moving']
        
        origin.append(val)
        if is_moving:
            moving_lines.append(str(i+1)) # 1-based index
            changed.append('2' if val == '1' else '1')
        else:
            changed.append(val)
            
    def make_key(ls): return "".join(ls[0:3]) + "-" + "".join(ls[3:6])
    
    o_key = make_key(origin)
    c_key = make_key(changed)
    
    return {
        "o_name": get_hex_name(o_key), 
        "c_name": get_hex_name(c_key), 
        "o_code": o_key,
        "c_code": c_key,
        "o_visual": draw_lines_html(origin), 
        "c_visual": draw_lines_html(changed), 
        "moving_cnt": len(moving_lines),
        "moving_pos": ", ".join(moving_lines) if moving_lines else "없음"
    }

def render_hex_input_ui(key_prefix, label):
    """6효 입력 UI"""
    st.markdown(f"**{label}**")
    inputs = [] 
    temp_inputs = {} 
    
    # 화면 표시는 6효(상) -> 1효(초) 순서
    for i in range(6, 0, -1):
        c1, c2, c3 = st.columns([0.8, 2.5, 1.5])
        with c1: st.caption(f"{i}효")
        with c2: val = st.radio(f"효{i}", ["양(1)", "음(2)"], horizontal=True, key=f"r_{key_prefix}_{i}", label_visibility="collapsed")
        with c3: move = st.checkbox("변효", key=f"c_{key_prefix}_{i}")
        temp_inputs[i] = {'val': '1' if "양" in val else '2', 'is_moving': move}
        
    # 데이터는 1효 -> 6효 순서로 리스트 저장
    for i in range(1, 7): inputs.append(temp_inputs[i])
    return inputs

# --- 5. 메인 앱 ---

st.title("🧙‍♂️ GEMS: 마스터 프롬프트 생성기")
st.markdown("""
<div class="guide-text">
    <b>💡 사용법:</b><br>
    1. 분석할 <b>경기 정보(팀 이름)</b>를 입력하세요.<br>
    2. 동전을 던져 나온 <b>주역 괘(6효)</b>를 입력하세요.<br>
    3. 생성된 <b>[프롬프트]</b>를 복사해서 <b>GEMS(제미나이)</b>에게 붙여넣으세요.
</div>
""", unsafe_allow_html=True)

# [입력 섹션]
c_home, c_away = st.columns(2)

with c_home:
    st.subheader("🅰️ 홈 팀 (Home)")
    team_a = st.text_input("홈 팀 이름", "토트넘")
    inp_a = render_hex_input_ui("home", "홈 팀 괘 입력")
    res_a = calculate_hex(inp_a) # 실시간 계산
    
    # 괘 확인용 시각화
    st.markdown("---")
    v1, v2, v3 = st.columns([1, 0.2, 1])
    with v1: 
        st.caption(f"본괘: {res_a['o_name']}")
        st.markdown(res_a['o_visual'], unsafe_allow_html=True)
    with v2: st.markdown("<br><br>➜", unsafe_allow_html=True)
    with v3: 
        st.caption(f"지괘: {res_a['c_name']}")
        st.markdown(res_a['c_visual'], unsafe_allow_html=True)

with c_away:
    st.subheader("🅱️ 원정 팀 (Away)")
    team_b = st.text_input("원정 팀 이름", "아스날")
    inp_b = render_hex_input_ui("away", "원정 팀 괘 입력")
    res_b = calculate_hex(inp_b) # 실시간 계산
    
    # 괘 확인용 시각화
    st.markdown("---")
    v4, v5, v6 = st.columns([1, 0.2, 1])
    with v4: 
        st.caption(f"본괘: {res_b['o_name']}")
        st.markdown(res_b['o_visual'], unsafe_allow_html=True)
    with v5: st.markdown("<br><br>➜", unsafe_allow_html=True)
    with v6: 
        st.caption(f"지괘: {res_b['c_name']}")
        st.markdown(res_b['c_visual'], unsafe_allow_html=True)

st.divider()

# [프롬프트 생성 섹션]
st.subheader("📝 GEMS에게 보낼 프롬프트 (자동 생성)")

if st.button("🚀 프롬프트 생성하기", type="primary", use_container_width=True):
    
    # GEMS에게 보낼 강력한 프롬프트 내용
    final_prompt = f"""
[GEMS 통합 분석 요청]

당신은 스포츠 데이터 분석가이자 주역(I Ching) 전문가입니다.
다음 경기에 대해 '현실 데이터'와 '주역 점사'를 통합하여 승부를 예측해 주세요.

1. 대상 경기: {team_a} vs {team_b}

2. [1단계: 현실 데이터 검색 및 시각화]
- 구글 검색을 통해 양 팀의 최신 배당률, 상대 전적, 최근 5경기 기세를 조사하세요.
- 조사한 승률 데이터를 반드시 아래와 같은 ASCII 차트 형태로 시각화해서 보여주세요.
  (예시: [ {team_a} ■■■■■□□□ 무승부 □□ {team_b} ■■■ ])
- 각 팀의 핵심 이슈(부상, 결장, 분위기)를 3줄로 요약하세요.

3. [2단계: 주역 괘 분석]
내가 뽑은 점사 결과는 다음과 같습니다. 이 흐름을 해석해 주세요.
- {team_a} (홈): [{res_a['o_name']}]에서 [{res_a['c_name']}]으로 변화 (변효: {res_a['moving_pos']}효)
- {team_b} (원정): [{res_b['o_name']}]에서 [{res_b['c_name']}]으로 변화 (변효: {res_b['moving_pos']}효)

* 해석 지침:
- 본괘(현재)와 지괘(결과)의 의미를 살피고, 변효가 가리키는 상황을 구체적으로 대입하세요.
- 오행의 상생/상극 관계를 따져 어느 팀의 기운이 더 강한지 판단하세요.

4. [3단계: 최종 결론]
- 현실 데이터(정배/역배)와 주역의 기운이 일치하는지 충돌하는지 비교하세요.
- 최종적으로 어느 팀의 승리 확률이 높은지 퍼센트(%)로 제시하고 결론을 내리세요.
"""
    
    # 화면에 출력
    st.success("프롬프트가 생성되었습니다! 아래 박스의 내용을 복사(Ctrl+C)하세요.")
    st.code(final_prompt, language='text')
    
    st.markdown("""
    > **Tip:** 오른쪽 위의 📄 아이콘을 누르면 한 번에 복사됩니다.
    > 이제 GEMS(제미나이) 채팅창에 붙여넣기만 하면 분석 끝!
    """)