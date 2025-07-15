import streamlit as st
import os, whisper, sounddevice as sd, numpy as np
from datetime import datetime
import requests, wikipedia, tempfile, time, pygame
from langdetect import detect
from gtts import gTTS
import google.generativeai as genai
from translate import Translator
import subprocess
import webbrowser
import math
import re
from fpdf import FPDF
import scipy.io.wavfile as wav

# --- Constants ---
RECORDING_DURATION = 5
SAMPLE_RATE = 16000
DEFAULT_LANGUAGE = 'en'

# --- Gemini API Setup ---
GEMINI_API_KEY = "AIzaSyBGzLZFa0NkzSqrC7mymT2Nui5XpdWsnt8"  # Replace with your actual API key
if not GEMINI_API_KEY:
    st.error("❌ Please enter your Gemini API key in the code (replace the placeholder)")
    st.stop()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-1.5-flash")
    model = whisper.load_model("base")
    pygame.init()
except Exception as e:
    st.error(f"Error loading models: {e}")
    st.stop()

SUPPORTED_LANGUAGES = ['en','hi','mr','gu','ta','te','kn','bn','ur','ml','pa','or','as']
LANGUAGE_MAP = {
    "en": "English", "hi": "Hindi", "mr": "Marathi", "gu": "Gujarati",
    "ta": "Tamil", "te": "Telugu", "kn": "Kannada", "bn": "Bengali",
    "ur": "Urdu", "ml": "Malayalam", "pa": "Punjabi", "or": "Odia", "as": "Assamese",
}

# --- Application Functions ---
def open_application(app_name):
    """Open applications based on name with fallback to web search"""
    app_commands = {
        'notepad': 'notepad.exe', 'calculator': 'calc.exe', 'paint': 'mspaint.exe',
        'chrome': 'chrome.exe', 'firefox': 'firefox.exe', 'word': 'winword.exe',
        'excel': 'excel.exe', 'powerpoint': 'powerpnt.exe', 'cmd': 'cmd.exe',
        'control panel': 'control.exe', 'task manager': 'taskmgr.exe',
        'file explorer': 'explorer.exe', 'spotify': 'spotify.exe'
    }
    
    app_name_lower = app_name.lower()
    
    # Try to open the application
    if app_name_lower in app_commands:
        try:
            subprocess.Popen(app_commands[app_name_lower])
            return f"✅ Opening {app_name}..."
        except Exception as e:
            # If local app fails, try web search
            try:
                search_url = f"https://www.google.com/search?q={app_name.replace(' ', '+')}+download"
                webbrowser.open(search_url)
                return f"🔍 Couldn't find {app_name} locally. Opening download options in browser..."
            except Exception as web_err:
                return f"❌ Could not open {app_name} or find download options. Error: {str(e)}"
    else:
        # For apps not in our list, try web search directly
        try:
            search_url = f"https://www.google.com/search?q={app_name.replace(' ', '+')}+download"
            webbrowser.open(search_url)
            return f"🔍 {app_name} not in my app list. Opening download options in browser..."
        except Exception as e:
            return f"❌ Could not find download options for {app_name}. Error: {str(e)}"

def perform_calculation(expression):
    """Perform mathematical calculations"""
    try:
        # Replace common words with operators
        expression = expression.replace('plus', '+').replace('add', '+')
        expression = expression.replace('minus', '-').replace('subtract', '-')
        expression = expression.replace('multiply', '*').replace('times', '*')
        expression = expression.replace('divide', '/').replace('divided by', '/')
        
        # Remove non-mathematical characters except operators and numbers
        expression = re.sub(r'[^0-9+\-*/().\s]', '', expression)
        
        # Evaluate the expression
        result = eval(expression)
        return f"🧮 The result is: {result}"
    except Exception as e:
        return f"❌ Could not calculate. Please check your expression."

def search_and_order_flipkart(product):
    """Search for products on Flipkart"""
    try:
        search_url = f"https://www.flipkart.com/search?q={product.replace(' ', '%20')}"
        webbrowser.open(search_url)
        return f"🛒 Opening Flipkart search for '{product}'. You can complete the order from the browser."
    except Exception as e:
        return f"❌ Could not open Flipkart search. Error: {str(e)}"
    
def get_website_url(app_name):
    """Generate website URL from app name"""
    app_name = app_name.lower().strip()
    
    # Special cases (common exceptions)
    special_cases = {
        'amazon': 'amazon.in',
        'youtube': 'youtube.com',
        'facebook': 'facebook.com',
        'instagram': 'instagram.com',
        'twitter': 'x.com',  # Twitter's new domain
        'whatsapp': 'web.whatsapp.com',
        'gmail': 'mail.google.com',
        'netflix': 'netflix.com',
        'prime': 'primevideo.com',
        'hotstar': 'hotstar.com'
    }
    
    # Try special cases first
    if app_name in special_cases:
        return f"https://www.{special_cases[app_name]}"
    
    # Generic pattern for most sites
    return f"https://www.{app_name}.com"

