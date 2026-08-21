import streamlit as st
import requests
import os
from typing import List, Tuple

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="RESONA Chatbot", page_icon="🤖", layout="centered")

# Inject custom CSS for a cleaner, ChatGPT-like UI
st.markdown("""
<style>
[data-testid="stSidebar"] {
    min-width: 260px !important;
    max-width: 260px !important;
}
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 3rem !important;
    max-width: 900px !important;
}
.stButton button {
    border-radius: 20px !important;
    border: 1px solid #d9d9e3 !important;
    background-color: transparent !important;
    transition: all 0.2s ease-in-out;
}
.stButton button:hover {
    background-color: #ececf1 !important;
    border-color: #d9d9e3 !important;
    color: #343541 !important;
}
.stButton button[kind="primary"] {
    background: linear-gradient(90deg, #2b5876 0%, #4e4376 100%) !important; 
    /* Or the green gradient from screenshot: */
    background: linear-gradient(90deg, #2e606b 0%, #87b372 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: bold;
}
.stButton button[kind="primary"]:hover {
    opacity: 0.9;
}
.login-header {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: #1f2937;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state for Auth and Chat
if "token" not in st.session_state:
    st.session_state.token = None
if "fullname" not in st.session_state:
    st.session_state.fullname = None
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "login"

def get_auth_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}

def login_user(email, password):
    try:
        response = requests.post(f"{BACKEND_URL}/login", data={"username": email, "password": password})
        if response.status_code == 200:
            data = response.json()
            st.session_state.token = data["access_token"]
            st.session_state.fullname = data["fullname"]
            st.rerun()
        else:
            st.error("Invalid email or password.")
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")

def register_user(fullname, email, password):
    try:
        payload = {"fullname": fullname, "email": email, "password": password}
        response = requests.post(f"{BACKEND_URL}/register", json=payload)
        if response.status_code == 200:
            st.success("Registration successful! Please login.")
            st.session_state.auth_mode = "login"
            st.rerun()
        else:
            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")

def logout_user():
    st.session_state.token = None
    st.session_state.fullname = None
    st.session_state.current_session_id = None
    st.session_state.messages = []
    st.rerun()

def load_session(session_id):
    st.session_state.current_session_id = session_id
    try:
        response = requests.get(f"{BACKEND_URL}/sessions/{session_id}", headers=get_auth_headers())
        if response.status_code == 200:
            msgs = response.json()
            st.session_state.messages = []
            for msg in msgs:
                content = msg["content"]
                if msg["role"] == "assistant" and msg.get("sources"):
                    sources = msg["sources"]
                    content += "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources])
                st.session_state.messages.append({"role": msg["role"], "content": content})
    except Exception as e:
        st.error(f"Failed to load session: {e}")


# ==========================================
# AUTHENTICATION UI
# ==========================================
if not st.session_state.token:
    # Add an outer container for styling
    with st.container():
        # Create a 50/50 split layout
        col1, col2 = st.columns([1.1, 1], gap="large")
        
        with col1:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.session_state.auth_mode == "login":
                st.markdown('<div class="login-header">Log in</div>', unsafe_allow_html=True)
                st.markdown("Welcome back to RESONA Document Intelligence")
                
                login_email = st.text_input("✉️ Email or Phone Number", key="login_email")
                login_password = st.text_input("🔒 Password", type="password", key="login_password")
                
                cc1, cc2 = st.columns([1, 1])
                cc1.checkbox("remember me")
                cc2.markdown("<div style='text-align: right; margin-top: 5px;'><a href='#' style='color: #4b5563; text-decoration: none; font-size: 0.9em;'>Forgot Password?</a></div>", unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Log in", type="primary", use_container_width=True):
                    if login_email and login_password:
                        login_user(login_email, login_password)
                    else:
                        st.warning("Please enter email and password.")
                        
                st.markdown("<div style='text-align: center; margin: 15px 0; color: #6b7280; font-size: 0.9em;'>Log in with</div>", unsafe_allow_html=True)
                sc1, sc2, sc3, sc4 = st.columns([1, 2, 2, 1])
                with sc2:
                    st.button("🌐 Google", use_container_width=True)
                with sc3:
                    st.button("📘 Facebook", use_container_width=True)
                        
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown("<span style='color: #6b7280;'>Don't have an account? </span>", unsafe_allow_html=True)
                if st.button("Register Now", key="switch_to_reg"):
                    st.session_state.auth_mode = "register"
                    st.rerun()

            else:
                st.markdown('<div class="login-header">Register</div>', unsafe_allow_html=True)
                st.markdown("Create a new RESONA account")
                
                reg_fullname = st.text_input("👤 Full Name")
                reg_email = st.text_input("✉️ Email", key="reg_email")
                reg_password = st.text_input("🔒 Password", type="password", key="reg_password")
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("Create Account", type="primary", use_container_width=True):
                    if reg_fullname and reg_email and reg_password:
                        register_user(reg_fullname, reg_email, reg_password)
                    else:
                        st.warning("Please fill in all fields.")
                        
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown("<span style='color: #6b7280;'>Already have an account? </span>", unsafe_allow_html=True)
                if st.button("Log In", key="switch_to_login"):
                    st.session_state.auth_mode = "login"
                    st.rerun()

        with col2:
            st.markdown("<br><br><br><br>", unsafe_allow_html=True)
            st.image("logo.png", use_container_width=True)

# ==========================================
# MAIN APP UI (LOGGED IN)
# ==========================================
else:
    # Sidebar
    with st.sidebar:
        # Logo and Title
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image("logo.png", use_container_width=True)
        with col2:
            st.title("RESONA")
            
        st.markdown(f"**Welcome, {st.session_state.fullname}!**")
        
        colA, colB = st.columns(2)
        with colA:
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_session_id = None
                st.session_state.messages = []
                st.rerun()
        with colB:
            if st.button("Logout", key="logout_btn", use_container_width=True):
                logout_user()
            
        st.markdown("---")
        
        st.header("1. Upload Documents")
        uploaded_files = st.file_uploader(
            "Upload documents here", 
            accept_multiple_files=True,
            type=["pdf", "docx", "csv", "txt"]
        )
        
        if st.button("Process Files"):
            if uploaded_files:
                with st.spinner("Processing files..."):
                    files = [("files", (file.name, file.getvalue(), file.type)) for file in uploaded_files]
                    try:
                        response = requests.post(f"{BACKEND_URL}/upload", files=files, headers=get_auth_headers())
                        if response.status_code == 200:
                            st.success("Files processed successfully!")
                        else:
                            st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Failed to connect to backend: {e}")
            else:
                st.warning("Please upload at least one file.")
                
        st.header("2. Chat History")
        if st.button("➕ New Chat", use_container_width=True):
            st.session_state.current_session_id = None
            st.session_state.messages = []
            st.rerun()
            
        st.markdown("---")
        try:
            response = requests.get(f"{BACKEND_URL}/sessions", headers=get_auth_headers())
            if response.status_code == 200:
                sessions = response.json()
                for s in sessions:
                    is_active = (s["id"] == st.session_state.current_session_id)
                    btn_type = "primary" if is_active else "secondary"
                    if st.button(f"💬 {s['title']}", key=s['id'], use_container_width=True, type=btn_type):
                        load_session(s["id"])
                        st.rerun()
        except:
            st.warning("Could not load chat history.")

        st.header("3. Manage Database")
        if st.button("Clear Vector DB"):
            try:
                response = requests.delete(f"{BACKEND_URL}/clear", headers=get_auth_headers())
                if response.status_code == 200:
                    st.success("Database cleared!")
                else:
                    st.error(f"Failed to clear database: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Failed to connect to backend: {e}")

    # Main Chat Area
    if not st.session_state.messages:
        st.title(f"Hi {st.session_state.fullname}, what's up?")
        st.markdown("Ask me a question about your documents, or search the web!")

    for message in st.session_state.messages:
        avatar_img = "user_avatar.jpg" if message["role"] == "user" else "bot_avatar.jpg"
        with st.chat_message(message["role"], avatar=avatar_img):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask a question..."):
        st.chat_message("user", avatar="user_avatar.jpg").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        payload = {
            "question": prompt,
            "session_id": st.session_state.current_session_id
        }
        
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{BACKEND_URL}/chat", json=payload, headers=get_auth_headers())
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    session_id = data.get("session_id")
                    
                    source_text = "\n\n**Sources:**\n" + "\n".join([f"- {s}" for s in sources]) if sources else ""
                    full_response = answer + source_text
                    
                    if not st.session_state.current_session_id:
                        st.session_state.current_session_id = session_id
                    
                    with st.chat_message("assistant", avatar="bot_avatar.jpg"):
                        st.markdown(full_response)
                    
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                    st.rerun()
                else:
                    error_msg = f"Error: {response.json().get('detail', 'Unknown error')}"
                    with st.chat_message("assistant", avatar="bot_avatar.jpg"):
                        st.error(error_msg)
            except Exception as e:
                with st.chat_message("assistant", avatar="bot_avatar.jpg"):
                    st.error(f"Failed to connect to backend: {e}")
