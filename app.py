"""
Snap & Study AI - Production-Ready Streamlit Educational Application.

A professional visual learning assistant leveraging Google Gemini 2.5 Flash
(Vision + Chat) and Gmail SMTP to help students analyze textbook pages,
handwritten notes, diagrams, and assignment questions with real-time follow-up
dialogue and automated email study summaries.

All responses are powered strictly by the live Google Gemini API and Gmail SMTP.
No preview modes, mock data, or fake responses.
"""

import io
import os
import re
import socket
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Dict, Any, Optional, Tuple, Union

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types
from google.genai.errors import APIError

import prompts

# ==============================================================================
# STREAMLIT PAGE CONFIGURATION & THEME
# ==============================================================================
st.set_page_config(
    page_title="Snap & Study AI | Educational Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Modern Blue + White Academic Theme (ChatGPT style)
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --primary-blue: #1E40AF;
        --royal-blue: #2563EB;
        --soft-blue: #DBEAFE;
        --ice-blue: #EFF6FF;
        --navy-dark: #0F172A;
        --slate-gray: #475569;
        --border-color: #E2E8F0;
        --card-bg: #FFFFFF;
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Container padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 4rem;
        max-width: 1050px;
    }

    /* Academic Header Banner */
    .app-header-box {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #2563EB 100%);
        border-radius: 18px;
        padding: 1.8rem 2rem;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 25px -5px rgba(30, 58, 138, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .app-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: #BFDBFE;
        border: 1px solid rgba(191, 219, 254, 0.25);
        margin-bottom: 0.6rem;
    }

    .app-title {
        font-size: 2.2rem;
        font-weight: 800;
        line-height: 1.2;
        margin-bottom: 0.4rem;
        color: #FFFFFF;
        letter-spacing: -0.02em;
    }

    .app-subtitle {
        font-size: 1.0rem;
        line-height: 1.55;
        color: #E2E8F0;
        max-width: 800px;
        margin: 0;
    }

    /* Sidebar Profile Card */
    .sidebar-profile {
        background: #FFFFFF;
        border: 1px solid #DBEAFE;
        border-radius: 14px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(37, 99, 235, 0.05);
    }

    .sidebar-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748B;
        letter-spacing: 0.04em;
        margin-bottom: 2px;
    }

    .sidebar-value {
        font-size: 0.95rem;
        font-weight: 700;
        color: #0F172A;
        word-break: break-all;
    }

    .sidebar-meta {
        font-size: 0.8rem;
        color: #2563EB;
        font-weight: 500;
        word-break: break-all;
        margin-top: 2px;
    }

    /* Attachment Preview Bar */
    .attachment-bar {
        background: #F8FAFC;
        border: 1px dashed #CBD5E1;
        border-radius: 12px;
        padding: 0.8rem 1rem;
        margin-top: 0.5rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Onboarding Highlights Box */
    .onboarding-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.8rem;
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.04);
    }

    .onboarding-feature {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        margin-bottom: 1.2rem;
    }

    .onboarding-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: #EFF6FF;
        color: #1E40AF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        flex-shrink: 0;
        border: 1px solid #DBEAFE;
    }

    /* Status Pill */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .status-active {
        background: #ECFDF5;
        color: #065F46;
        border: 1px solid #A7F3D0;
    }

    .status-error {
        background: #FEF2F2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ==============================================================================
# SECRETS MANAGEMENT (STRICT: NO HARDCODED KEYS, ONLY ST.SECRETS)
# ==============================================================================
def get_gemini_api_key() -> str:
    """
    Read the Gemini API key strictly from st.secrets['GEMINI_API_KEY'].
    Raises a descriptive exception if missing or unconfigured.
    """
    try:
        if "GEMINI_API_KEY" not in st.secrets:
            raise KeyError("Gemini API key not found. Please configure .streamlit/secrets.toml.")
        key = str(st.secrets["GEMINI_API_KEY"]).strip()
        if not key or key == "YOUR_GEMINI_API_KEY":
            raise ValueError("Gemini API key not found. Please configure .streamlit/secrets.toml.")
        return key
    except Exception as e:
        if isinstance(e, ValueError) and "Gemini API key not found" in str(e):
            raise e
        raise KeyError("Gemini API key not found. Please configure .streamlit/secrets.toml.") from e


def get_gmail_secrets() -> Tuple[str, str]:
    """
    Read GMAIL_ADDRESS and GMAIL_APP_PASSWORD strictly from st.secrets.
    Raises a descriptive exception if missing or unconfigured.
    """
    try:
        if "GMAIL_ADDRESS" not in st.secrets or "GMAIL_APP_PASSWORD" not in st.secrets:
            raise KeyError("Gmail credentials not found. Please configure GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .streamlit/secrets.toml.")
        addr = str(st.secrets["GMAIL_ADDRESS"]).strip()
        pwd = str(st.secrets["GMAIL_APP_PASSWORD"]).strip()
        if not addr or addr == "YOUR_GMAIL_ADDRESS" or not pwd or pwd == "YOUR_GMAIL_APP_PASSWORD":
            raise ValueError("Gmail credentials not configured. Please set GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .streamlit/secrets.toml.")
        return addr, pwd
    except Exception as e:
        if isinstance(e, ValueError) and "Gmail credentials not configured" in str(e):
            raise e
        raise KeyError("Gmail credentials not found. Please configure GMAIL_ADDRESS and GMAIL_APP_PASSWORD in .streamlit/secrets.toml.") from e


def init_gemini_client() -> genai.Client:
    """
    Initialize and return Google GenAI Client with live Gemini API key.
    """
    return get_gemini_client()


def get_gemini_client() -> genai.Client:
    """
    Initialize and return the singleton authenticated Google GenAI Client.
    Uses:
        from google import genai
        client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    Ensures every Gemini request uses the exact same authenticated client.
    """
    if "gemini_client" not in st.session_state or st.session_state.gemini_client is None:
        api_key = get_gemini_api_key()
        st.session_state.gemini_client = genai.Client(api_key=api_key)
    return st.session_state.gemini_client


# ==============================================================================
# GEMINI MODEL CONFIGURATION (CURRENT OFFICIAL PUBLIC MODELS ONLY)
# ==============================================================================
SUPPORTED_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
    "gemini-flash-latest",
]
DEFAULT_MODEL = "gemini-3.5-flash"