def process_command(text):
    """Process commands with single, definitive actions"""
    text_lower = text.lower().strip()
    
    # 1. Extract the target name
    match = re.search(r'open\s+(.+)', text_lower)
    if not match:
        return "❌ Please specify what to open"
    
    target = match.group(1).strip()
    target_lower = target.lower()
    
    # 2. Predefined official sites (add more as needed)
    OFFICIAL_SITES = {
        'flipkart': 'https://www.flipkart.com',
        'amazon': 'https://www.amazon.in',
        'youtube': 'https://www.youtube.com',
        'whatsapp': 'https://web.whatsapp.com',
        'gmail': 'https://mail.google.com',
        'netflix': 'https://www.netflix.com',
        'prime': 'https://www.primevideo.com'
    }
    
    # 3. Check for exact website matches first
    for site_name, url in OFFICIAL_SITES.items():
        if site_name in target_lower:
            webbrowser.open(url)
            return f"🌐 Opening {site_name.capitalize()}'s official site"
    
    # 4. Try local applications
    app_result = open_application(target)
    if "Opening" in app_result:
        return app_result
    
    # 5. Final decision - website or search
    if '.' in target:  # If user specified a domain
        webbrowser.open(f"https://{target}")
        return f"🌐 Opening {target}"
    else:
        webbrowser.open(f"https://www.google.com/search?q={target}")
        return f"🔍 Searching for {target}"
            
    
    # ... [rest of your existing code] ...
    
    # ... [rest of your existing code] ...
    
    # ... [rest of your existing code] ...
    
    # 2. Existing application opening logic
    if "open" in text_lower:
        app_match = re.search(r'open\s+(\w+(?:\s+\w+)*)', text_lower)
        if app_match:
            app_name = app_match.group(1)
            if app_name.lower() != "flipkart":  # Avoid conflict
                return open_application(app_name)
    
    # ... [rest of your existing code remains unchanged] ...
    
    # Check for calculation commands
    if any(word in text_lower for word in ['calculate', 'compute', 'math', 'add', 'subtract', 'multiply', 'divide', 'plus', 'minus', 'times']):
        calc_match = re.search(r'calculate\s+(.+)', text_lower)
        if calc_match:
            expression = calc_match.group(1)
            return perform_calculation(expression)
        else:
            # Try to find mathematical patterns
            math_pattern = r'[\d+\-*/().\s]+'
            if re.search(math_pattern, text):
                return perform_calculation(text)
    
    # Check for Flipkart ordering commands
    if any(word in text_lower for word in ['order', 'buy', 'purchase', 'flipkart']):
        if 'from flipkart' in text_lower or 'on flipkart' in text_lower:
            product_match = re.search(r'(?:order|buy|purchase)\s+(.+?)(?:\s+from\s+flipkart|\s+on\s+flipkart)', text_lower)
            if product_match:
                product = product_match.group(1)
                return search_and_order_flipkart(product)
        elif 'flipkart' in text_lower:
            product_match = re.search(r'flipkart\s+(.+)', text_lower)
            if product_match:
                product = product_match.group(1)
                return search_and_order_flipkart(product)
    
    return None

def record_voice():
    """Record voice input"""
    try:
        with st.spinner("🎤 Recording... Speak now (5 seconds)"):
            audio_data = sd.rec(int(RECORDING_DURATION * SAMPLE_RATE), 
                              samplerate=SAMPLE_RATE, channels=1, dtype='int16')
            sd.wait()
            
            # Create temporary file path
            temp_path = os.path.join(tempfile.gettempdir(), f"temp_recording_{time.time()}.wav")
            
            # Write WAV file
            wav.write(temp_path, SAMPLE_RATE, audio_data)
            
            # Transcribe
            result = model.transcribe(temp_path)
            transcribed_text = result["text"]
            
            # Clean up with retry mechanism
            try:
                os.unlink(temp_path)
            except PermissionError:
                time.sleep(0.1)
                try:
                    os.unlink(temp_path)
                except:
                    pass  # Final attempt failed, but we'll continue
                
            return transcribed_text
    except Exception as e:
        st.error(f"Recording error: {str(e)}")
        return ""

# --- REST OF YOUR CODE REMAINS EXACTLY THE SAME ---

