"""Simple test of audio recorder"""
import streamlit as st
from audio_recorder_streamlit import audio_recorder
import speech_recognition as sr

st.title("Audio Test")

# Record audio
audio_bytes = audio_recorder(text="Click to record", icon_size="2x")

if audio_bytes:
    st.success(f"Audio recorded! Size: {len(audio_bytes)} bytes")

    # Try to transcribe
    try:
        recognizer = sr.Recognizer()
        audio_data = sr.AudioData(audio_bytes, sample_rate=44100, sample_width=2)
        st.info("Attempting to transcribe...")
        text = recognizer.recognize_google(audio_data)
        st.success(f"Transcription: {text}")
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.info("Click the microphone to record audio")