# ==============================================================================
# DEBUGGING & DIAGNOSTICS (REQUIREMENT 11 & 12)
# ==============================================================================
def get_debug_info() -> Dict[str, Any]:
    """
    Collect authentication debugging information:
    - SDK version
    - Selected model
    - Whether the API key exists (without printing the key itself)
    - Which authentication method is used
    """
    key_exists = False
    key_preview = "Not configured"
    auth_method = "Google AI Studio API Key (x-goog-api-key)"

    try:
        if "GEMINI_API_KEY" in st.secrets:
            raw_key = str(st.secrets["GEMINI_API_KEY"]).strip()
            if raw_key and raw_key != "YOUR_GEMINI_API_KEY":
                key_exists = True
                prefix = raw_key[:4]
                suffix = raw_key[-4:] if len(raw_key) > 8 else ""
                key_preview = f"{prefix}...{suffix} ({len(raw_key)} chars)"
    except Exception:
        pass

    sdk_ver = getattr(genai, "__version__", "2.27.0")
    model = st.session_state.get("active_model", DEFAULT_MODEL)

    return {
        "sdk_version": sdk_ver,
        "selected_model": model,
        "api_key_configured": key_exists,
        "api_key_preview": key_preview,
        "auth_method": auth_method,
    }


def print_debug_info() -> None:
    """Print debugging information to terminal/console log."""
    if st.session_state.get("_debug_printed"):
        return
    info = get_debug_info()
    print("=" * 60)
    print(" SNAP & STUDY AI - GEMINI AUTHENTICATION DIAGNOSTICS")
    print("=" * 60)
    print(f" - SDK Version:           google-genai v{info['sdk_version']}")
    print(f" - Selected Model:        {info['selected_model']}")
    print(f" - API Key Configured:    {info['api_key_configured']} ({info['api_key_preview']})")
    print(f" - Authentication Method: {info['auth_method']}")
    print("=" * 60)
    st.session_state._debug_printed = True


