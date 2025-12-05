import streamlit as st

# --- 1. 페이지 설정 ---
st.set_page_config(layout="wide", page_title="GEMS: Prompt Builder (Lite)")

# --- 2. 스타일 CSS ---
st.markdown("""
<style>
    /* 괘 막대 스타일 */
    .yang { background-color: #2c3e50; height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .yin { background: linear-gradient(to right, #2c3e50 42%, transparent 42%, transparent 58%, #2c3e50 58%); height: 10px; width: 100%; margin-bottom: 4px; border-radius: 2px; }
    .hex-box { width: 70px; padding: 10px; border: 1px solid #ddd; background: #fff; margin: 0 auto; display: flex; flex-direction: column; justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    
    /* 버튼 및 링크 스타일 */
    .naver-btn {
        display: inline-block; width: 100%; padding: 12px; 
        background-color: #03C75A; color: white !important; 
        text-align: center; text-decoration: none; font-weight: bold; 
        border-radius: 8px; margin-bottom: 10px; transition: 0.3s;
    }
    .naver-btn:hover { background-color: #02b351; }
    
    .guide-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #6c757d; margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 데이터 (64괘 매핑) ---
RAW_DATA = """111-111 중천건 111-112 택천쾌 111-121 화천대유 111-122 뇌천대장 111-211 풍천소축 111-212 수천수 111-221 산천대축 111-222 지천태 112-111 천택리 112-112 태위택 112-121 화택규 112-122 뇌택귀매 112-211 풍택중부 112-212 수택절 112-221 산택손 112-222 지택림 121-111 천화동인 121-112 택화혁 121-121 중화리 121-122 뇌화풍 121-211 풍화가인 121-212 수화기제 121-221 산화비 121-222 지화명이 122-111 천뢰무망 122-112 택뢰수 122-121 화뢰서합 122-122 진위뢰 122-211 풍뢰익 122-212 수뢰둔 122-221 산뢰이 122-222 지뢰복 211-111 천풍구 211-112 택풍대과 211-121 화풍정 211-122 뇌풍항 211-211 중풍손 211-212 수풍정 211-221 산풍고 211-222 지풍승 212-111 천수송 212-112 택수곤 212-121 화수미제 212-122 뇌수해 212-211 풍수환 212-212 감위수 212-221 산수몽 212-222 지수사 221-111 천산돈 221-112 택산함 221-121 화산려 221-122 뇌산소과 221-211 풍산점 221-212 수산건 221-221 간위산 221-222 지산겸 222-111 천지비 222-112 택지췌 222-121 화지진 222-122 뇌지예 222-211 풍지관 222-212 수지비 222-221 산지박 222-222 중지곤"""
HEX_DB = {}
tokens = RAW_DATA.split()
for i in range(0, len(tokens), 2): HEX_DB[tokens[i]] = tokens[i+1]
def get_hex_name(key): return HEX_DB.get(key, "미지")

# --- 4. 함수 정의 ---

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
    
    moving_display = ",".join(m_lines) + "효" if m_lines else "변효 없음"
    moving_raw = ",".join(m_lines) if m_lines else "0"
    
    return {
        "o_name": get_hex_name(k1), "c_name": get_hex_name(k2), 
        "o_visual": draw_lines_html(origin), "c_visual": draw_lines_html(changed), 
        "moving_display": moving_display, "moving_raw": moving_raw
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

# 상단: 리셋 버튼
c_top1, c_top2 = st.columns([3, 1])
with c_top1:
    st.title("💎 GEMS: Prompt Builder")
with c_top2:
    if st.button("🔄 새로운 경기 (Reset)", type="primary"):
        st.rerun()

st.markdown("""
<div class="guide-box">
    <b>💡 사용 프로세스:</b><br>
    1. <b>[네이버 스포츠]</b>에서 경기 일정/팀을 확인한다.<br>
    2. 아래에 팀 이름과 주역 괘를 입력한다.<br>
    3. 생성된 <b>프롬프트</b>를 복사해 GEMS(제미나이)에게 보낸다.
</div>
""", unsafe_allow_html=True)

# [네이버 바로가기 버튼]
st.markdown("""
<a href="https://m.sports.naver.com/wfootball/schedule/index" target="_blank" class="naver-btn">
    📅 네이버 해외축구 일정 확인하기 (클릭)
</a>
""", unsafe_allow_html=True)

st.divider()

# [입