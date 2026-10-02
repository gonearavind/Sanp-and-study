# 📚 Snap & Study AI

> **A professional, AI-powered visual study assistant built with Python, Streamlit, and Google Gemini 2.5 Flash (Vision + Chat).**  
> Students can upload textbook pages, handwritten lecture notes, scientific diagrams, and assignment questions. Gemini explains the content in simple language, engages in unlimited follow-up discussions, and delivers an AI-generated study summary directly to the student's email inbox via Gmail SMTP.

---

## 🌟 Objective & Workflow

Snap & Study AI simplifies academic learning into a seamless 6-step workflow:

```
[Onboarding] ➡️ [Welcome & Chat] ➡️ [Image Analysis] ➡️ [Follow-up Q&A] ➡️ [AI Summary] ➡️ [Email Delivery]
```

1. **Onboarding**: The student registers their **Name** and **Email Address** once. Input fields are strictly validated and stored in `st.session_state`.
2. **Welcome & Chat**: The student enters a ChatGPT-style conversation interface with a personalized welcome greeting.
3. **Image Analysis**: The student attaches a photo or scan of their textbook, handwritten notes, or diagram. Gemini 2.5 Flash reads, extracts, and explains the material step-by-step.
4. **Follow-up Q&A**: The student can ask unlimited questions. Gemini retains conversational context across multi-turn exchanges.
5. **AI Summary**: At the end of revision, clicking **"📧 Send Study Notes"** prompts Gemini to synthesize the entire conversation into a clean, exam-ready study guide.
6. **Email Delivery**: The application formats the study brief into clean Markdown & HTML and dispatches it directly to the student's email via Gmail SMTP.

---

## 🛠️ Tech Stack

- **Frontend / Framework**: [Streamlit](https://streamlit.io/) (1.35.0+)
- **Multimodal AI**: Google Gemini 2.5 Flash (`google-genai` SDK)
- **Email Protocol**: Gmail SMTP (`smtplib` + `email.mime` with TLS encryption)
- **State Management**: Streamlit Session State (`st.session_state`)
- **Secrets Management**: Streamlit Secrets (`st.secrets`)
- **Image Processing**: Pillow (`PIL`)

---

## 📁 Project Structure

```plaintext
snap-study/
│
├── app.py                     # Main Streamlit application and ChatGPT-style interface
├── prompts.py                 # System prompt, welcome template, & summary generator
├── requirements.txt           # Production dependencies
├── README.md                  # Comprehensive setup and deployment documentation
├── .gitignore                 # Excludes secrets.toml, virtual environments, and cache
│
└── .streamlit/
      ├── config.toml          # Academic Blue theme & server configuration
      └── secrets.toml.example # Secrets template for Gemini API key & Gmail SMTP
```

---

## 🚀 Quickstart & Local Installation

### 1. Prerequisites
- **Python 3.10+** (Python 3.10, 3.11, 3.12, 3.13, 3.14 supported)
- A free [Google AI Studio API Key](https://aistudio.google.com/app/apikey)
- A Gmail account with a 16-character [App Password](https://myaccount.google.com/apppasswords)

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/snap-study.git
cd snap-study
```

### 3. Create a Virtual Environment
```bash
# Windows
py -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Local Secrets
Copy the secrets template:
```bash
# Windows (PowerShell)
Copy-Item .streamlit/secrets.toml.example .streamlit/secrets.toml

# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Open `.streamlit/secrets.toml` in your editor and provide your credentials:
```toml
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
GMAIL_ADDRESS="YOUR_GMAIL_ADDRESS"
GMAIL_APP_PASSWORD="YOUR_GMAIL_APP_PASSWORD"
```

### 6. Test Gemini Authentication (Optional but Recommended)
Test your API key and connection directly:
```bash
# Windows
py test_gemini.py

# macOS / Linux
python3 test_gemini.py
```

### 7. Run the Application
```bash
streamlit run app.py
```
Or with the Windows Python launcher:
```bash
py -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## ☁️ Deployment on Streamlit Community Cloud

Snap & Study AI is built for 1-click deployment on **Streamlit Community Cloud**:

1. **Push to GitHub**:
   - Commit your code (`app.py`, `prompts.py`, `requirements.txt`, `.gitignore`, `README.md`, `.streamlit/config.toml`, `.streamlit/secrets.toml.example`).
   - Push to your GitHub repository.
2. **Deploy on Streamlit Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/) and log in with GitHub.
   - Click **"New app"**.
   - Select your repository, branch (`main`), and set the main file path to `app.py`.
3. **Configure Secrets in Streamlit Cloud**:
   - Click **"Advanced settings..."** (or go to App Settings ➡️ Secrets).
   - Paste the contents of your `secrets.toml`:
     ```toml
     GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"
     GMAIL_ADDRESS = "YOUR_GMAIL_ADDRESS"
     GMAIL_APP_PASSWORD = "YOUR_GMAIL_APP_PASSWORD"
     ```
   - Click **"Save"**.
4. **Deploy**:
   - Click **"Deploy!"**. Your live application will be available at a custom URL (e.g., `https://snap-study-ai.streamlit.app`).

---

## 🔒 Gmail App Password Setup Guide

Standard Gmail account passwords cannot be used with SMTP due to Google's security standards. To generate an App Password:

1. Go to your [Google Account Security Settings](https://myaccount.google.com/security).
2. Enable **2-Step Verification** if not already enabled.
3. In the security search bar, search for **"App passwords"** (or visit [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Enter an app name (e.g. `SnapStudyAI`) and click **Create**.
5. Copy the generated **16-character code** (format: `xxxx xxxx xxxx xxxx`) into `GMAIL_APP_PASSWORD`.

---

## 🎯 Architecture & Helper Functions

The codebase adheres strictly to functional separation and clean modular architecture:

| Function | Responsibility |
| :--- | :--- |
| `render_message(message)` | Renders user/assistant messages with optional image thumbnails inside chat bubbles. |
| `add_message(role, content, image)` | Appends incoming messages to state memory and conversation history strings. |
| `render_chat_history()` | Iterates through `st.session_state.messages` to render the multi-turn discussion. |
| `ask_gemini(prompt, image)` | Connects to Gemini 2.5 Flash, formats multimodal inputs (`types.Part`), and queries the model. |
| `send_email(to, name, summary)` | Establishes an encrypted TLS connection to `smtp.gmail.com:587` and delivers HTML + Plain Text briefs. |
| `reset_chat()` | Wipes message memory, creates a fresh Gemini chat session, and re-seeds the welcome greeting. |

---

## 🛡️ Error Handling & Resilience

- **Invalid Input**: Form validation prevents empty names, malformed emails, and blank submissions.
- **Image Safeguards**: Catches corrupt files and checks for clarity. If blurry or unreadable, Gemini prompts the student for a clearer picture.
- **API Outages**: Gracefully catches `google.genai.errors.APIError` and network timeouts without crashing the UI.
- **SMTP Authentication**: Validates Google App Passwords and displays actionable error messages if authentication fails.
- **Missing Secrets**: Shows clear Streamlit error if API key or SMTP secrets are unconfigured. No mock or fallback responses.
- **Diagnostics**: Includes standalone diagnostic test script `test_gemini.py` and in-app diagnostics panel.

---

## 📄 License

MIT License. Designed with ❤️ for students and educators worldwide.