def test_gemini_connection(model_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Standalone test function that sends 'Hello' to Gemini.
    Returns (success: bool, response_or_error_message: str).
    If it fails, displays the exact reason and clear diagnostics.
    """
    model = model_name or st.session_state.get("active_model", DEFAULT_MODEL)
    try:
        client = get_gemini_client()
        chat = client.chats.create(model=model)
        response = chat.send_message("Hello")
        if response and response.text:
            return True, response.text.strip()
        return True, "Connected successfully, but response text was empty."
    except APIError as api_err:
        return False, f"Gemini API Error: {api_err}"
    except Exception as e:
        return False, f"Gemini Request Failed: {str(e)}"


# Print diagnostic info to terminal once
print_debug_info()


# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================
if "student_name" not in st.session_state:
    st.session_state.student_name = ""

if "email" not in st.session_state:
    st.session_state.email = ""

if "is_onboarded" not in st.session_state:
    st.session_state.is_onboarded = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "gemini_chat" not in st.session_state:
    st.session_state.gemini_chat = None

if "gemini_client" not in st.session_state:
    st.session_state.gemini_client = None

if "active_model" not in st.session_state:
    st.session_state.active_model = DEFAULT_MODEL

if "pending_image" not in st.session_state:
    st.session_state.pending_image = None

if "pending_image_name" not in st.session_state:
    st.session_state.pending_image_name = None

if "last_summary" not in st.session_state:
    st.session_state.last_summary = None


# ==============================================================================
# VALIDATION HELPERS
# ==============================================================================
def validate_name(name: str) -> Tuple[bool, str]:
    """Validate student full name."""
    cleaned = name.strip()
    if not cleaned:
        return False, "Student Name is required."
    if len(cleaned) < 2:
        return False, "Student Name must be at least 2 characters long."
    if len(cleaned) > 80:
        return False, "Student Name cannot exceed 80 characters."
    if not re.match(r"^[A-Za-z\s'\.\-]+$", cleaned):
        return False, "Student Name should contain letters, spaces, hyphens, and apostrophes only."
    return True, ""


def validate_email(email_str: str) -> Tuple[bool, str]:
    """Validate student email address using standard regex."""
    cleaned = email_str.strip()
    if not cleaned:
        return False, "Email Address is required."
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, cleaned):
        return False, "Please enter a valid email address (e.g., student@university.edu)."
    return True, ""


# ==============================================================================
# CORE GEMINI API FUNCTIONS (RESILIENT LIVE API CALLS)
# ==============================================================================
def init_gemini_chat_session(model_name: Optional[str] = None):
    """
    Create a persistent live Gemini chat session with SYSTEM_PROMPT.
    Uses the authenticated client and supported public models with fallback.
    """
    client = get_gemini_client()
    models_to_try = [model_name] if model_name else SUPPORTED_MODELS
    last_err = None

    for m in models_to_try:
        try:
            chat = client.chats.create(
                model=m,
                config=types.GenerateContentConfig(
                    system_instruction=prompts.SYSTEM_PROMPT,
                    temperature=0.2,
                )
            )
            st.session_state.gemini_chat = chat
            st.session_state.active_model = m
            return chat
        except Exception as e:
            last_err = e
            continue

    if last_err:
        raise last_err
    raise RuntimeError("Failed to create Gemini chat session with any supported model.")


def send_gemini_message(contents: Union[str, List[Any]]) -> str:
    """
    Send prompt or multi-modal parts to live Gemini chat session.
    Uses the same authenticated client and handles model fallback if needed.
    """
    client = get_gemini_client()

    # 1. Try active chat session if available
    if st.session_state.gemini_chat is not None:
        try:
            response = st.session_state.gemini_chat.send_message(contents)
            return response.text
        except Exception:
            # Active chat session failed, fall back to creating a fresh session on supported models
            pass

    # 2. Iterate through supported models
    last_error = None
    for m in SUPPORTED_MODELS:
        try:
            chat = client.chats.create(
                model=m,
                config=types.GenerateContentConfig(
                    system_instruction=prompts.SYSTEM_PROMPT,
                    temperature=0.2,
                )
            )
            response = chat.send_message(contents)
            st.session_state.gemini_chat = chat
            st.session_state.active_model = m
            return response.text
        except Exception as err:
            last_error = err
            continue

    if last_error:
        raise last_error
    raise RuntimeError("Failed to obtain response from Gemini API.")


def analyze_with_gemini(image_data: Union[bytes, Image.Image], user_prompt: Optional[str] = None) -> str:
    """
    Reusable function:
    - accepts uploaded image bytes or PIL Image
    - accepts optional user prompt
    - sends both directly to Gemini Vision
    - returns the real Gemini response text
    Raises exception directly on failure.
    """
    # 1. Convert input to image bytes
    if isinstance(image_data, bytes):
        image_bytes = image_data
    elif isinstance(image_data, Image.Image):
        buf = io.BytesIO()
        rgb_img = image_data.convert("RGB") if image_data.mode in ("RGBA", "P") else image_data
        rgb_img.save(buf, format="JPEG", quality=95)
        image_bytes = buf.getvalue()
    elif hasattr(image_data, "getvalue"):
        image_bytes = image_data.getvalue()
    else:
        raise ValueError("Invalid image data provided for Gemini Vision analysis.")

    # 2. Wrap image bytes into GenAI types.Part
    image_part = types.Part.from_bytes(
        data=image_bytes,
        mime_type="image/jpeg"
    )

    # 3. Build structured image analysis prompt
    full_prompt = prompts.get_image_analysis_prompt(user_prompt or "")

    # 4. Send directly to active live Gemini chat session / model
    return send_gemini_message([image_part, full_prompt])


def ask_gemini(prompt: str, image: Optional[Union[bytes, Image.Image]] = None) -> str:
    """
    Query Gemini with text and optional visual input.
    Always uses the real Gemini API.
    Returns the real response or raises an exception.
    """
    if image is not None:
        return analyze_with_gemini(image_data=image, user_prompt=prompt)

    return send_gemini_message(prompt)


# ==============================================================================
# CHAT MANAGEMENT HELPER FUNCTIONS
# ==============================================================================
def add_message(role: str, content: str, image: Optional[Image.Image] = None) -> None:
    """Append a message to session state and conversation history."""
    msg_data = {
        "role": role,
        "content": content,
        "image": image,
        "timestamp": datetime.now().strftime("%I:%M %p"),
    }
    st.session_state.messages.append(msg_data)
    
    text_repr = f"[{msg_data['timestamp']}] {role.capitalize()}: {content}"
    if image is not None:
        text_repr += " [User uploaded an image]"
    st.session_state.conversation_history.append(text_repr)


def render_message(message: Dict[str, Any]) -> None:
    """Render a single chat message with optional image thumbnail."""
    role = message.get("role", "assistant")
    content = message.get("content", "")
    image = message.get("image")

    with st.chat_message(role):
        if image is not None:
            st.image(image, caption="Uploaded Educational Material", use_container_width=True)
        if content:
            st.markdown(content)


def render_chat_history() -> None:
    """Render all messages currently stored in the session history."""
    for msg in st.session_state.messages:
        render_message(msg)


def reset_chat() -> None:
    """Clear message history, re-initialize live Gemini chat, and re-seed welcome message."""
    st.session_state.messages = []
    st.session_state.conversation_history = []
    st.session_state.pending_image = None
    st.session_state.pending_image_name = None
    st.session_state.last_summary = None

    try:
        init_gemini_chat_session()
    except Exception as e:
        st.error(f"❌ Failed to reset Gemini chat: {e}")

    # Re-seed Welcome Message
    welcome_text = prompts.get_welcome_message(st.session_state.student_name)
    add_message(role="assistant", content=welcome_text)
    st.rerun()


# ==============================================================================
# GMAIL SMTP EMAIL DISPATCH (LIVE ONLY, STRICT CREDENTIALS)
# ==============================================================================
def send_email(recipient_email: str, student_name: str, summary_content: str) -> Tuple[bool, str]:
    """
    Send study notes to student email via Gmail SMTP using st.secrets.
    Returns (success_boolean, status_message).
    """
    gmail_address, gmail_app_password = get_gmail_secrets()

    # Validate recipient email
    is_valid, msg = validate_email(recipient_email)
    if not is_valid:
        return False, msg

    date_str = datetime.now().strftime("%B %d, %Y - %I:%M %p")

    # Build Multipart Email
    email_msg = MIMEMultipart("alternative")
    email_msg["Subject"] = f"📚 Snap & Study AI - Study Notes for {student_name}"
    email_msg["From"] = f"Snap & Study AI <{gmail_address}>"
    email_msg["To"] = recipient_email

    # Plain text version
    plain_text = f"""Snap & Study AI - Study Brief
Student Name: {student_name}
Date: {date_str}

==================================================
STUDY NOTES & SUMMARY
==================================================

{summary_content}

==================================================
Generated by Snap & Study AI • Powered by Google Gemini AI
"""

    html_formatted_summary = summary_content.replace("\n", "<br>")

    html_text = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                background-color: #F8FAFC;
                color: #0F172A;
                margin: 0;
                padding: 20px;
            }}
            .email-container {{
                max-width: 650px;
                margin: auto;
                background: #FFFFFF;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
                border: 1px solid #E2E8F0;
            }}
            .header {{
                background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 60%, #2563EB 100%);
                color: #FFFFFF;
                padding: 24px;
                text-align: left;
            }}
            .header h1 {{
                margin: 0;
                font-size: 24px;
                font-weight: 700;
            }}
            .header p {{
                margin: 6px 0 0 0;
                font-size: 14px;
                color: #DBEAFE;
            }}
            .meta-box {{
                background: #EFF6FF;
                border-left: 4px solid #2563EB;
                padding: 12px 18px;
                margin: 20px 24px;
                font-size: 13px;
                color: #1E293B;
            }}
            .content {{
                padding: 0 24px 24px 24px;
                line-height: 1.65;
                font-size: 14px;
                color: #334155;
            }}
            .footer {{
                background: #F1F5F9;
                padding: 14px 24px;
                text-align: center;
                font-size: 12px;
                color: #64748B;
                border-top: 1px solid #E2E8F0;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>📚 Snap & Study AI</h1>
                <p>Personalized Study Brief & Revision Notes</p>
            </div>
            <div class="meta-box">
                <strong>Student:</strong> {student_name}<br>
                <strong>Email:</strong> {recipient_email}<br>
                <strong>Generated On:</strong> {date_str}
            </div>
            <div class="content">
                <h3>📖 Study Session Summary</h3>
                <div>{html_formatted_summary}</div>
            </div>
            <div class="footer">
                Snap & Study AI • Powered by Google Gemini Live API • Keep learning!
            </div>
        </div>
    </body>
    </html>
    """

    email_msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    email_msg.attach(MIMEText(html_text, "html", "utf-8"))

    # Connect to Gmail SMTP (Port 587 with STARTTLS)
    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(gmail_address, gmail_app_password)
            server.sendmail(gmail_address, recipient_email, email_msg.as_string())
        return True, f"Study notes successfully sent to {recipient_email}!"

    except smtplib.SMTPAuthenticationError:
        return (
            False,
            "Gmail Authentication Failed. Please verify that you are using a 16-character 'Google App Password', not your regular password."
        )
    except (socket.gaierror, socket.timeout):
        return False, "Network Connection Timeout. Could not reach smtp.gmail.com. Please check your internet connection."
    except Exception as e:
        return False, f"Failed to send email via SMTP: {str(e)}"


# ==============================================================================
# ONBOARDING SCREEN
# ==============================================================================
def render_onboarding_page():
    """Display the student onboarding view when the app opens for the first time."""
    # Check if Gemini API key exists in secrets before proceeding
    try:
        get_gemini_api_key()
    except Exception:
        st.error("Gemini API key not found. Please configure .streamlit/secrets.toml.")

    st.markdown("""
        <div class="app-header-box">
            <div class="app-badge">
                <span>🎓</span>
                <span>Student Onboarding</span>
            </div>
            <h1 class="app-title">📚 Snap & Study AI</h1>
            <p class="app-subtitle">
                Upload notes, textbook pages, handwritten notes, diagrams or assignment questions and learn with AI.
            </p>
        </div>
    """, unsafe_allow_html=True)

    col_info, col_form = st.columns([1.1, 1.2], gap="large")

    with col_info:
        st.markdown("### 🌟 Start Your Study Journey")
        st.markdown("""
            <div class="onboarding-feature">
                <div class="onboarding-icon">🤖</div>
                <div>
                    <strong style="color:#0F172A; font-size:0.95rem;">Powered by Google Gemini AI</strong>
                    <p style="color:#64748B; font-size:0.85rem; margin:2px 0 0 0;">
                        Live Google Gemini vision & reasoning explains dense textbook chapters and diagrams in plain language.
                    </p>
                </div>
            </div>
            <div class="onboarding-feature">
                <div class="onboarding-icon">📸</div>
                <div>
                    <strong style="color:#0F172A; font-size:0.95rem;">Multi-Modal Visual Study</strong>
                    <p style="color:#64748B; font-size:0.85rem; margin:2px 0 0 0;">
                        Snap textbook pages, handwritten notes, formulas, or homework diagrams directly in the chat.
                    </p>
                </div>
            </div>
            <div class="onboarding-feature">
                <div class="onboarding-icon">💬</div>
                <div>
                    <strong style="color:#0F172A; font-size:0.95rem;">Interactive ChatGPT-Style Tutor</strong>
                    <p style="color:#64748B; font-size:0.85rem; margin:2px 0 0 0;">
                        Ask unlimited follow-up questions. Your AI tutor remembers previous context throughout the session.
                    </p>
                </div>
            </div>
            <div class="onboarding-feature">
                <div class="onboarding-icon">📧</div>
                <div>
                    <strong style="color:#0F172A; font-size:0.95rem;">Direct-to-Inbox Summaries</strong>
                    <p style="color:#64748B; font-size:0.85rem; margin:2px 0 0 0;">
                        When done, 1-click compiles your questions and formulas into structured study notes sent to your email.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_form:
        with st.container(border=True):
            st.markdown("""
                <div style="margin-bottom:1rem;">
                    <span style="background:#EFF6FF; color:#1E40AF; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:99px; text-transform:uppercase;">
                        Get Started
                    </span>
                    <h3 style="margin:8px 0 2px 0; font-size:1.3rem; font-weight:800; color:#0F172A;">Student Profile</h3>
                    <p style="color:#64748B; font-size:0.85rem; margin:0;">
                        Please provide your name and student email to initialize your study room.
                    </p>
                </div>
            """, unsafe_allow_html=True)

            with st.form("onboarding_form", clear_on_submit=False):
                name_input = st.text_input(
                    "Student Name *",
                    value=st.session_state.student_name,
                    placeholder="e.g. Alex Johnson",
                    help="Your full name will be used to personalize tutor responses and study briefs."
                )

                email_input = st.text_input(
                    "Email Address *",
                    value=st.session_state.email,
                    placeholder="e.g. alex.johnson@university.edu",
                    help="Your AI-generated study summaries will be emailed to this address."
                )

                st.markdown("<br>", unsafe_allow_html=True)

                submit_btn = st.form_submit_button(
                    "🚀 Enter Snap & Study AI",
                    type="primary",
                    use_container_width=True
                )

                if submit_btn:
                    is_name_ok, name_err = validate_name(name_input)
                    is_email_ok, email_err = validate_email(email_input)

                    if not is_name_ok:
                        st.error(f"⚠️ {name_err}")
                    elif not is_email_ok:
                        st.error(f"⚠️ {email_err}")
                    else:
                        # Verify API key before completing onboarding
                        try:
                            get_gemini_api_key()
                        except Exception as err:
                            st.error(f"⚠️ {err}")
                            st.stop()

                        # Store in session state
                        st.session_state.student_name = name_input.strip()
                        st.session_state.email = email_input.strip()

                        # Initialize live Gemini Chat Session
                        try:
                            init_gemini_chat_session()
                            st.session_state.is_onboarded = True
                        except Exception as e:
                            err_str = str(e)
                            st.error(f"❌ Failed to connect to Gemini API: {err_str}")
                            if "ACCESS_TOKEN_TYPE_UNSUPPORTED" in err_str or "UNAUTHENTICATED" in err_str:
                                st.warning("""
                                **Authentication Issue Detected:**
                                Google's API rejected the key with `401 ACCESS_TOKEN_TYPE_UNSUPPORTED`.
                                
                                **How to fix:**
                                1. Open [Google AI Studio](https://aistudio.google.com/app/apikey) and generate a new Gemini API key.
                                2. Copy the key and paste it into `.streamlit/secrets.toml` as:
                                   `GEMINI_API_KEY = "AIzaSy..."`
                                3. If using a Google Cloud project key, make sure the **Generative Language API** (`generativelanguage.googleapis.com`) is enabled for your project and the key has no restrictive API constraints.
                                """)
                            st.stop()

                        # Seed Welcome Message (displayed once)
                        welcome_content = prompts.get_welcome_message(st.session_state.student_name)
                        add_message(role="assistant", content=welcome_content)

                        # Redirect automatically to the chat page
                        st.rerun()

    # Footer
    st.markdown("<br><hr style='border:none; border-top:1px solid #E2E8F0; margin:2rem 0;'>", unsafe_allow_html=True)
    st.markdown("""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; font-size:0.8rem; color:#64748B;">
            <div><strong>Snap & Study AI</strong> • Built with Streamlit & Google Gemini AI</div>
            <div>Academic Blue Edition</div>
        </div>
    """, unsafe_allow_html=True)

    st.stop()


# If student is not yet onboarded, show onboarding page and stop
if not st.session_state.is_onboarded:
    render_onboarding_page()


# ==============================================================================
# MAIN CHAT PAGE: SIDEBAR
# ==============================================================================
with st.sidebar:
    st.markdown("""
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:1rem;">
            <div style="background:#1E40AF; border-radius:12px; width:40px; height:40px; display:flex; align-items:center; justify-content:center; color:white; font-size:1.3rem;">
                📚
            </div>
            <div>
                <h3 style="margin:0; font-size:1.15rem; font-weight:800; color:#0F172A; line-height:1.1;">Snap & Study AI</h3>
                <span style="font-size:0.75rem; color:#64748B; font-weight:500;">Gemini Live AI Vision Tutor</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Student Profile Card
    conversation_count = len([m for m in st.session_state.messages if m["role"] == "user"])
    st.markdown(f"""
        <div class="sidebar-profile">
            <div class="sidebar-label">Student Name</div>
            <div class="sidebar-value">👤 {st.session_state.student_name}</div>
            <div class="sidebar-label" style="margin-top:6px;">Registered Email</div>
            <div class="sidebar-meta">✉️ {st.session_state.email}</div>
            <div class="sidebar-label" style="margin-top:6px;">Conversation Count</div>
            <div style="font-size:0.85rem; font-weight:700; color:#0F172A;">💬 {conversation_count} message(s) sent</div>
        </div>
    """, unsafe_allow_html=True)

    # API / Service Status Badge
    try:
        get_gemini_api_key()
        active_label = st.session_state.get("active_model", DEFAULT_MODEL)
        disp_model = active_label.replace("-", " ").title()
        gemini_status_html = f'<div class="status-pill status-active"><span>●</span> <span>Gemini: Active ({disp_model})</span></div>'
    except Exception:
        gemini_status_html = '<div class="status-pill status-error"><span>●</span> <span>Gemini: Key Missing</span></div>'

    try:
        get_gmail_secrets()
        smtp_status_html = '<div class="status-pill status-active"><span>●</span> <span>Gmail SMTP: Configured</span></div>'
    except Exception:
        smtp_status_html = '<div class="status-pill status-error"><span>●</span> <span>Gmail SMTP: Missing</span></div>'

    st.markdown(f"""
        <div style="display:flex; flex-direction:column; gap:6px; margin-bottom:1.2rem;">
            {gemini_status_html}
            {smtp_status_html}
        </div>
    """, unsafe_allow_html=True)

    # Standalone Diagnostics & Connection Test Expander
    with st.expander("🛠️ Diagnostics & Connection Test", expanded=False):
        debug_info = get_debug_info()
        st.markdown(f"**SDK:** `google-genai v{debug_info['sdk_version']}`")
        st.markdown(f"**Model:** `{debug_info['selected_model']}`")
        st.markdown(f"**API Key:** `{debug_info['api_key_preview']}`")
        st.markdown(f"**Auth Method:** `{debug_info['auth_method']}`")

        if st.button("🧪 Test Gemini Connection ('Hello')", key="sidebar_test_btn", use_container_width=True):
            with st.spinner("Testing Gemini connection with 'Hello'..."):
                ok, res_text = test_gemini_connection()
                if ok:
                    st.success(f"✅ Success! Response:\n\n{res_text}")
                else:
                    st.error(f"❌ Connection Failed:\n\n{res_text}")
                    if "ACCESS_TOKEN_TYPE_UNSUPPORTED" in res_text or "UNAUTHENTICATED" in res_text:
                        st.info("💡 **Resolution:** Generate an unrestricted API key at https://aistudio.google.com/app/apikey and save it in `.streamlit/secrets.toml`.")

    # SEND STUDY NOTES ACTION BUTTON
    st.markdown("### 📬 Session Summary")
    if st.button("📧 Send Study Notes", type="primary", use_container_width=True, help="Generate AI summary of the conversation and email to your address"):
        user_msgs = [m for m in st.session_state.messages if m["role"] == "user"]
        if not user_msgs:
            st.warning("⚠️ No study questions recorded yet! Ask a question or upload study material first.")
        else:
            with st.spinner("🤖 Gemini is synthesizing your study notes..."):
                summary_prompt = (
                    prompts.SUMMARY_REQUEST_PROMPT + "\n\n"
                    "Here is the dialogue history of this study session:\n" +
                    "\n".join(st.session_state.conversation_history)
                )

                try:
                    if st.session_state.gemini_chat:
                        summary_res = st.session_state.gemini_chat.send_message(summary_prompt)
                        summary_content = summary_res.text
                    else:
                        summary_content = ask_gemini(summary_prompt)
                    st.session_state.last_summary = summary_content
                except Exception as e:
                    st.error(f"❌ Failed to generate summary from Gemini: {e}")
                    summary_content = None

            if summary_content:
                with st.spinner("✉️ Dispatching study brief to your registered email..."):
                    try:
                        success, msg = send_email(
                            recipient_email=st.session_state.email,
                            student_name=st.session_state.student_name,
                            summary_content=summary_content
                        )
                        if success:
                            st.success(f"✅ {msg}")
                            st.balloons()
                        else:
                            st.error(f"❌ {msg}")
                    except Exception as err:
                        st.error(f"❌ Email sending error: {err}")

    # RESET CHAT BUTTON
    st.markdown("---")
    col_reset1, col_reset2 = st.columns(2)
    with col_reset1:
        if st.button("🔄 Reset Chat", use_container_width=True, help="Clear message history and start a fresh chat"):
            reset_chat()

    with col_reset2:
        if st.button("🚪 Logout", use_container_width=True, help="Exit session and return to onboarding"):
            st.session_state.is_onboarded = False
            st.session_state.student_name = ""
            st.session_state.email = ""
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.session_state.gemini_chat = None
            st.session_state.pending_image = None
            st.rerun()

    # ABOUT SNAP & STUDY
    st.markdown("---")
    with st.expander("ℹ️ About Snap & Study AI"):
        st.markdown("""
            **Snap & Study AI** is an intelligent visual learning companion.
            
            - **Model**: Google Gemini Live Vision + Chat API (Multi-Model Resilient)
            - **Formats**: JPG, JPEG, PNG, WEBP
            - **Capabilities**:
              - Transcribing handwritten notes
              - Deciphering scientific & math formulas
              - Breaking down biological/engineering diagrams
              - Step-by-step assignment problem solving
            - **Security**: Strictly uses `.streamlit/secrets.toml`. Passwords & API keys are never hardcoded.
        """)

    st.markdown("""
        <div style="text-align:center; padding-top:1rem; font-size:0.75rem; color:#94A3B8;">
            Snap & Study AI • Academic Blue Edition<br>
            Designed for curious learners 💡
        </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# MAIN CHAT PAGE: HEADER
# ==============================================================================
st.markdown("""
    <div class="app-header-box">
        <h1 class="app-title">📚 Snap & Study AI</h1>
        <p class="app-subtitle">
            Upload notes, textbook pages, handwritten notes, diagrams or assignment questions and learn with AI.
        </p>
    </div>
""", unsafe_allow_html=True)


# ==============================================================================
# MAIN CHAT PAGE: CONVERSATION HISTORY DISPLAY
# ==============================================================================
render_chat_history()


# ==============================================================================
# CHAT INPUT & ATTACHMENT SECTION (TEXT, IMAGE, OR IMAGE + TEXT)
# ==============================================================================
# Attachment Bar / Expander for Images
with st.expander("📎 Attach Study Material Image (Textbook, Notes, Diagram, Assignment)", expanded=(st.session_state.pending_image is not None)):
    file_col, preview_col = st.columns([1.5, 1])

    with file_col:
        uploaded_img_file = st.file_uploader(
            "Upload image (JPG, JPEG, PNG, WEBP):",
            type=["jpg", "jpeg", "png", "webp"],
            key="chat_image_uploader",
            help="High-contrast, well-lit photos work best for handwritten notes and scientific diagrams."
        )

        if uploaded_img_file is not None:
            try:
                pil_img = Image.open(uploaded_img_file)
                st.session_state.pending_image = pil_img
                st.session_state.pending_image_name = uploaded_img_file.name
            except Exception as e:
                st.error(f"⚠️ Error reading image file: {e}")

    with preview_col:
        if st.session_state.pending_image is not None:
            st.markdown(f"**Selected:** `{st.session_state.pending_image_name}`")
            st.image(st.session_state.pending_image, width=180)
            if st.button("❌ Remove Attachment", key="remove_img_btn"):
                st.session_state.pending_image = None
                st.session_state.pending_image_name = None
                st.rerun()
        else:
            st.caption("No image attached. You can send text-only, attach an image, or send image + text together.")

# Primary Chat Input
prompt_input = st.chat_input(
    f"Ask a question or explain attached material, {st.session_state.student_name}..."
)

# Immediate "Send Attached Image" button if image is attached without typed text
if st.session_state.pending_image is not None and not prompt_input:
    send_img_col1, send_img_col2 = st.columns([1.2, 3])
    with send_img_col1:
        if st.button("📤 Send Image for Analysis", type="primary", use_container_width=True):
            prompt_input = "Please analyze this uploaded study material in detail and explain the core concepts."

if prompt_input:
    current_image = st.session_state.pending_image
    current_image_name = st.session_state.pending_image_name

    # Reset pending attachment
    st.session_state.pending_image = None
    st.session_state.pending_image_name = None

    # 1. Add user message to state and UI
    add_message(role="user", content=prompt_input, image=current_image)
    
    with st.chat_message("user"):
        if current_image is not None:
            st.image(current_image, caption=f"Material: {current_image_name}", use_container_width=True)
        st.markdown(prompt_input)

    # 2. Call live Gemini Vision / Chat API (no mock responses)
    with st.chat_message("assistant"):
        with st.spinner("🤖 Gemini is reviewing your study material..."):
            try:
                ai_reply = ask_gemini(prompt=prompt_input, image=current_image)
                st.markdown(ai_reply)
                # 3. Save assistant response
                add_message(role="assistant", content=ai_reply)
                st.rerun()
            except (KeyError, ValueError) as err:
                st.error(f"⚠️ {err}")
            except APIError as api_err:
                st.error(f"❌ Gemini API Error: {api_err}")
            except Exception as e:
                st.error(f"❌ Gemini Request Failed: {e}")


# ==============================================================================
# EMAIL SUMMARY PREVIEW MODAL / DRAWER (IF GENERATED)
# ==============================================================================
if st.session_state.last_summary:
    with st.expander("📄 View Latest Generated Study Summary", expanded=False):
        st.markdown(st.session_state.last_summary)
        st.download_button(
            label="📥 Download Study Notes (.md)",
            data=st.session_state.last_summary,
            file_name=f"Study_Notes_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True
        )
