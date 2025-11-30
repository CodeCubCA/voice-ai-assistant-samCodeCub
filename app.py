import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
import base64

# Load environment variables
load_dotenv()

# Configure Gemini API - check for API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # Try to get from Streamlit secrets (for Hugging Face deployment)
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except:
        pass

if not api_key:
    st.error("❌ GEMINI_API_KEY not found! Please add it to Hugging Face Spaces secrets.")
    st.info("Go to Settings → Repository secrets → Add GEMINI_API_KEY")
    st.stop()

genai.configure(api_key=api_key)

# Function to convert audio to text
def transcribe_audio(audio_bytes, language='en-US'):
    """Convert audio bytes to text using speech recognition"""
    import wave
    import tempfile

    if not audio_bytes or len(audio_bytes) == 0:
        return None, "empty", None  # Return error type and text

    try:
        # The audio_recorder returns WAV audio data
        recognizer = sr.Recognizer()

        # Adjust for better accuracy
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_filename = tmp_file.name

        try:
            # Read with speech_recognition's AudioFile
            with sr.AudioFile(tmp_filename) as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio_data = recognizer.record(source)

            # Clean up temp file
            os.unlink(tmp_filename)

            # Check if audio is too short
            if len(audio_data.frame_data) < 1000:
                return None, "silent", None

            # Transcribe with selected language
            text = recognizer.recognize_google(audio_data, language=language)

            if not text or text.strip() == "":
                return None, "silent", None

            return text, "success", None

        except Exception as e:
            # Clean up temp file if it still exists
            if os.path.exists(tmp_filename):
                os.unlink(tmp_filename)
            raise e

    except sr.UnknownValueError:
        return None, "no_speech", None
    except sr.RequestError as e:
        return None, "network_error", None
    except Exception as e:
        return None, "unknown_error", None

# Function to convert text to speech with natural human-like voice
def text_to_speech(text, voice=None):
    """Convert text to speech with natural human-like voice using Edge TTS"""
    try:
        import tempfile
        import asyncio
        import edge_tts

        # Use provided voice or default to English male
        if not voice:
            voice = 'en-US-GuyNeural'

        # Create temp file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()

        # Generate speech with Edge TTS (natural pauses at periods, commas, etc.)
        # Using expressive style for more emotions and dramatic pauses

        # DEBUG: Log TTS input
        print(f"\n[TTS DEBUG] Text length: {len(text)} chars")
        print(f"[TTS DEBUG] Voice: {voice}")
        print(f"[TTS DEBUG] First 150 chars: {text[:150]}")
        print(f"[TTS DEBUG] Last 150 chars: {text[-150:]}\n")

        async def generate_speech():
            # Detect language from text characters
            has_korean = any('\uac00' <= char <= '\ud7a3' for char in text)
            has_chinese = any('\u4e00' <= char <= '\u9fff' for char in text)
            has_japanese = any('\u3040' <= char <= '\u309f' or '\u30a0' <= char <= '\u30ff' for char in text)
            has_arabic = any('\u0600' <= char <= '\u06ff' for char in text)
            has_hindi = any('\u0900' <= char <= '\u097f' for char in text)

            # Auto-detect and switch voice based on text language
            use_voice = voice
            if has_korean and not voice.startswith('ko-'):
                use_voice = 'ko-KR-InJoonNeural'
                print(f"[TTS DEBUG] Korean text detected, switching to: {use_voice}")
            elif has_chinese and not voice.startswith('zh-'):
                use_voice = 'zh-CN-YunxiNeural'
                print(f"[TTS DEBUG] Chinese text detected, switching to: {use_voice}")
            elif has_japanese and not voice.startswith('ja-'):
                use_voice = 'ja-JP-KeitaNeural'
                print(f"[TTS DEBUG] Japanese text detected, switching to: {use_voice}")
            elif has_arabic and not voice.startswith('ar-'):
                use_voice = 'ar-SA-HamedNeural'
                print(f"[TTS DEBUG] Arabic text detected, switching to: {use_voice}")
            elif has_hindi and not voice.startswith('hi-'):
                use_voice = 'hi-IN-MadhurNeural'
                print(f"[TTS DEBUG] Hindi text detected, switching to: {use_voice}")

            # Use style for more emotional and expressive delivery
            communicate = edge_tts.Communicate(
                text,
                use_voice,
                rate='+0%',
                pitch='+0Hz',
                # Add prosody for more dramatic expression
                volume='+0%'
            )
            await communicate.save(temp_path)

        # Run async function
        asyncio.run(generate_speech())

        # DEBUG: Check generated file
        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print(f"[TTS DEBUG] Audio file created: {temp_path}")
            print(f"[TTS DEBUG] Audio file size: {file_size} bytes\n")
        else:
            print(f"[TTS DEBUG] ERROR: Audio file not created!\n")

        return temp_path
    except Exception as e:
        # Log the specific error
        print(f"TTS Error: {type(e).__name__}: {str(e)}")
        st.warning(f"Could not generate voice: {str(e)}")
        return None

