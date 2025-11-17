import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr
import io
from gtts import gTTS
import base64

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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

# Function to convert text to speech
def text_to_speech(text):
    """Convert text to speech and return audio file"""
    try:
        import tempfile
        # Limit text length to avoid timeouts
        if len(text) > 500:
            text = text[:500] + "..."

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(fp.name)
            return fp.name
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
    page_title="AI Chatbot",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "personality" not in st.session_state:
    st.session_state.personality = "Professional"

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

# Sidebar
with st.sidebar:
    st.title("⚙️ Settings")

    # Personality selector
    personality_choice = st.selectbox(
        "Choose AI Personality:",
        list(PERSONALITIES.keys()),
        index=list(PERSONALITIES.keys()).index(st.session_state.personality)
    )

    # Update personality if changed
    if personality_choice != st.session_state.personality:
        st.session_state.personality = personality_choice
        st.session_state.messages = []  # Clear chat history on personality change
        st.rerun()

    # Display personality info
    current_personality = PERSONALITIES[st.session_state.personality]
    st.markdown(f"### {current_personality['emoji']} {current_personality['name']}")
    st.info(current_personality['description'])

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

    st.divider()

    # About section
    st.markdown("### 📖 About")
    st.markdown("""
    This chatbot uses:
    - **Streamlit** for the interface
    - **Google Gemini API** (gemini-2.5-flash)
    - **Custom personalities** for unique experiences
    - **Voice input** for hands-free interaction
    """)

    st.divider()

    # Language selector
    st.markdown("### 🌍 Language")
    languages = {
        "English (US)": "en-US",
        "English (UK)": "en-GB",
        "Spanish": "es-ES",
        "French": "fr-FR",
        "German": "de-DE",
        "Italian": "it-IT",
        "Portuguese": "pt-PT",
        "Chinese (Mandarin)": "zh-CN",
        "Japanese": "ja-JP",
        "Korean": "ko-KR",
        "Hindi": "hi-IN",
        "Arabic": "ar-SA"
    }

    selected_language = st.selectbox(
        "Voice Recognition Language:",
        list(languages.keys()),
        index=0
    )
    st.session_state.language = languages[selected_language]

    st.divider()

    # Voice input instructions
    st.markdown("### 🎤 Voice Input Tips")
    st.markdown("""
    **How to use:**
    1. Click the microphone button
    2. Speak clearly and slowly
    3. Click again to stop recording
    4. Review and **edit the text** if needed
    5. Click Send button

    **For better accuracy:**
    - Speak in a quiet environment
    - Be close to your microphone
    - Speak clearly and at normal pace
    - Use short sentences
    - Always check and fix errors!
    """)

    st.divider()

    # Voice commands help
    st.markdown("### 🎙️ Voice Commands")
    with st.expander("See available commands"):
        st.markdown("""
        Speak these commands to control the app:

        **Clear Chat:**
        - "Clear chat"
        - "Clear conversation"
        - "Delete history"

        **Change Personality:**
        - "Change personality to Professional"
        - "Change personality to Clash Royale"
        - "Switch personality to Professional"
        - "Switch personality to Clash Royale"
        """)

# Main chat interface
st.title(f"{current_personality['emoji']} AI Chatbot - {current_personality['name']}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Voice input section with form
st.markdown("### 🎤 Voice Input or Type Your Message")

# Audio recorder
col1, col2 = st.columns([1, 5])

with col1:
    audio_bytes = audio_recorder(
        text="",
        recording_color="#e74c3c",
        neutral_color="#3498db",
        icon_name="microphone",
        icon_size="2x",
    )

    if audio_bytes:
        st.caption("🔴 Processing...")
    else:
        st.caption("🔵 Ready")

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
                    else:
                        # Normal transcription - auto-send the message
                        st.session_state.auto_send_message = transcribed_text
                        st.success(f"✅ Heard: **{transcribed_text}**")
                        st.rerun()
                else:
                    # Show error
                    if status == "silent":
                        st.warning("🔇 No speech detected")
                    elif status == "no_speech":
                        st.info("🎤 Couldn't understand")
                    elif status == "network_error":
                        st.error("🌐 Network error")
                    else:
                        st.error("❌ Error occurred")

# Initialize current_input if not exists
if 'current_input' not in st.session_state:
    st.session_state.current_input = ""

# Check if there's an auto-send message from voice input
prompt = None
if 'auto_send_message' in st.session_state and st.session_state.auto_send_message:
    prompt = st.session_state.auto_send_message
    st.session_state.auto_send_message = None
    st.session_state.current_input = ""

# Use a form to prevent reruns on text change
if not prompt:  # Only show form if not auto-sending
    with st.form(key="message_form", clear_on_submit=False):
        user_input = st.text_area(
            "Your message:",
            value=st.session_state.current_input,
            placeholder="Type here or use voice button above...",
            height=100,
            key="message_input"
        )

        send_button = st.form_submit_button("📤 Send", use_container_width=True, type="primary")

    # Process manual send
    if send_button:
        if user_input and user_input.strip():
            prompt = user_input
            # Clear for next message
            st.session_state.current_input = ""
        else:
            st.warning("Please enter a message first!")

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
            # Create model with system instruction
            model = genai.GenerativeModel(
                'gemini-2.5-flash',
                system_instruction=current_personality['system_prompt']
            )

            # Generate response
            response = model.generate_content(prompt)
            full_response = response.text

            # Display response
            message_placeholder.markdown(full_response)

            # Add assistant response to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})

            # Generate voice response for Professional personality only
            if st.session_state.personality == "Professional":
                try:
                    with st.spinner("🔊 Generating voice response..."):
                        audio_file = text_to_speech(full_response)
                        if audio_file and os.path.exists(audio_file):
                            # Read audio file as bytes
                            with open(audio_file, 'rb') as f:
                                audio_bytes = f.read()

                            # Display audio player
                            st.audio(audio_bytes, format='audio/mp3')
                            st.caption("🔊 Click play to hear the response")

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

    # After processing, rerun to clear the input
    st.rerun()

# Footer
st.divider()
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
        Powered by Google Gemini API | Built with Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
