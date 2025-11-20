import streamlit as st
from openai import OpenAI
from typing import List, Dict


def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


st.set_page_config(page_title="야식 추천 챗봇", page_icon="🍜")

st.title("🍽️ 야식 추천 챗봇")
st.write("야식 메뉴를 추천해주고 대화를 이어가는 챗봇입니다. 바로 사용하려면 `.streamlit/secrets.toml`에 `OPENAI_API_KEY`를 설정하세요.")

# Use the API key from Streamlit secrets. No input box shown to the user.
openai_api_key = st.secrets.get("OPENAI_API_KEY")
if not openai_api_key:
    st.error("앱 설정에 `OPENAI_API_KEY`가 없습니다. `.streamlit/secrets.toml`에 키를 추가하세요.")
    st.stop()

client = get_client(openai_api_key)


# System prompt: assistant persona and behavior for night-snack recommending chatbot
SYSTEM_PROMPT = (
    "너는 야식 메뉴 추천 전문가이자 친절한 챗봇이야. 사용자가 현재 기분, 식성, 예산, 인원수, 원재료 제한(예: 채식) 등을 알려주면 "
    "그에 맞는 야식 메뉴를 2~4가지 추천하고 각 메뉴에 간단한 설명(맛/양/조리 난이도)과 예상 가격을 적어줘. "
    "추가로 사용자가 더 원하면 레시피 요약(간단 단계)이나 배달 가능한지 추천해줘. 대화는 자연스럽고 친근하게 이어가고, 불필요한 길게 설명은 피해줘."
)


def api_chat(messages: List[Dict]) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
            max_tokens=500,
        )
        # Try attribute access, then dict-style access as fallback
        choice = resp.choices[0]
        assistant_msg = None
        if hasattr(choice, "message"):
            msg = choice.message
            assistant_msg = getattr(msg, "content", None) or msg.get("content")
        else:
            assistant_msg = choice["message"]["content"] if ("message" in choice) else None
        if not assistant_msg:
            # Fallback to text field if present
            assistant_msg = getattr(resp, "text", None) or resp.get("text")
        return assistant_msg or "(응답을 받아오지 못했습니다.)"
    except Exception as e:
        return f"오류가 발생했습니다: {e}"


if "history" not in st.session_state:
    # history holds dicts with role: 'user'|'assistant' and content
    st.session_state.history = []


def display_history():
    for msg in st.session_state.history:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        with st.chat_message(role):
            st.markdown(content)


col1, col2 = st.columns([9, 1])
with col2:
    if st.button("새 대화"):
        st.session_state.history = []

display_history()

user_input = st.chat_input("원하시는 야식 스타일을 알려주세요 — 예: 매운 것, 가벼운 한 끼, 2인분, 예산 1만원 등")
if user_input:
    # Append user message and show immediately
    st.session_state.history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build messages for API: system prompt + history
    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in st.session_state.history:
        api_messages.append({"role": m["role"], "content": m["content"]})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("작성 중...")

    assistant_text = api_chat(api_messages)

    # Replace placeholder with assistant response and store
    st.session_state.history.append({"role": "assistant", "content": assistant_text})
    # Update the placeholder directly instead of calling experimental_rerun()
    try:
        placeholder.markdown(assistant_text)
    except Exception:
        # If placeholder is unavailable for some reason, fallback to showing the text
        with st.chat_message("assistant"):
            st.markdown(assistant_text)