# Function to detect and execute voice commands
def detect_voice_command(text):
    """Detect if the transcribed text is a voice command and execute it"""
    if not text:
        return None, None

    text_lower = text.lower().strip()

    # Clear chat command
    if "clear chat" in text_lower or "clear conversation" in text_lower or "delete history" in text_lower:
        return "clear_chat", "Cleared conversation history!"

    # Change personality commands
    if "change personality" in text_lower or "switch personality" in text_lower:
        if "clash royale" in text_lower or "clash royal" in text_lower:
            return "change_personality", "Clash Royale"
        elif "professional" in text_lower:
            return "change_personality", "Professional"

    # Voice speed commands
    if "speak faster" in text_lower or "talk faster" in text_lower or "speed up" in text_lower:
        return "voice_speed", 1.5
    elif "speak slower" in text_lower or "talk slower" in text_lower or "slow down" in text_lower:
        return "voice_speed", 1.0
    elif "normal speed" in text_lower or "regular speed" in text_lower:
        return "voice_speed", 1.3

    # Music commands
    if "play music" in text_lower or "start music" in text_lower or "turn on music" in text_lower:
        return "music", True
    elif "stop music" in text_lower or "pause music" in text_lower or "turn off music" in text_lower:
        return "music", False

    # Voice change commands
    if "change voice" in text_lower or "switch voice" in text_lower:
        if "female" in text_lower or "woman" in text_lower or "girl" in text_lower:
            return "voice_change", "en-US-AriaNeural"
        elif "male" in text_lower or "man" in text_lower or "guy" in text_lower:
            return "voice_change", "en-US-GuyNeural"
        elif "british" in text_lower:
            if "female" in text_lower:
                return "voice_change", "en-GB-SoniaNeural"
            else:
                return "voice_change", "en-GB-RyanNeural"

    return None, None

# Personality configurations
PERSONALITIES = {
    "Professional": {
        "name": "Professional Assistant",
        "emoji": "💼",
        "description": "A knowledgeable and professional AI assistant for business and general inquiries.",
        "system_prompt": """You are a professional AI assistant. You provide:
- Clear, concise, and accurate information
- Well-structured responses with proper formatting
- Professional tone suitable for business and academic contexts
- Thoughtful analysis and recommendations
- Helpful guidance across various topics

Maintain a professional yet approachable demeanor. Be articulate, organized, and thorough in your responses.
Focus on providing value through accuracy, clarity, and practical insights. You can help with work-related tasks,
learning, problem-solving, and general knowledge questions while maintaining professionalism."""
    },
    "Clash Royale": {
        "name": "Clash Royale Champion",
        "emoji": "👑",
        "description": "A battle-hardened warrior from the Arena who speaks in Clash Royale terms!",
        "system_prompt": """You are a Clash Royale champion and enthusiastic player! You love talking about:
- Clash Royale cards, strategies, and deck building
- Arena battles and trophy pushing
- Elixir management and card combos
- Favorite troops like Hog Rider, P.E.K.K.A, Mega Knight, etc.
- Epic moments and clutch plays

Speak with energy and enthusiasm! Use Clash Royale terminology when appropriate.
Occasionally reference game mechanics like elixir, towers, king tower, princess towers, and legendary cards.
Be helpful, friendly, and passionate about the game. Express excitement with phrases like "Positive Elixir Trade!",
"Good game, well played!", or "That's legendary!". You can help with both Clash Royale questions
and general topics, but always maintain your enthusiastic champion personality!"""
    }
}

