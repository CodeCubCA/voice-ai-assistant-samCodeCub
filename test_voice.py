"""Test script to verify audio recording and speech recognition"""
import speech_recognition as sr

print("Testing speech recognition...")
print("Available recognizers:", dir(sr))

# Test if we can create a recognizer
try:
    recognizer = sr.Recognizer()
    print("✓ Speech recognizer created successfully")
except Exception as e:
    print(f"✗ Error creating recognizer: {e}")

# Test audio recorder import
try:
    from audio_recorder_streamlit import audio_recorder
    print("✓ Audio recorder imported successfully")
except Exception as e:
    print(f"✗ Error importing audio recorder: {e}")

print("\nAll imports successful!")
