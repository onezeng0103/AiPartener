import streamlit as st
import json
import os
from datetime import datetime
from openai import OpenAI

# ==================== 配置区 ====================
API_KEY = os.getenv("MOONSHOT_API_KEY", "sk-7IptY0EiK7WEy1cxCQy40atcl0IK41Kxw6tTrURViUpopxrB")
BASE_URL = "https://api.moonshot.cn/v1"
MODEL_NAME = "kimi-k2.6"
SESSION_DIR = "session"

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="AI 智能伴侣",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==================== 会话状态初始化 ====================
def init_session_state():
    """初始化 Streamlit 会话状态，避免 KeyError"""
    defaults = {
        "nick_name": "周敏",
        "personality": "活泼开朗的江西姑娘",
        "message": [],
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_session": None,   # 当前加载的历史会话文件名
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ==================== 文件操作 ====================
def ensure_session_dir():
    """确保 session 目录存在"""
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)


def read_session_file() -> list:
    """读取 session 目录下所有会话文件名（按时间倒序）"""
    ensure_session_dir()
    session_list = [
        f[:-5] for f in os.listdir(SESSION_DIR) if f.endswith(".json")
    ]
    session_list.sort(reverse=True)
    return session_list


def save_session(session_name: str = None):
    """保存当前会话到 JSON 文件（统一存储结构）"""
    if not st.session_state.message:
        return
    ensure_session_dir()
    session_name = session_name or st.session_state.current_time
    session_data = {
        "nick_name": st.session_state.nick_name,
        "personality": st.session_state.personality,
        "message": st.session_state.message,
        "current_time": st.session_state.current_time,
    }
    with open(f"{SESSION_DIR}/{session_name}.json", "w", encoding="utf-8") as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)


def load_session(session_name: str):
    """加载指定会话到 session_state"""
    path = f"{SESSION_DIR}/{session_name}.json"
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        st.session_state.message = data
        st.session_state.current_session = session_name
    else:
        st.session_state.message = data.get("message", [])
        st.session_state.nick_name = data.get("nick_name", st.session_state.nick_name)
        st.session_state.personality = data.get("personality", st.session_state.personality)
        st.session_state.current_time = data.get("current_time", st.session_state.current_time)
        st.session_state.current_session = session_name


def delete_session(session_name: str):
    """删除指定会话文件，若删除的是当前会话则重置状态"""
    path = f"{SESSION_DIR}/{session_name}.json"
    if os.path.exists(path):
        os.remove(path)
    if st.session_state.current_session == session_name:
        st.session_state.message = []
        st.session_state.current_session = None
        st.session_state.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def new_session():
    """开启新会话（自动保存旧会话）"""
    save_session()
    st.session_state.message = []
    st.session_state.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.current_session = None


# ==================== 系统提示词 ====================
SYSTEM_PROMPT = """
你现在扮演用户的恋人/伴侣，你的名字是%s。
用户是你的伴侣，你要用亲密、活泼的语气和用户聊天。

规则:
    1. 每次只回一条消息
    2. 禁止任何场景或状态描述性文字
    3. 匹配用户的语言
    4. 回复简短，像微信聊天一样
    5. 需要的话可以用🥰😘🌸等 emoji 表情
    6. 用符合伴侣性格的方式对话
    7. 回复的内容，要充分体现伴侣的特征

伴侣性格:
    %s

你必须严格遵守上述规则来回复用户。
"""


# ==================== 客户端（懒加载） ====================
@st.cache_resource
def get_client():
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ==================== 会话信息展示 ====================
def render_session_info():
    """在标题下方显示当前加载的会话信息（仅当加载了历史会话时显示）"""
    if st.session_state.current_session:
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 3, 2])
            with col1:
                st.markdown(f"**👤 昵称：** {st.session_state.nick_name}")
            with col2:
                st.markdown(f"**💖 性格：** {st.session_state.personality}")
            with col3:
                st.markdown(f"**🕐 会话时间：** {st.session_state.current_session}")


# ==================== 侧边栏 ====================
def render_sidebar():
    with st.sidebar:
        st.subheader("🎛️ AI 控制面板")

        if st.button("新建会话", use_container_width=True, icon="✏️"):
            new_session()
            st.rerun()

        if st.button("清空当前对话", use_container_width=True, icon="🧹"):
            st.session_state.message = []
            st.session_state.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state.current_session = None
            st.rerun()

        st.divider()
        st.text("📚 历史会话")

        session_list = read_session_file()
        if not session_list:
            st.caption("暂无历史会话")

        for session in session_list:
            col1, col2 = st.columns([4, 1])
            with col1:
                is_current = session == st.session_state.current_session
                if st.button(
                    session,
                    type="primary" if is_current else "secondary",
                    use_container_width=True,
                    key=f"load_{session}",
                    icon="📃",
                ):
                    save_session()
                    load_session(session)
                    st.rerun()
            with col2:
                if st.button("", use_container_width=True, key=f"delete_{session}", icon="🗑️"):
                    delete_session(session)
                    st.rerun()

        st.divider()

        st.text_input("昵称", key="nick_name", placeholder="请输入伴侣昵称")
        st.text_area("性格", key="personality", placeholder="请输入伴侣性格", height=100)


# ==================== 主聊天逻辑 ====================
def render_chat_history():
    """展示历史消息"""
    for message in st.session_state.message:
        with st.chat_message(message["role"]):
            st.write(message["content"])


def stream_reply(messages):
    """调用 Kimi API 流式返回"""
    try:
        response = get_client().chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            stream=True,
            reasoning_effort="low",
        )
        full_content = ""
        placeholder = st.empty()
        for chunk in response:
            delta = chunk.choices[0].delta.content
            if delta:
                full_content += delta
                placeholder.write(full_content)
        return full_content
    except Exception as e:
        return f"⚠️ 出错了：{e}"


def handle_user_input(prompt: str):
    """处理用户输入并调用模型"""
    st.session_state.message.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
            % (st.session_state.nick_name, st.session_state.personality),
        },
        *st.session_state.message,
    ]

    with st.chat_message("assistant"):
        full_content = stream_reply(messages)

    st.session_state.message.append({"role": "assistant", "content": full_content})
    save_session()


# ==================== 入口 ====================
def main():
    st.title("🤖 AI 智能伴侣")
    init_session_state()
    render_sidebar()
    render_session_info()          # ← 标题下方显示会话信息
    render_chat_history()

    prompt = st.chat_input("请输入你要问的问题…")
    if prompt:
        handle_user_input(prompt)
        st.rerun()


if __name__ == "__main__":
    main()