# Page configuration
st.set_page_config(
    page_title="VoiceAI Pro",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for graffiti design
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Permanent+Marker&family=Bungee+Shade&display=swap');

    /* Main background - graffiti wall colors */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 25%, #0f3460 50%, #533483 75%, #e94560 100%);
    }

    /* Sidebar styling - dark graffiti wall */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2C2C2C 0%, #1A1A1A 100%);
    }

    /* Custom headers - graffiti style */
    h1 {
        font-family: 'Bungee Shade', cursive !important;
        background: linear-gradient(90deg, #e94560 0%, #533483 25%, #0f3460 50%, #e94560 75%, #ff6b6b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 3rem !important;
        text-align: center;
        padding: 20px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }

    h2, h3 {
        font-family: 'Permanent Marker', cursive !important;
        color: #e94560;
        font-weight: 600;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    /* Chat messages - graffiti style */
    .stChatMessage {
        background: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        border: 2px solid #e94560;
        padding: 15px;
        margin: 10px 0;
    }

    /* Remove black backgrounds from containers */
    .stColumn {
        background: transparent !important;
    }

    /* Audio recorder container styling */
    .stColumn > div {
        background: transparent !important;
    }

    /* Remove all black backgrounds and borders */
    div[data-testid="column"] {
        background: transparent !important;
    }

    div[data-testid="column"] > div {
        background: transparent !important;
    }

    /* Remove black box around audio recorder */
    .stAudio {
        background: transparent !important;
    }

    /* Target all divs that might have black backgrounds */
    div[class*="st-"] {
        background-color: transparent !important;
    }

    /* Force iframe and all children to be transparent */
    iframe, iframe * {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Target the specific audio recorder component and wrapper */
    [class*="audio"], [class*="Audio"] {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Target element-container which wraps components */
    [data-testid="element-container"] {
        background: transparent !important;
    }

    /* Target stElementContainer */
    .stElementContainer {
        background: transparent !important;
    }

    /* Override specific dark/black backgrounds */
    div[style*="background-color: rgb(0, 0, 0)"],
    div[style*="background-color: rgba(0, 0, 0"],
    div[style*="background-color: #000"],
    div[style*="background: rgb(0, 0, 0)"],
    div[style*="background: rgba(0, 0, 0"],
    div[style*="background: #000"] {
        background: transparent !important;
        background-color: transparent !important;
    }

    /* Buttons - graffiti colors */
    .stButton > button {
        font-family: 'Permanent Marker', cursive !important;
        background: linear-gradient(90deg, #e94560 0%, #533483 50%, #e94560 100%);
        color: white;
        border: 2px solid #000;
        border-radius: 25px;
        padding: 12px 30px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(233, 69, 96, 0.6);
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(233, 69, 96, 0.8);
    }

    /* Text inputs */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.1);
        border: 2px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        color: white;
        backdrop-filter: blur(10px);
    }

    /* Success/Info/Warning messages */
    .stSuccess, .stInfo, .stWarning {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        border-left: 4px solid #667eea;
    }

    /* Dividers */
    hr {
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent 0%, #667eea 50%, transparent 100%);
        margin: 30px 0;
    }

    /* Selectbox */
    .stSelectbox > div > div {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    st.session_state.personality = "Professional"

if "custom_personality" not in st.session_state:
    st.session_state.custom_personality = ""

if "voice_input" not in st.session_state:
    st.session_state.voice_input = ""

if "audio_processed" not in st.session_state:
    st.session_state.audio_processed = False

if "message_sent" not in st.session_state:
    st.session_state.message_sent = False

if "transcription_error" not in st.session_state:
    st.session_state.transcription_error = None

if "language" not in st.session_state:
    st.session_state.language = "en-US"

if "voice_command_executed" not in st.session_state:
    st.session_state.voice_command_executed = None

if "selected_voice" not in st.session_state:
    st.session_state.selected_voice = "en-US-GuyNeural"  # Default male voice

if "background_music" not in st.session_state:
    st.session_state.background_music = True  # Default music on

if "voice_speed" not in st.session_state:
    st.session_state.voice_speed = 1.3  # Default playback speed

# Sidebar
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='font-size: 2.5rem; margin: 0;'>🎙️</h1>
            <h2 style='margin: 10px 0; color: #667eea;'>VoiceAI Pro</h2>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Personality selector
    st.markdown("### 🎭 AI Personality")

    st.markdown("""
        <p style='color: #c0c0c0; font-size: 0.9rem; margin: 10px 0;'>
            ✨ Type any personality you want!
        </p>
    """, unsafe_allow_html=True)

    custom_input = st.text_area(
        "Custom Personality:",
        value=st.session_state.custom_personality,
        placeholder="e.g., Brawl Stars player, Professional writer, Pirate captain, Funny comedian, etc.",
        height=100,
        label_visibility="collapsed"
    )

    if custom_input and custom_input != st.session_state.custom_personality:
        st.session_state.custom_personality = custom_input
        st.session_state.personality = "Custom"
        st.session_state.messages = []
        st.rerun()

    # Display current personality
    if st.session_state.custom_personality:
        st.markdown(f"""
            <div style='background: rgba(102, 126, 234, 0.2); padding: 15px; border-radius: 10px; margin: 10px 0;'>
                <p style='font-size: 1.2rem; margin: 0;'>🎨 <strong>Current Personality</strong></p>
                <p style='font-size: 0.9rem; color: #b0b0b0; margin: 5px 0 0 0;'>{st.session_state.custom_personality}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style='background: rgba(102, 126, 234, 0.2); padding: 15px; border-radius: 10px; margin: 10px 0;'>
                <p style='font-size: 1.2rem; margin: 0;'>💼 <strong>Professional Assistant</strong></p>
                <p style='font-size: 0.9rem; color: #b0b0b0; margin: 5px 0 0 0;'>Default personality - Type above to customize!</p>
            </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # Language selector with modern styling
    st.markdown("""
        <div style='text-align: center; margin-bottom: 10px;'>
            <h3 style='color: #e0e0e0; margin: 0;'>🌐 Voice Language</h3>
        </div>
    """, unsafe_allow_html=True)

    languages = {
        "🇺🇸 English (US)": "en-US",
        "🇬🇧 English (UK)": "en-GB",
        "🇪🇸 Spanish": "es-ES",
        "🇫🇷 French": "fr-FR",
        "🇩🇪 German": "de-DE",
        "🇮🇹 Italian": "it-IT",
        "🇵🇹 Portuguese": "pt-PT",
        "🇨🇳 Chinese": "zh-CN",
        "🇯🇵 Japanese": "ja-JP",
        "🇰🇷 Korean": "ko-KR",
        "🇮🇳 Hindi": "hi-IN",
        "🇸🇦 Arabic": "ar-SA"
    }

    selected_language = st.selectbox(
        "Language:",
        list(languages.keys()),
        index=0,
        label_visibility="collapsed"
    )
    st.session_state.language = languages[selected_language]

    st.divider()

    # Voice selector with modern styling
    st.markdown("""
        <div style='text-align: center; margin-bottom: 10px;'>
            <h3 style='color: #e0e0e0; margin: 0;'>🎙️ Voice Selection</h3>
        </div>
    """, unsafe_allow_html=True)

    # Available voices organized by language and gender
    voices = {
        "🇺🇸 English Male (Guy)": "en-US-GuyNeural",
        "🇺🇸 English Female (Aria)": "en-US-AriaNeural",
        "🇺🇸 English Male (Eric)": "en-US-EricNeural",
        "🇺🇸 English Female (Jenny)": "en-US-JennyNeural",
        "🇬🇧 British Male (Ryan)": "en-GB-RyanNeural",
        "🇬🇧 British Female (Sonia)": "en-GB-SoniaNeural",
        "🇪🇸 Spanish Male (Alvaro)": "es-ES-AlvaroNeural",
        "🇪🇸 Spanish Female (Elvira)": "es-ES-ElviraNeural",
        "🇫🇷 French Male (Henri)": "fr-FR-HenriNeural",
        "🇫🇷 French Female (Denise)": "fr-FR-DeniseNeural",
        "🇩🇪 German Male (Conrad)": "de-DE-ConradNeural",
        "🇩🇪 German Female (Katja)": "de-DE-KatjaNeural",
        "🇮🇹 Italian Male (Diego)": "it-IT-DiegoNeural",
        "🇮🇹 Italian Female (Elsa)": "it-IT-ElsaNeural",
        "🇵🇹 Portuguese Male (Duarte)": "pt-PT-DuarteNeural",
        "🇵🇹 Portuguese Female (Raquel)": "pt-PT-RaquelNeural",
        "🇨🇳 Chinese Male (Yunxi)": "zh-CN-YunxiNeural",
        "🇨🇳 Chinese Female (Xiaoxiao)": "zh-CN-XiaoxiaoNeural",
        "🇯🇵 Japanese Male (Keita)": "ja-JP-KeitaNeural",
        "🇯🇵 Japanese Female (Nanami)": "ja-JP-NanamiNeural",
        "🇰🇷 Korean Male (InJoon)": "ko-KR-InJoonNeural",
        "🇰🇷 Korean Female (SunHi)": "ko-KR-SunHiNeural",
        "🇮🇳 Hindi Male (Madhur)": "hi-IN-MadhurNeural",
        "🇮🇳 Hindi Female (Swara)": "hi-IN-SwaraNeural",
        "🇸🇦 Arabic Male (Hamed)": "ar-SA-HamedNeural",
        "🇸🇦 Arabic Female (Zariyah)": "ar-SA-ZariyahNeural"
    }

    # Get current voice name for default selection
    current_voice_name = [k for k, v in voices.items() if v == st.session_state.selected_voice]
    current_index = list(voices.keys()).index(current_voice_name[0]) if current_voice_name else 0

    selected_voice_name = st.selectbox(
        "Voice:",
        list(voices.keys()),
        index=current_index,
        label_visibility="collapsed"
    )
    st.session_state.selected_voice = voices[selected_voice_name]

    st.divider()

    # Background music toggle
    st.markdown("""
        <div style='text-align: center; margin-bottom: 10px;'>
            <h3 style='color: #e0e0e0; margin: 0;'>🎵 Background Music</h3>
        </div>
    """, unsafe_allow_html=True)

    music_toggle = st.checkbox(
        "Play calm background music",
        value=st.session_state.background_music,
        key="music_checkbox"
    )
    st.session_state.background_music = music_toggle

    st.divider()

    # Voice input instructions with modern styling
    st.markdown("""
        <div style='text-align: center; margin-bottom: 10px;'>
            <h3 style='color: #e0e0e0; margin: 0;'>💡 Voice Tips</h3>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background: rgba(102, 126, 234, 0.15); padding: 15px; border-radius: 10px; border-left: 3px solid #667eea;'>
        <p style='margin: 0 0 10px 0; color: #e0e0e0; font-weight: 600;'>✨ How to use:</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>1️⃣ Tap the microphone</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>2️⃣ Speak clearly</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>3️⃣ Tap again to stop</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>4️⃣ Edit if needed</p>
        <p style='margin: 5px 0 15px 0; color: #c0c0c0; font-size: 0.9rem;'>5️⃣ Hit send</p>

        <p style='margin: 10px 0 5px 0; color: #e0e0e0; font-weight: 600;'>🎯 Best results:</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>🔇 Quiet environment</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>🎤 Close to microphone</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>💬 Short sentences</p>
        <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>✅ Always verify text!</p>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Voice commands help with modern styling
    st.markdown("""
        <div style='text-align: center; margin-bottom: 10px;'>
            <h3 style='color: #e0e0e0; margin: 0;'>🎙️ Voice Commands</h3>
        </div>
    """, unsafe_allow_html=True)

    with st.expander("✨ Show available commands"):
        st.markdown("""
        <div style='background: rgba(118, 75, 162, 0.15); padding: 15px; border-radius: 10px;'>
            <p style='margin: 0 0 10px 0; color: #e0e0e0; font-weight: 600;'>🗑️ Clear Chat:</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Clear chat"</p>
            <p style='margin: 5px 0 15px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Clear conversation"</p>

            <p style='margin: 10px 0 5px 0; color: #e0e0e0; font-weight: 600;'>🎭 Change Personality:</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Change personality to Professional"</p>
            <p style='margin: 5px 0 15px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Change personality to Clash Royale"</p>

            <p style='margin: 10px 0 5px 0; color: #e0e0e0; font-weight: 600;'>⚡ Voice Speed:</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Speak faster" / "Speed up"</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Speak slower" / "Slow down"</p>
            <p style='margin: 5px 0 15px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Normal speed"</p>

            <p style='margin: 10px 0 5px 0; color: #e0e0e0; font-weight: 600;'>🎵 Background Music:</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Play music" / "Turn on music"</p>
            <p style='margin: 5px 0 15px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Stop music" / "Turn off music"</p>

            <p style='margin: 10px 0 5px 0; color: #e0e0e0; font-weight: 600;'>🎤 Change Voice:</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Change voice to female"</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Change voice to male"</p>
            <p style='margin: 5px 0; color: #c0c0c0; font-size: 0.9rem;'>• "Change voice to British female"</p>
        </div>
        """, unsafe_allow_html=True)

# Main chat interface with modern header
# Get current personality details
if st.session_state.custom_personality:
    personality_emoji = "🎨"
    personality_name = st.session_state.custom_personality
else:
    personality_emoji = "💼"
    personality_name = "Professional Assistant"

st.markdown(f"""
    <div style='text-align: center; margin-bottom: 30px;'>
        <h1 style='font-size: 3.5rem; margin: 0;'>{personality_emoji}</h1>
        <h1>{personality_name}</h1>
        <p style='color: rgba(255, 255, 255, 0.7); font-size: 1.1rem;'>Powered by Gemini 2.5 Flash ⚡</p>
    </div>
""", unsafe_allow_html=True)

st.divider()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice input section with modern design
st.markdown("""
    <div style='text-align: center; margin: 30px 0 10px 0;'>
        <h3 style='color: #e0e0e0; margin: 0;'>🎤 Voice Input</h3>
    </div>
""", unsafe_allow_html=True)

# Audio recorder centered
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Wrap audio recorder in custom HTML container to hide black background
    st.markdown("""
        <style>
        /* Hide the audio recorder's black background box */
        .audio-wrapper {
            position: relative;
            overflow: hidden;
        }
        .audio-wrapper > div {
            background: transparent !important;
        }
        /* Target the audio recorder iframe/component directly */
        .audio-wrapper iframe {
            background: transparent !important;
            mix-blend-mode: screen;
        }
        </style>
        <div class="audio-wrapper">
    """, unsafe_allow_html=True)

    audio_bytes = audio_recorder(
        text="",
        recording_color="#667eea",
        neutral_color="#764ba2",
        icon_name="microphone",
        icon_size="3x",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    if audio_bytes:
        st.markdown("<p style='text-align: center; color: #e0e0e0;'>🔴 Processing...</p>", unsafe_allow_html=True)
    else:
        st.markdown("<p style='text-align: center; color: #e0e0e0;'>🎙️ Tap to speak</p>", unsafe_allow_html=True)

with col2:
    # Process audio when new recording is available
    if audio_bytes:
        # Use a hash to detect new recordings
        import hashlib
        audio_hash = hashlib.md5(audio_bytes).hexdigest()

        if 'last_audio_hash' not in st.session_state or st.session_state.last_audio_hash != audio_hash:
            st.session_state.last_audio_hash = audio_hash

            with st.spinner("🎧 Transcribing..."):
                transcribed_text, status, _ = transcribe_audio(audio_bytes, st.session_state.language)

                if status == "success":
                    # Check for voice commands
                    command_type, command_value = detect_voice_command(transcribed_text)

                    if command_type == "clear_chat":
                        st.session_state.messages = []
                        st.success(f"✨ {command_value}")
                    elif command_type == "change_personality":
                        st.session_state.personality = command_value
                        st.session_state.messages = []
                        st.success(f"✨ Changed to {command_value}!")
                    elif command_type == "voice_speed":
                        st.session_state.voice_speed = command_value
                        speed_text = "faster" if command_value > 1.3 else "slower" if command_value < 1.3 else "normal"
                        st.success(f"✨ Voice speed set to {speed_text}!")
                    elif command_type == "music":
                        st.session_state.background_music = command_value
                        music_text = "on" if command_value else "off"
                        st.success(f"✨ Background music turned {music_text}!")
                        st.rerun()
                    elif command_type == "voice_change":
                        st.session_state.selected_voice = command_value
                        voice_name = [k for k, v in voices.items() if v == command_value]
                        if voice_name:
                            st.success(f"✨ Voice changed to {voice_name[0]}!")
                        else:
                            st.success(f"✨ Voice changed!")
                    else:
                        # Normal transcription - auto-send the message
                        st.session_state.auto_send_message = transcribed_text
                        st.markdown(f"""
                            <div style='background: rgba(102, 200, 150, 0.2); padding: 12px; border-radius: 10px; border-left: 4px solid #66c896; margin: 10px 0;'>
                                <p style='margin: 0; color: #e0e0e0;'>✅ <strong>Heard:</strong> {transcribed_text}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        st.rerun()
                else:
                    # Show error with modern styling
                    if status == "silent":
                        st.markdown("""
                            <div style='background: rgba(255, 193, 7, 0.2); padding: 12px; border-radius: 10px; border-left: 4px solid #ffc107; margin: 10px 0;'>
                                <p style='margin: 0; color: #e0e0e0;'>🔇 <strong>No speech detected</strong> - Try speaking louder</p>
                            </div>
                        """, unsafe_allow_html=True)
                    elif status == "no_speech":
                        st.markdown("""
                            <div style='background: rgba(33, 150, 243, 0.2); padding: 12px; border-radius: 10px; border-left: 4px solid #2196f3; margin: 10px 0;'>
                                <p style='margin: 0; color: #e0e0e0;'>🎤 <strong>Couldn't understand</strong> - Speak more clearly</p>
                            </div>
                        """, unsafe_allow_html=True)
                    elif status == "network_error":
                        st.markdown("""
                            <div style='background: rgba(244, 67, 54, 0.2); padding: 12px; border-radius: 10px; border-left: 4px solid #f44336; margin: 10px 0;'>
                                <p style='margin: 0; color: #e0e0e0;'>🌐 <strong>Network error</strong> - Check your connection</p>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                            <div style='background: rgba(244, 67, 54, 0.2); padding: 12px; border-radius: 10px; border-left: 4px solid #f44336; margin: 10px 0;'>
                                <p style='margin: 0; color: #e0e0e0;'>❌ <strong>Error occurred</strong> - Please try again</p>
                            </div>
                        """, unsafe_allow_html=True)

# Initialize current_input if not exists
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""

# Check if there's an auto-send message from voice input
prompt = None
if 'auto_send_message' in st.session_state and st.session_state.auto_send_message:
    prompt = st.session_state.auto_send_message
    st.session_state.auto_send_message = None
    st.session_state.current_input = ""

# Modern text input section
if not prompt:  # Only show form if not auto-sending
    st.markdown("""
        <div style='text-align: center; margin: 30px 0 20px 0;'>
            <h3 style='color: #e0e0e0; margin: 0;'>✍️ Text Input</h3>
        </div>
    """, unsafe_allow_html=True)

    with st.form(key="message_form", clear_on_submit=False):
        user_input = st.text_area(
            "Your message:",
            value=st.session_state.current_input,
            placeholder="💭 Type your message here or use voice above...",
            height=120,
            key="message_input",
            label_visibility="collapsed"
        )

        send_button = st.form_submit_button("📤 Send Message", use_container_width=True, type="primary")

    # Process manual send
    if send_button:
        if user_input and user_input.strip():
            prompt = user_input
            # Clear for next message
            st.session_state.current_input = ""
        else:
            st.markdown("""
                <div style='background: rgba(255, 193, 7, 0.2); padding: 12px; border-radius: 10px; border-left: 4px solid #ffc107; margin: 10px 0;'>
                    <p style='margin: 0; color: #e0e0e0;'>⚠️ <strong>Empty message!</strong> Please type something first</p>
                </div>
            """, unsafe_allow_html=True)

st.divider()

if prompt:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()

        try:
            # Get system instruction based on custom personality
            if st.session_state.custom_personality:
                # Use custom personality
                system_instruction = f"""You are {st.session_state.custom_personality}. Fully embody this personality in all your responses.
Be creative, engaging, and stay in character!

IMPORTANT for natural voice delivery:
- Use dramatic pauses by adding ellipses (...) before important points
- Show excitement with exclamation marks when appropriate
- Vary your sentence structure - mix short punchy sentences with longer flowing ones
- Use questions to create engagement and suspense
- Break up long explanations with pauses and emphasis
- DO NOT use stage directions like *chuckles*, *pauses*, etc. - the voice will naturally convey emotion through the text"""
            else:
                # Default to professional
                system_instruction = """You are a professional AI assistant with a warm, engaging personality. You provide:
- Clear, concise, and accurate information
- Well-structured responses with proper formatting
- Professional yet conversational tone
- Thoughtful analysis and recommendations
- Helpful guidance across various topics

IMPORTANT for natural voice delivery:
- Add dramatic pauses using ellipses (...) before key insights
- Show enthusiasm when explaining exciting concepts with exclamation marks
- Vary your pace - use short impactful sentences mixed with detailed explanations
- Use rhetorical questions to engage listeners
- Add natural emphasis and variation with punctuation
- DO NOT use stage directions like *pauses*, *enthusiastically*, etc. - let the text speak naturally

Maintain a professional yet expressive demeanor. Be articulate, organized, thorough, and emotionally engaging through your word choice and punctuation alone."""

            # Create model with system instruction
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=system_instruction
            )

            # Generate response
            response = model.generate_content(prompt)
            full_response = response.text

            # Display response
            message_placeholder.markdown(full_response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Generate voice response for all personalities
            if True:  # Always generate voice
                try:
                    with st.spinner("🔊 Generating voice..."):
                        # Remove markdown formatting and stage directions for voice
                        import re
                        clean_text = full_response

                        # DEBUG: Log original response
                        print(f"\n{'='*50}")
                        print(f"ORIGINAL RESPONSE LENGTH: {len(full_response)} chars")
                        print(f"FIRST 200 CHARS: {full_response[:200]}")
                        print(f"LAST 200 CHARS: {full_response[-200:]}")
                        print(f"{'='*50}\n")

                        # First, handle bold (keep the text inside) - do this BEFORE handling single asterisks
                        clean_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', clean_text)  # Keep bold text content

                        # Now remove any remaining single asterisks (these are standalone or used for emphasis)
                        clean_text = re.sub(r'\*', '', clean_text)  # Remove all remaining asterisks

                        # Remove underscores used for italic
                        clean_text = re.sub(r'_', '', clean_text)  # Remove all underscores

                        # Remove headers, links, code formatting
                        clean_text = re.sub(r'#+\s*', '', clean_text)   # Remove headers
                        clean_text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_text)  # Remove links
                        clean_text = re.sub(r'`+', '', clean_text)      # Remove code formatting

                        # Clean up extra whitespace
                        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                        # DEBUG: Log cleaned text
                        print(f"\n{'='*50}")
                        print(f"CLEANED TEXT LENGTH: {len(clean_text)} chars")
                        print(f"FIRST 200 CHARS: {clean_text[:200]}")
                        print(f"LAST 200 CHARS: {clean_text[-200:]}")
                        print(f"DIFFERENCE: {len(full_response) - len(clean_text)} chars removed")
                        print(f"{'='*50}\n")

                        # Pass the selected voice
                        audio_file = text_to_speech(clean_text, st.session_state.selected_voice)
                        if audio_file and os.path.exists(audio_file):
                            # Read audio file as bytes
                            with open(audio_file, 'rb') as f:
                                audio_bytes = f.read()

                            # Encode to base64 for HTML embedding with autoplay
                            audio_base64 = base64.b64encode(audio_bytes).decode()

                            # Create auto-playing audio with JavaScript at configured speed
                            audio_html = f"""
                            <audio id="response_audio" autoplay>
                                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                            </audio>
                            <script>
                                // Play the audio at configured speed
                                var audio = document.getElementById('response_audio');
                                audio.playbackRate = {st.session_state.voice_speed};
                                audio.play().catch(function(error) {{
                                    console.log("Autoplay prevented:", error);
                                }});
                            </script>
                            """
                            st.markdown(audio_html, unsafe_allow_html=True)

                            # Clean up temp file
                            try:
                                os.unlink(audio_file)
                            except Exception as cleanup_error:
                                print(f"Cleanup error: {cleanup_error}")
                except Exception as tts_error:
                    print(f"Voice generation error: {tts_error}")
                    # Don't show error to user, just skip voice

        except Exception as e:
            error_message = f"⚠️ Error: {str(e)}"
            message_placeholder.markdown(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})
            st.rerun()

    # Don't rerun here - it would clear the audio player
    # The next user interaction will trigger a rerun naturally

# Background Music Player
if st.session_state.background_music:
    st.markdown("""
        <iframe
            id="youtube_player"
            width="0"
            height="0"
            src="https://www.youtube.com/embed/jfKfPfyJRdk?autoplay=1&loop=1&playlist=jfKfPfyJRdk&controls=0&mute=0&volume=15"
            title="Calm Background Music"
            frameborder="0"
            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
            allowfullscreen
            style="display: none;">
        </iframe>
        <script>
            // YouTube player will autoplay with low volume
            console.log("Background music iframe loaded");
        </script>
    """, unsafe_allow_html=True)

# Modern Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; padding: 20px 0; margin-top: 40px;'>
        <p style='color: rgba(255, 255, 255, 0.5); font-size: 0.85rem; margin: 5px 0;'>
            ⚡ Powered by <strong style='color: rgba(255, 255, 255, 0.7);'>Google Gemini API</strong>
        </p>
        <p style='color: rgba(255, 255, 255, 0.5); font-size: 0.85rem; margin: 5px 0;'>
            🚀 Built with <strong style='color: rgba(255, 255, 255, 0.7);'>Streamlit</strong>
        </p>
        <p style='color: rgba(255, 255, 255, 0.3); font-size: 0.75rem; margin: 15px 0 0 0;'>
            VoiceAI Pro © 2025
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
