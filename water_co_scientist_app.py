import streamlit as st
import openai
import base64
import io
import time
import re
import json
import pandas as pd
import plotly.express as px
from datetime import datetime

# PDF 및 이미지 처리를 위한 라이브러리
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

# ──────────────────────────────────────────
# PAGE CONFIG & CSS (기존 유지)
# ──────────────────────────────────────────
st.set_page_config(
    page_title="Water Co-Scientist | K-water AI연구소",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700;900&family=DM+Mono:wght@400;500&display=swap');
html, body, [data-testid="stAppViewContainer"] { background: #f0f4f9 !important; font-family: 'Noto Sans KR', sans-serif; }
[data-testid="stSidebar"] { background: #0a1628 !important; border-right: 1px solid rgba(30,111,196,0.2); }
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.85) !important; }
.wcs-header { background: linear-gradient(135deg, #0a1628 0%, #0d2d5e 60%, #1a4a8a 100%); border-radius: 14px; padding: 28px 36px; margin-bottom: 20px; position: relative; overflow: hidden; }
.wcs-header h1 { font-size: 26px; font-weight: 900; color: #fff !important; margin: 0; }
.chat-user { background: #1e6fc4; color: #fff !important; border-radius: 14px 14px 4px 14px; padding: 14px 18px; margin: 8px 0; font-size: 14px; max-width: 80%; margin-left: auto; }
.chat-assistant { background: #fff; color: #0a1628 !important; border-radius: 14px 14px 14px 4px; padding: 16px 20px; margin: 8px 0; font-size: 14px; border: 1px solid #e0e8f0; box-shadow: 0 2px 12px rgba(10,22,40,0.06); max-width: 88%; }
.agent-label { font-size: 10px; font-family: 'DM Mono', monospace; letter-spacing: 2px; color: #f07c20; margin-bottom: 4px; text-transform: uppercase; }
.info-box { background: linear-gradient(135deg, #eef4fc, #e8f0fa); border-left: 4px solid #1e6fc4; border-radius: 0 10px 10px 0; padding: 14px 18px; margin: 12px 0; font-size: 13px; color: #0d2d5e; }
.warn-box { background: #fff8f0; border-left: 4px solid #f07c20; border-radius: 0 10px 10px 0; padding: 14px 18px; margin: 12px 0; font-size: 13px; color: #7a3f00; }
.sb-title { font-size: 10px; font-family: 'DM Mono', monospace; letter-spacing: 3px; color: #f07c20 !important; text-transform: uppercase; margin: 20px 0 8px 0; }
.tool-chip { display: inline-block; background: #f0f4f9; border: 1px solid #d0dcea; border-radius: 20px; padding: 3px 10px; font-size: 11px; color: #3d5a7a; margin: 2px; font-family: 'DM Mono', monospace; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────
# AGENT MODES (기존 유지)
# ──────────────────────────────────────────
AGENT_MODES = {
    "🧠 지식 검색 (RAG)": {
        "key": "rag",
        "desc": "업로드된 문서 기반 Q&A (표/그림 분석 포함)",
        "system": "당신은 K-water AI연구소의 Water Co-Scientist RAG 에이전트입니다. 문서 내 텍스트뿐만 아니라 제공된 이미지(표, 그래프)를 분석하여 답변하세요."
    },
    "🔬 기술 포트폴리오 분석": {
        "key": "portfolio",
        "desc": "기술 랭킹·트렌드 자동 분석",
        "system": "기술 자산 가치와 랭킹을 분석합니다. 수치 데이터가 있으면 시각화 형식을 활용하세요."
    },
    "⚙️ 시뮬레이션 보조 (Tool Agent)": {
        "key": "simulation",
        "desc": "수리·수문 모델링 해석 보조",
        "system": "수리/수문 모델링 파라미터를 계산하고 결과를 시각화하여 설명합니다."
    },
    "📊 정책 인사이트 대시보드": {
        "key": "policy",
        "desc": "물 정책 분석 및 리포트 생성",
        "system": "정책 동향을 요약하고 리스크 요인을 분석합니다."
    },
}

EXAMPLE_QUESTIONS = {
    "rag": ["문서 내 주요 수치 데이터를 표로 정리하고 그래프로 그려줘", "그림에 나온 시스템 구성도를 설명해줘"],
    "portfolio": ["K-water 핵심 기술의 TRL 수준을 차트로 보여줘"],
    "simulation": ["유량 변화에 따른 수위 변동 추이를 그래프로 그려줘"],
    "policy": ["연도별 물관리 예산 비중을 분석해줘"],
}

# ──────────────────────────────────────────
# HELPERS: PDF 처리 & 차트 렌더링
# ──────────────────────────────────────────

def process_pdf_vlm(uploaded_file):
    """PDF에서 텍스트와 이미지(VLM용)를 모두 추출"""
    if fitz is None: return "PyMuPDF 미설치", []
    
    doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
    full_text = ""
    images_b64 = []
    
    for i, page in enumerate(doc):
        full_text += page.get_text()
        # 데모 효율을 위해 앞 5페이지만 이미지 변환
        if i < 5:
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img_data = pix.tobytes("jpg")
            images_b64.append(base64.b64encode(img_data).decode('utf-8'))
    
    return full_text[:60000], images_b64

def render_plotly_chart(text):
    """답변 내 JSON을 찾아 Plotly 차트로 변환"""
    match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1))
            if "chart_type" in data or "chart" in data:
                df = pd.DataFrame(data["data"])
                title = data.get("title", "데이터 분석 결과")
                
                if data.get("chart_type") == "line" or data.get("chart") == "line":
                    fig = px.line(df, x=data["x"], y=data["y"], title=title, markers=True)
                else:
                    fig = px.bar(df, x=data["x"], y=data["y"], title=title, color=data["y"])
                
                fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
                st.plotly_chart(fig, use_container_width=True)
                return True
        except: pass
    return False

def call_agent_vlm(api_key, mode_key, messages, pdf_text="", pdf_images=[]):
    """GPT-4o-mini(VLM)를 사용하여 텍스트와 이미지를 동시 분석"""
    client = openai.OpenAI(api_key=api_key)
    mode_info = AGENT_MODES[st.session_state.current_mode]
    
    system_instr = mode_info["system"] + """
    \n[시각화 지침] 데이터를 설명할 때 시각화가 가능하다면 반드시 아래 JSON 형식을 답변 끝에 포함하세요:
    ```json
    {"chart_type": "bar", "title": "제목", "x": "항목명", "y": "수치명", "data": [{"항목명": "A", "수치명": 10}, ...]}
    ```
    """
    
    content = [{"type": "text", "text": f"{system_instr}\n\n문서 컨텍스트: {pdf_text}"}]
    
    # 이미지 컨텍스트 주입 (VLM)
    for img in pdf_images:
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})
    
    # 사용자 질문
    content.append({"type": "text", "text": messages[-1]["content"]})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": content}],
        max_tokens=2048,
    )
    return response.choices[0].message.content, response.usage.total_tokens

# ──────────────────────────────────────────
# SESSION STATE & SIDEBAR (기존 구조 유지)
# ──────────────────────────────────────────
if "messages" not in st.session_state: st.session_state.messages = []
if "current_mode" not in st.session_state: st.session_state.current_mode = "🧠 지식 검색 (RAG)"
if "pdf_content" not in st.session_state: st.session_state.pdf_content = ""
if "pdf_images" not in st.session_state: st.session_state.pdf_images = []
if "api_key" not in st.session_state: st.session_state.api_key = ""
if "total_tokens" not in st.session_state: st.session_state.total_tokens = 0

with st.sidebar:
    st.markdown('<div style="text-align:center; padding:20px 0;"><div style="font-size:36px;">💧</div><div style="font-family:\'DM Mono\',monospace; font-size:13px; font-weight:700; color:#fff; letter-spacing:2px;">WATER CO-SCIENTIST</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="sb-title">🔑 API Key</div>', unsafe_allow_html=True)
    st.session_state.api_key = st.text_input("", type="password", placeholder="sk-...", value=st.session_state.api_key, label_visibility="collapsed")

    st.markdown('<div class="sb-title">📄 문서 업로드 (VLM 분석)</div>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("", type=["pdf"], label_visibility="collapsed")

    if uploaded_pdf:
        if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_pdf.name:
            with st.spinner("이미지 및 텍스트 분석 중..."):
                txt, imgs = process_pdf_vlm(uploaded_pdf)
                st.session_state.pdf_content = txt
                st.session_state.pdf_images = imgs
                st.session_state.last_uploaded = uploaded_pdf.name
            st.success(f"로드 완료: {uploaded_pdf.name}")

    st.markdown('<div class="sb-title">🤖 모드</div>', unsafe_allow_html=True)
    selected_mode = st.selectbox("", list(AGENT_MODES.keys()), label_visibility="collapsed")
    if selected_mode != st.session_state.current_mode:
        st.session_state.current_mode = selected_mode
        st.session_state.messages = []
        st.rerun()

    st.markdown('<div class="sb-title">💬 예시</div>', unsafe_allow_html=True)
    for q in EXAMPLE_QUESTIONS.get(AGENT_MODES[st.session_state.current_mode]["key"], []):
        if st.button(q):
            st.session_state.messages.append({"role": "user", "content": q})
            st.rerun()

# ──────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────
st.markdown(f'<div class="wcs-header"><div style="background:rgba(240,124,32,0.2); border:1px solid #f07c20; border-radius:4px; padding:2px 8px; font-size:10px; color:#f07c20; display:inline-block; margin-bottom:8px;">DEMO V2.0 (VLM + PLOTLY)</div><h1>💧 Water Co-Scientist</h1><p>{st.session_state.current_mode}</p></div>', unsafe_allow_html=True)

if not st.session_state.api_key:
    st.info("좌측 사이드바에 OpenAI API Key를 입력해주세요.")

# 채팅 히스토리 출력
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="agent-label">💧 WATER CO-SCIENTIST</div><div class="chat-assistant">{msg["content"]}</div>', unsafe_allow_html=True)
        render_plotly_chart(msg["content"])

# 질문 처리
if user_input := st.chat_input("질문을 입력하세요..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.rerun()

# AI 응답 생성
if st.session_state.messages and st.session_state.messages[-1]["role"] == "user" and st.session_state.api_key:
    with st.spinner("AI 분석 및 시각화 중..."):
        try:
            ans, tkn = call_agent_vlm(
                st.session_state.api_key, 
                AGENT_MODES[st.session_state.current_mode]["key"],
                st.session_state.messages,
                st.session_state.pdf_content,
                st.session_state.pdf_images
            )
            st.session_state.messages.append({"role": "assistant", "content": ans})
            st.session_state.total_tokens += tkn
            st.rerun()
        except Exception as e:
            st.error(f"오류: {e}")

st.markdown('<div style="font-size:10px; color:#8fa3bc; text-align:right; margin-top:50px;">K-WATER AI LAB · 2026 · Confidential</div>', unsafe_allow_html=True)
