"""
Water Co-Scientist — K-water AI연구소 가상 에이전트 시연 앱
Streamlit + OpenAI o4-mini API
"""

import streamlit as st
import openai
import base64
import io
import time
from datetime import datetime

# PDF 텍스트 추출용
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# ──────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Water Co-Scientist | K-water AI연구소",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=DM+Mono:wght@400;500&display=swap');

/* ── 전체 배경 ── */
html, body, [data-testid="stAppViewContainer"] {
    background: #f0f4f9 !important;
    font-family: 'Noto Sans KR', sans-serif;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #0a1628 !important;
    border-right: 1px solid rgba(30,111,196,0.2);
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stFileUploader label { color: rgba(255,255,255,0.6) !important; font-size: 12px !important; }

/* ── 헤더 배너 ── */
.wcs-header {
    background: linear-gradient(135deg, #0a1628 0%, #0d2d5e 60%, #1a4a8a 100%);
    border-radius: 14px;
    padding: 28px 36px;
    margin-bottom: 20px;
    position: relative;
    overflow: hidden;
}
.wcs-header::before {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse 60% 80% at 80% 50%, rgba(30,111,196,0.3), transparent 60%);
}
.wcs-header h1 {
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 26px;
    font-weight: 900;
    color: #fff !important;
    margin: 0 0 6px 0;
    position: relative;
}
.wcs-header p {
    font-size: 13px;
    color: rgba(255,255,255,0.6) !important;
    margin: 0;
    position: relative;
    font-family: 'DM Mono', monospace;
    letter-spacing: 1px;
}
.wcs-header .badge {
    display: inline-block;
    background: rgba(240,124,32,0.25);
    border: 1px solid rgba(240,124,32,0.5);
    border-radius: 4px;
    padding: 2px 10px;
    font-size: 10px;
    color: #f9a154 !important;
    letter-spacing: 2px;
    font-family: 'DM Mono', monospace;
    margin-bottom: 10px;
    position: relative;
}

/* ── 채팅 메시지 ── */
.chat-user {
    background: #1e6fc4;
    color: #fff !important;
    border-radius: 14px 14px 4px 14px;
    padding: 14px 18px;
    margin: 8px 0;
    font-size: 14px;
    line-height: 1.7;
    max-width: 80%;
    margin-left: auto;
}
.chat-assistant {
    background: #fff;
    color: #0a1628 !important;
    border-radius: 14px 14px 14px 4px;
    padding: 16px 20px;
    margin: 8px 0;
    font-size: 14px;
    line-height: 1.8;
    border: 1px solid #e0e8f0;
    box-shadow: 0 2px 12px rgba(10,22,40,0.06);
    max-width: 88%;
}
.chat-assistant strong { color: #0d2d5e; }

/* ── 에이전트 레이블 ── */
.agent-label {
    font-size: 10px;
    font-family: 'DM Mono', monospace;
    letter-spacing: 2px;
    color: #f07c20;
    margin-bottom: 4px;
    text-transform: uppercase;
}

/* ── 모드 카드 ── */
.mode-card {
    background: #fff;
    border: 2px solid #e0e8f0;
    border-radius: 12px;
    padding: 16px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
}
.mode-card:hover { border-color: #1e6fc4; }
.mode-card.active { border-color: #1e6fc4; background: #eef4fc; }

/* ── 상태 인디케이터 ── */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    background: #2cb67d;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse 2s infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}

/* ── 정보 박스 ── */
.info-box {
    background: linear-gradient(135deg, #eef4fc, #e8f0fa);
    border-left: 4px solid #1e6fc4;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 13px;
    color: #0d2d5e;
}
.warn-box {
    background: #fff8f0;
    border-left: 4px solid #f07c20;
    border-radius: 0 10px 10px 0;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 13px;
    color: #7a3f00;
}

/* ── 입력창 ── */
[data-testid="stChatInput"] textarea {
    font-family: 'Noto Sans KR', sans-serif !important;
    font-size: 14px !important;
    border-radius: 12px !important;
}

/* ── 사이드바 섹션 타이틀 ── */
.sb-title {
    font-size: 10px;
    font-family: 'DM Mono', monospace;
    letter-spacing: 3px;
    color: #f07c20 !important;
    text-transform: uppercase;
    margin: 20px 0 8px 0;
}

/* ── 예시 질문 버튼 ── */
.stButton > button {
    background: rgba(30,111,196,0.1) !important;
    border: 1px solid rgba(30,111,196,0.3) !important;
    color: #0d2d5e !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    padding: 6px 12px !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: #1e6fc4 !important;
    color: #fff !important;
    border-color: #1e6fc4 !important;
}

/* ── 툴팁 칩 ── */
.tool-chip {
    display: inline-block;
    background: #f0f4f9;
    border: 1px solid #d0dcea;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    color: #3d5a7a;
    margin: 2px;
    font-family: 'DM Mono', monospace;
}
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────
# AGENT MODES
# ──────────────────────────────────────────
AGENT_MODES = {
    "🧠 지식 검색 (RAG)": {
        "key": "rag",
        "desc": "업로드된 문서 기반 Q&A",
        "system": """당신은 K-water AI연구소의 **Water Co-Scientist** RAG 에이전트입니다.

역할:
- 사용자가 업로드한 K-water 내부 연구보고서, 정책문서, 기술문서를 기반으로 정확한 답변 제공
- 문서에 없는 내용은 "해당 문서에서 관련 내용을 찾을 수 없습니다"라고 명시
- 답변 시 관련 섹션/페이지를 참조로 제시
- 할루시네이션(Hallucination) 절대 금지

답변 형식:
1. 핵심 답변 먼저 (2-3문장)
2. 근거 (문서 내용 인용)
3. 관련 추가 정보 (있을 경우)

항상 한국어로 답변하며, 전문적이고 간결한 어조를 유지하세요."""
    },
    "🔬 기술 포트폴리오 분석": {
        "key": "portfolio",
        "desc": "기술 랭킹·트렌드 자동 분석",
        "system": """당신은 K-water AI연구소의 **Water Co-Scientist** 기술 포트폴리오 분석 에이전트입니다.

역할:
- K-water 보유 기술 자산의 가치와 랭킹 분석
- 글로벌 물 기술 트렌드와 K-water 기술 간 연관성 분석
- 유망 미래 기술 탐지 및 투자 우선순위 제안
- 기술 공백(Gap) 자동 탐지

분석 프레임워크:
- 기술 성숙도(TRL): 1-9 단계 평가
- 시장 영향력: 국내/글로벌 파급효과
- K-water 고유성: 타 기관 대비 차별성
- 미래 성장성: 5년 후 전망

답변 시 구조화된 분석 결과를 표나 항목으로 제시하세요. 항상 한국어로 답변하세요."""
    },
    "⚙️ 시뮬레이션 보조 (Tool Agent)": {
        "key": "simulation",
        "desc": "수리·수문 모델링 해석 보조",
        "system": """당신은 K-water AI연구소의 **Water Co-Scientist** Tool Agent 시뮬레이션 보조 에이전트입니다.

역할:
- 수리/수문 시뮬레이터 파라미터 설정 및 해석 보조
- HEC-RAS, SWMM, K-water 자체 모델 관련 질의응답
- 시뮬레이션 결과 해석 및 이상값 탐지
- 복잡한 수리학적 공식 계산 보조

보조 가능한 시뮬레이터:
- HEC-HMS / HEC-RAS (홍수 모델링)
- SWMM (하수도 시뮬레이션)
- QUAL2K (수질 모델링)
- K-water 댐 운영 시뮬레이터

답변 시 수식, 단위, 기준값을 명확히 제시하세요. 항상 한국어로 답변하세요."""
    },
    "📊 정책 인사이트 대시보드": {
        "key": "policy",
        "desc": "물 정책 분석 및 리포트 생성",
        "system": """당신은 K-water AI연구소의 **Water Co-Scientist** 정책 인사이트 에이전트입니다.

역할:
- 국내외 물 정책 동향 분석 및 요약
- K-water 사업과 국가 정책 간 정합성 분석
- 경영진 및 실무진을 위한 정책 브리핑 자동 생성
- 리스크 요인 및 기회 요인 식별

분석 영역:
- 과기부 AI Co-Scientist 국가 전략 연계
- 환경부 물관리 기본계획
- K-water 중장기 경영전략
- 글로벌 수자원 거버넌스 동향

항상 실무진이 바로 활용할 수 있는 형태로 구조화하여 한국어로 답변하세요."""
    },
}

EXAMPLE_QUESTIONS = {
    "rag": [
        "Water Co-Scientist의 4대 추진 축을 요약해줘",
        "K-water 연구 환경의 현실적 문제점은?",
        "Two-Track 보안 아키텍처를 설명해줘",
        "2026~2028 로드맵의 단계별 목표는?",
    ],
    "portfolio": [
        "K-water의 핵심 기술 자산 랭킹을 분석해줘",
        "글로벌 스마트 수처리 기술 트렌드는?",
        "K-water 기술 포트폴리오의 공백(Gap)은 어디인가?",
        "향후 5년간 집중 투자해야 할 유망 기술은?",
    ],
    "simulation": [
        "HEC-RAS에서 홍수 유량 계산 시 Manning 계수 설정 기준은?",
        "댐 방류량 시뮬레이션에서 이상값 판단 기준을 알려줘",
        "SWMM 모델에서 침투 파라미터 보정 방법은?",
        "수문 개도율과 하류 수위 관계를 시뮬레이션하고 싶어",
    ],
    "policy": [
        "과기부 AI Co-Scientist 정책과 K-water 전략의 정합성 분석",
        "2026년 물관리 분야 주요 정책 이슈 브리핑",
        "국내 스마트 물관리 정책 현황 요약",
        "Water Co-Scientist 사업의 예상 리스크 요인은?",
    ],
}


# ──────────────────────────────────────────
# SESSION STATE 초기화
# ──────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_mode" not in st.session_state:
    st.session_state.current_mode = "🧠 지식 검색 (RAG)"
if "pdf_content" not in st.session_state:
    st.session_state.pdf_content = None
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = None
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "total_tokens" not in st.session_state:
    st.session_state.total_tokens = 0


# ──────────────────────────────────────────
# HELPER: PDF → 텍스트 추출 (OpenAI는 PDF 직접 전달 불가)
# ──────────────────────────────────────────
def pdf_to_text(uploaded_file) -> str:
    if PdfReader is None:
        return "[pypdf 미설치 — pip install pypdf]"
    try:
        reader = PdfReader(io.BytesIO(uploaded_file.read()))
        pages = [page.extract_text() or "" for page in reader.pages]
        text = "\n\n".join(pages).strip()
        # 토큰 한도 대비 최대 12만 자 제한
        return text[:120_000]
    except Exception as e:
        return f"[PDF 텍스트 추출 오류: {e}]"


# ──────────────────────────────────────────
# HELPER: OpenAI o4-mini API 호출
# ──────────────────────────────────────────
def call_agent(api_key: str, mode_key: str, messages: list, pdf_text: str = None):
    client = openai.OpenAI(api_key=api_key)
    system_prompt = next(v["system"] for k, v in AGENT_MODES.items() if v["key"] == mode_key)

    # PDF 내용이 있으면 system prompt에 문서 컨텍스트로 주입
    if pdf_text:
        system_prompt += f"""

────────────────────────────────
[업로드된 K-water 내부 문서 전문]
아래 문서를 참조하여 답변하세요. 문서에 없는 내용은 반드시 "해당 문서에서 관련 내용을 찾을 수 없습니다"라고 명시하세요.

{pdf_text}
────────────────────────────────"""

    # OpenAI 메시지 포맷 구성
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg["role"], "content": msg["content"]})

    response = client.chat.completions.create(
        model="o4-mini",
        max_completion_tokens=4096,
        messages=api_messages,
    )

    answer = response.choices[0].message.content or ""
    tokens = response.usage.prompt_tokens + response.usage.completion_tokens
    return answer, tokens


# ──────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────
with st.sidebar:
    # 로고
    st.markdown("""
    <div style="padding: 20px 0 10px 0; text-align:center;">
        <div style="font-size:36px; margin-bottom:8px;">💧</div>
        <div style="font-family:'DM Mono',monospace; font-size:13px; font-weight:700; color:#fff; letter-spacing:2px;">WATER</div>
        <div style="font-family:'DM Mono',monospace; font-size:13px; color:#3a9dd8; letter-spacing:2px;">CO-SCIENTIST</div>
        <div style="font-size:10px; color:rgba(255,255,255,0.35); margin-top:4px; font-family:'DM Mono',monospace; letter-spacing:1px;">K-WATER AI LAB · 2026</div>
    </div>
    <hr style="border-color:rgba(255,255,255,0.1); margin:10px 0;">
    """, unsafe_allow_html=True)

    # ── API KEY ──
    st.markdown('<div class="sb-title">🔑 OpenAI API Key</div>', unsafe_allow_html=True)
    api_key_input = st.text_input(
        "", type="password",
        placeholder="sk-...",
        value=st.session_state.api_key,
        label_visibility="collapsed"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    # ── PDF 업로드 ──
    st.markdown('<div class="sb-title">📄 문서 업로드 (PDF)</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader(
        "", type=["pdf"],
        label_visibility="collapsed",
        help="K-water 내부 연구보고서, 정책문서 등을 업로드하세요"
    )

    if uploaded_pdf is not None:
        if st.session_state.pdf_name != uploaded_pdf.name:
            with st.spinner("PDF 텍스트 추출 중..."):
                st.session_state.pdf_content = pdf_to_text(uploaded_pdf)
                st.session_state.pdf_name = uploaded_pdf.name
                time.sleep(0.3)
        st.markdown(f"""
        <div style="background:rgba(44,182,125,0.15); border:1px solid rgba(44,182,125,0.4);
             border-radius:8px; padding:10px 14px; font-size:12px; color:#7fd6bc; margin-top:8px;">
            ✅ <strong style="color:#fff;">{uploaded_pdf.name}</strong><br>
            <span style="color:rgba(255,255,255,0.5); font-size:10px;">문서 로드 완료 · RAG 모드에서 사용 가능</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:rgba(255,255,255,0.04); border:1px dashed rgba(255,255,255,0.15);
             border-radius:8px; padding:10px 14px; font-size:11px; color:rgba(255,255,255,0.4); margin-top:4px; text-align:center;">
            PDF를 드래그하거나 클릭해서 업로드하세요
        </div>
        """, unsafe_allow_html=True)

    # ── 에이전트 모드 선택 ──
    st.markdown('<div class="sb-title">🤖 에이전트 모드</div>', unsafe_allow_html=True)
    selected_mode = st.selectbox(
        "",
        list(AGENT_MODES.keys()),
        index=list(AGENT_MODES.keys()).index(st.session_state.current_mode),
        label_visibility="collapsed"
    )

    if selected_mode != st.session_state.current_mode:
        st.session_state.current_mode = selected_mode
        st.session_state.messages = []
        st.rerun()

    mode_info = AGENT_MODES[selected_mode]
    st.markdown(f"""
    <div style="background:rgba(30,111,196,0.12); border:1px solid rgba(30,111,196,0.25);
         border-radius:8px; padding:10px 14px; font-size:12px; color:rgba(255,255,255,0.65); margin-top:4px;">
        <span class="status-dot"></span>{mode_info['desc']}
    </div>
    """, unsafe_allow_html=True)

    # ── 예시 질문 ──
    st.markdown('<div class="sb-title">💬 예시 질문</div>', unsafe_allow_html=True)
    mode_key = mode_info["key"]
    for q in EXAMPLE_QUESTIONS[mode_key]:
        if st.button(q, key=f"ex_{q[:20]}"):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()

    # ── 대화 초기화 ──
    st.markdown('<div class="sb-title">🗑 관리</div>', unsafe_allow_html=True)
    if st.button("대화 초기화", key="clear"):
        st.session_state.messages = []
        st.session_state.total_tokens = 0
        st.rerun()

    # ── 통계 ──
    st.markdown(f"""
    <hr style="border-color:rgba(255,255,255,0.1); margin:16px 0 10px 0;">
    <div style="font-size:11px; color:rgba(255,255,255,0.3); font-family:'DM Mono',monospace; line-height:2;">
        대화 수: {len([m for m in st.session_state.messages if m['role']=='user'])}<br>
        토큰 사용: {st.session_state.total_tokens:,}<br>
        모드: {mode_key.upper()}
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────

# ── 헤더 ──
st.markdown(f"""
<div class="wcs-header">
    <div class="badge">K-WATER AI연구소 · DEMO v1.0</div>
    <h1>💧 Water Co-Scientist</h1>
    <p>현재 모드: {selected_mode} &nbsp;|&nbsp; {mode_info['desc']}</p>
</div>
""", unsafe_allow_html=True)

# ── API KEY 경고 ──
if not st.session_state.api_key:
    st.markdown("""
    <div class="warn-box">
        ⚠️ <strong>OpenAI API Key가 필요합니다.</strong><br>
        좌측 사이드바에서 API Key를 입력하면 Water Co-Scientist 에이전트가 활성화됩니다.
    </div>
    """, unsafe_allow_html=True)

# ── 환영 메시지 (첫 대화) ──
if not st.session_state.messages:
    col1, col2, col3, col4 = st.columns(4)
    for col, (mode_name, mode_data) in zip([col1, col2, col3, col4], AGENT_MODES.items()):
        is_active = mode_name == selected_mode
        with col:
            st.markdown(f"""
            <div style="background:{'#1e6fc4' if is_active else '#fff'};
                 border:2px solid {'#1e6fc4' if is_active else '#e0e8f0'};
                 border-radius:12px; padding:16px; text-align:center;
                 margin-bottom:16px;">
                <div style="font-size:24px; margin-bottom:8px;">{mode_name.split()[0]}</div>
                <div style="font-size:13px; font-weight:700;
                     color:{'#fff' if is_active else '#0a1628'}; margin-bottom:4px;">
                    {' '.join(mode_name.split()[1:])}
                </div>
                <div style="font-size:11px; color:{'rgba(255,255,255,0.7)' if is_active else '#8fa3bc'};">
                    {mode_data['desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="info-box">
        <strong>👋 Water Co-Scientist에 오신 것을 환영합니다!</strong><br>
        현재 <strong>{selected_mode}</strong> 모드가 활성화되어 있습니다.
        {'PDF가 업로드되지 않았습니다. 사이드바에서 K-water 문서를 업로드하면 문서 기반 Q&A가 가능합니다.' if not st.session_state.pdf_content else f'📄 <strong>{st.session_state.pdf_name}</strong> 문서를 기반으로 답변합니다.'}
        <br>좌측 예시 질문을 클릭하거나 아래 입력창에 질문을 입력하세요.
    </div>
    """, unsafe_allow_html=True)


# ── 채팅 히스토리 출력 ──
chat_container = st.container()
with chat_container:
    for i, msg in enumerate(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex; justify-content:flex-end; margin:12px 0;">
                <div>
                    <div style="text-align:right; font-size:10px; font-family:'DM Mono',monospace;
                         color:#8fa3bc; margin-bottom:4px; letter-spacing:1px;">YOU</div>
                    <div class="chat-user">{msg['content']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex; justify-content:flex-start; margin:12px 0;">
                <div style="max-width:88%;">
                    <div class="agent-label">💧 WATER CO-SCIENTIST · {mode_key.upper()}</div>
                    <div class="chat-assistant">{msg['content'].replace(chr(10), '<br>')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)


# ── 마지막 메시지가 user이면 → API 호출 ──
if (st.session_state.messages
        and st.session_state.messages[-1]["role"] == "user"
        and st.session_state.api_key):

    with st.spinner("🔄 Water Co-Scientist 분석 중..."):
        try:
            answer, tokens = call_agent(
                api_key=st.session_state.api_key,
                mode_key=mode_info["key"],
                messages=st.session_state.messages,
                pdf_text=st.session_state.pdf_content,
            )
            st.session_state.messages.append({"role": "assistant", "content": answer})
            st.session_state.total_tokens += tokens
            st.rerun()
        except openai.AuthenticationError:
            st.error("❌ API Key가 유효하지 않습니다. 사이드바에서 올바른 OpenAI API Key를 입력하세요.")
        except openai.RateLimitError:
            st.error("⚠️ API 호출 한도에 도달했습니다. 잠시 후 다시 시도하세요.")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")

elif (st.session_state.messages
      and st.session_state.messages[-1]["role"] == "user"
      and not st.session_state.api_key):
    st.warning("💡 API Key를 입력해야 에이전트가 응답합니다.")


# ── 채팅 입력 ──
user_input = st.chat_input(
    f"💧 {mode_info['desc']}에 대해 질문하세요...",
    disabled=not st.session_state.api_key,
)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()


# ──────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────
st.markdown("""
<hr style="border-color:#d0dcea; margin:32px 0 16px 0;">
<div style="display:flex; justify-content:space-between; align-items:center;
     font-size:11px; font-family:'DM Mono',monospace; color:#8fa3bc; padding-bottom:20px;">
    <div>
        <span style="color:#1e6fc4; font-weight:700;">K-WATER</span> · AI연구소 · Water Co-Scientist Demo
    </div>
    <div>
        <span class="tool-chip">o4-mini</span>
        <span class="tool-chip">RAG Pipeline</span>
        <span class="tool-chip">Multi-Agent</span>
        <span class="tool-chip">Sovereign AI</span>
    </div>
    <div>2026 · CONFIDENTIAL DRAFT</div>
</div>
""", unsafe_allow_html=True)