def chat_reply(text, lang):
    """Generate chat reply with command processing"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.chat_history.append((timestamp, "You", text))
    
    # First check if it's a special command
    command_result = process_command(text)
    if command_result:
        answer = command_result
    else:
        # Regular AI response
        try:
            prompt = f"Answer in {LANGUAGE_MAP.get(lang, 'English')}: {text}"
            answer = gemini_model.generate_content(prompt).text.strip()
        except Exception as e:
            answer = f"❌ Sorry, I couldn't generate a reply. Error: {str(e)}"
    
    st.session_state.chat_history.append((timestamp, "Zeno", answer))
    
    # Text-to-speech
    try:
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
        
        tts_text = answer
        if lang != 'en':
            translator = Translator(to_lang=lang)
            tts_text = translator.translate(answer)
        
        tts = gTTS(text=tts_text, lang=lang)
        audio_path = os.path.join(tempfile.gettempdir(), f"tts_{time.time()}.mp3")
        tts.save(audio_path)
        
        pygame.mixer.music.load(audio_path)
        pygame.mixer.music.play()
        
    except Exception as e:
        st.warning(f"TTS Error: {str(e)}")

# --- UI Setup ---
st.set_page_config(page_title="Zeno Assistant", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for modern UI
st.markdown("""
    <style>
    /* Main app styling */
    .stApp {
        background-color: #f5f5f5;
        color: #333;
    }
    
    /* Chat container */
    .chat-container {
        max-height: 65vh;
        overflow-y: auto;
        padding: 20px;
        margin-bottom: 80px;
        border-radius: 15px;
        background-color: white;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Message bubbles */
    .user-message {
        background-color: #e3f2fd;
        padding: 12px 16px;
        border-radius: 18px 18px 0 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    .bot-message {
        background-color: #f1f1f1;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 0;
        margin: 8px 0;
        max-width: 80%;
        margin-right: auto;
        box-shadow: 0 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Timestamps */
    .timestamp {
        font-size: 0.75em;
        color: #666;
        margin-bottom: 4px;
    }
    
    /* Input area */
    .input-container {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        padding: 15px;
        background-color: white;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
        z-index: 100;
        display: flex;
        gap: 10px;
        align-items: center;
    }
    
    /* Input field */
    .stTextInput>div>div>input {
        border-radius: 25px;
        padding: 12px 20px;
        border: 1px solid #ddd;
        font-size: 16px;
    }
    
    /* Buttons */
    .stButton>button {
        border-radius: 50%;
        width: 50px;
        height: 50px;
        padding: 0;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
    }
    
    .send-button {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    
    .voice-button {
        background-color: #2196F3 !important;
        color: white !important;
    }
    
    .clear-button {
        background-color: #f44336 !important;
        color: white !important;
    }
    
    /* Title styling */
    .title-text {
        color: #333;
        font-weight: 700;
        margin-bottom: 5px;
    }
    
    .subtitle-text {
        color: #666;
        font-size: 0.9em;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- Main App ---
st.markdown('<h1 class="title-text">🤖 Zeno AI Assistant</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle-text">Your intelligent voice and text assistant</p>', unsafe_allow_html=True)

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display help in sidebar
with st.sidebar:
    st.header("ℹ️ Help & Commands")
    st.markdown("""
    **App Control:**  
    "Open notepad", "Open calculator", "Open chrome"  
    *(Will search online if app not found)*
    
    **Calculations:**  
    "Calculate 25 + 30", "What is 15 times 8?"
    
    **Shopping:**  
    "Order laptop from Flipkart", "Buy headphones"
    
    **General Chat:**  
    Ask any question for AI responses
    """)
    st.markdown("---")
    st.caption("Made with ❤️ using Gemini AI")

# Chat history display
if st.session_state.chat_history:
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    for ts, role, msg in st.session_state.chat_history:
        if role == "You":
            st.markdown(f"""
                <div class="user-message">
                    <div class="timestamp">You • {ts}</div>
                    <div>{msg}</div>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div class="bot-message">
                    <div class="timestamp">Zeno • {ts}</div>
                    <div>{msg}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.info("💡 Start by typing a message or using voice input below")

# Input area at bottom
st.markdown('<div class="input-container">', unsafe_allow_html=True)

cols = st.columns([0.8, 0.1, 0.1, 0.1])
with cols[0]:
    user_msg = st.text_input("Type your message", label_visibility="collapsed", 
                           placeholder="Type your message or command here...")

with cols[1]:
    if st.button("🎤", key="voice_btn", help="Voice Input"):
        transcribed = record_voice()
        if transcribed:
            st.session_state.input_text = transcribed
            try:
                lang = detect(transcribed)
                chat_reply(transcribed, lang)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

with cols[2]:
    if st.button("➡️", key="send_btn", help="Send Message"):
        if user_msg:
            try:
                lang = detect(user_msg)
                chat_reply(user_msg, lang)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")

with cols[3]:
    if st.button("🗑️", key="clear_btn", help="Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# PDF download option
if st.session_state.chat_history:
    with st.sidebar:
        if st.button("📥 Export Chat as PDF"):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)
                
                pdf.cell(200, 10, "Zeno Assistant Chat History", ln=True, align='C')
                pdf.ln(10)
                
                for ts, role, msg in st.session_state.chat_history:
                    try:
                        line = f"{ts} | {role}: {msg}"
                        pdf.multi_cell(0, 10, line.encode('latin-1', 'replace').decode('latin-1'))
                        pdf.ln(2)
                    except:
                        pdf.multi_cell(0, 10, f"{ts} | {role}: [Error displaying text]")
                        pdf.ln(2)
                
                pdf_path = os.path.join(tempfile.gettempdir(), "zeno_chat.pdf")
                pdf.output(pdf_path)
                
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF Now",
                        data=f,
                        file_name="zeno_chat.pdf",
                        mime="application/pdf"
                    )
            except Exception as e:
                st.error(f"PDF generation error: {str(e)}")