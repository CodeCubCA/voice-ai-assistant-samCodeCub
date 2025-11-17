# Voice AI Assistant

A voice-enabled AI chatbot built with Streamlit and Google Gemini API, featuring automatic speech-to-text transcription and multi-language support.

## Features

- **Voice Input**: Click-to-record voice input with automatic transcription
- **Auto-Send**: Messages are automatically sent after voice transcription
- **Multi-Language Support**: Supports 12 languages including English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Hindi, and Arabic
- **Voice Commands**: Control the app with voice commands like "clear chat" or "change personality"
- **Custom Personalities**: Currently features a Clash Royale themed AI personality
- **Chat History**: Full conversation history with message display
- **Manual Text Input**: Type messages manually with a text area and send button

## Technologies Used

- **Streamlit**: Web interface framework
- **Google Gemini API**: AI language model (gemini-2.5-flash)
- **SpeechRecognition**: Speech-to-text conversion using Google's speech recognition
- **audio-recorder-streamlit**: Browser-based audio recording component
- **python-dotenv**: Environment variable management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/CodeCubCA/voice-ai-assistant-samCodeCub.git
cd voice-ai-assistant-samCodeCub
```

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Add your Google Gemini API key to `.env`:
```
GEMINI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
streamlit run app.py
```

## Usage

### Voice Input
1. Click the microphone button
2. Speak clearly when recording
3. Click again to stop recording
4. Your message will be automatically transcribed and sent

### Manual Input
1. Type your message in the text area
2. Click the "Send" button

### Voice Commands
Speak these commands to control the app:
- **Clear Chat**: "Clear chat", "Clear conversation", or "Delete history"
- **Change Personality**: "Change personality to Clash Royale"

## Configuration

### Language Selection
Choose your preferred language for voice recognition from the sidebar. Supported languages:
- English (US/UK)
- Spanish
- French
- German
- Italian
- Portuguese
- Chinese (Mandarin)
- Japanese
- Korean
- Hindi
- Arabic

### Personality Selection
Select different AI personalities from the sidebar (currently Clash Royale themed).

## Tips for Better Voice Recognition

- Speak in a quiet environment
- Be close to your microphone
- Speak clearly at normal pace
- Use short sentences
- Grant microphone permissions in your browser

## Project Structure

```
voice-ai-assistant/
├── app.py                 # Main application file
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in git)
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore file
├── README.md             # This file
└── test files/           # Testing utilities
    ├── test_mic.html
    ├── test_audio_simple.py
    └── test_voice.py
```

## Requirements

- Python 3.7+
- Modern web browser with microphone support
- Internet connection for speech recognition and AI API
- Google Gemini API key

## Troubleshooting

**Voice input not working:**
- Check browser microphone permissions
- Try the `test_mic.html` file to verify microphone access
- Ensure no other app is using your microphone

**Transcription errors:**
- Speak more clearly and slowly
- Reduce background noise
- Try a different language setting
- Check your internet connection

**API errors:**
- Verify your Gemini API key in `.env`
- Check API quota limits
- Ensure internet connection is stable

## License

This project is for educational purposes.

## Credits

Built with Streamlit and Google Gemini API
