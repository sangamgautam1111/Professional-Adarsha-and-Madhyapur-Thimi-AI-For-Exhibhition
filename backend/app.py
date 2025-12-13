import os
import sys
import importlib.util
import re
import time
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from textblob import TextBlob 

# ==================================================================================
# 1. ADVANCED AI MODULES (NOISE CANCELLATION & PERCEPTION)
# ==================================================================================

class NoiseCancelerRNN:
    def __init__(self):
        self.fillers = [
            "um", "uh", "ah", "like", "actually", "basically", "literally", 
            "you know", "i mean", "sort of", "kinda", "umm", "ahh", "eh"
        ]
    
    def clean(self, text):
        if not text: return ""
        clean_text = re.sub(r'\b(\w+)( \1\b)+', r'\1', text, flags=re.IGNORECASE)
        pattern = r'\b(' + '|'.join(self.fillers) + r')\b'
        clean_text = re.sub(pattern, '', clean_text, flags=re.IGNORECASE)
        return ' '.join(clean_text.split())

class PerceptionEngine:
    def analyze(self, text, lang='en'):
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        state = "Neutral"
        if sentiment > 0.3: state = "Happy/Excited"
        elif sentiment < -0.3: state = "Frustrated/Sad"
        
        return {
            "sentiment": state,
            "language": lang,
            "raw_score": sentiment
        }

# ==================================================================================
# 2. RAG PIPELINE LOADING
# ==================================================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
rag_file_path = os.path.join(current_dir, "pipeline.py")

rag_pipeline = None
noise_filter = NoiseCancelerRNN()
nlp_brain = PerceptionEngine()

print("\n" + "="*70)
print(" ADARSHA AI - MULTILINGUAL VOICE & CHAT SERVER")
print(" [SYSTEM] Initializing Noise Cancellation... DONE")
print(" [SYSTEM] Initializing Perception Engine... DONE")
print("="*70)

if os.path.exists(rag_file_path):
    try:
        spec = importlib.util.spec_from_file_location("pipeline", rag_file_path)
        rag_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rag_module)
        if hasattr(rag_module, 'get_chatbot'):
            rag_pipeline = rag_module.get_chatbot()
            print(" [SUCCESS] RAG Pipeline loaded successfully.")
        else:
            print(" [WARNING] 'get_chatbot' factory not found in pipeline.py.")
    except Exception as e:
        print(f" [ERROR] Could not load RAG Pipeline: {e}")
else:
    print(" [INFO] pipeline.py not found. Running in simulation mode.")

print("="*70 + "\n")


# ==================================================================================
# 3. FLASK APP SETUP
# ==================================================================================

app = Flask(__name__)
CORS(app)

# ==================================================================================
# 4. FRONTEND UI (Chat + Voice Hybrid)
# ==================================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Adarsha AI - Hybrid</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-color: #000000;
            --text-color: #e0e0e0;
            --accent-color: #00ff88;
            --nepali-color: #ff0055;
            --input-bg: #1a1a1a;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Courier New', monospace; }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            background-image: radial-gradient(circle at 50% 50%, #111 0%, #000 100%);
        }

        /* HUD */
        .hud {
            position: absolute;
            top: 0; left: 0; width: 100%; padding: 15px;
            display: flex;
            justify-content: space-between;
            z-index: 10;
            background: linear-gradient(to bottom, rgba(0,0,0,0.9), transparent);
        }
        .status-badge {
            background: rgba(20, 20, 20, 0.8);
            padding: 5px 10px;
            border: 1px solid #333;
            border-radius: 4px;
            font-size: 0.8rem;
        }

        .lang-switch { display: flex; gap: 10px; }
        .lang-btn {
            background: #222; border: 1px solid #444; color: #888;
            padding: 5px 15px; cursor: pointer; font-weight: bold; transition: 0.3s;
        }
        .lang-btn.active.en { background: var(--accent-color); color: #000; border-color: var(--accent-color); }
        .lang-btn.active.np { background: var(--nepali-color); color: #fff; border-color: var(--nepali-color); }

        /* VISUALIZER */
        .visualizer-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            position: relative;
            min-height: 200px;
        }

        .core {
            width: 120px; height: 120px;
            border: 3px solid var(--accent-color);
            border-radius: 50%;
            display: flex; justify-content: center; align-items: center;
            box-shadow: 0 0 30px rgba(0, 255, 136, 0.2);
            transition: all 0.3s;
        }
        .core.nepali-mode { border-color: var(--nepali-color); box-shadow: 0 0 30px rgba(255, 0, 85, 0.2); }

        .core-inner {
            width: 80px; height: 80px;
            background: var(--accent-color);
            border-radius: 50%; opacity: 0.8; filter: blur(8px); transition: 0.3s;
        }
        .core.nepali-mode .core-inner { background: var(--nepali-color); }
        .core.listening .core-inner { transform: scale(1.2); opacity: 1; filter: blur(2px); animation: pulse 0.8s infinite; }
        .core.processing { animation: spin 1s infinite linear; border-top-color: transparent; }
        @keyframes pulse { 0% { transform: scale(0.9); } 50% { transform: scale(1.1); } 100% { transform: scale(0.9); } }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

        /* CHAT & TRANSCRIPT AREA */
        .chat-container {
            height: 50vh;
            background: #0a0a0a;
            border-top: 1px solid #222;
            display: flex;
            flex-direction: column;
        }

        .messages-box {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            font-family: 'Inter', sans-serif;
            display: flex;
            flex-direction: column;
            gap: 15px;
        }

        .msg { max-width: 80%; padding: 10px 15px; border-radius: 12px; font-size: 0.95rem; line-height: 1.4; }
        .msg.user { align-self: flex-end; background: #222; color: #ccc; border: 1px solid #333; }
        .msg.ai { align-self: flex-start; background: rgba(0, 255, 136, 0.1); color: #fff; border: 1px solid var(--accent-color); }
        .msg.ai.nepali { background: rgba(255, 0, 85, 0.1); border-color: var(--nepali-color); }

        /* INPUT BAR */
        .input-area {
            padding: 15px;
            background: #000;
            display: flex;
            gap: 10px;
            align-items: center;
            border-top: 1px solid #222;
        }

        .chat-input {
            flex: 1;
            background: var(--input-bg);
            border: 1px solid #333;
            color: #fff;
            padding: 12px 15px;
            border-radius: 25px;
            outline: none;
            font-size: 1rem;
        }
        .chat-input:focus { border-color: #555; }

        .action-btn {
            width: 50px; height: 50px;
            border-radius: 50%;
            border: none;
            cursor: pointer;
            display: flex; justify-content: center; align-items: center;
            font-size: 1.2rem;
            transition: 0.2s;
        }
        
        .send-btn { background: #222; color: var(--accent-color); }
        .send-btn:hover { background: #333; }

        .mic-btn { background: #222; color: #fff; border: 1px solid #444; }
        .mic-btn.active { background: #fff; color: #000; animation: pulse-red 1.5s infinite; }
        @keyframes pulse-red { 0% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(255, 255, 255, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 255, 255, 0); } }

    </style>
</head>
<body>

    <div class="hud">
        <div class="status-badge">ADARSHA HYBRID</div>
        <div class="lang-switch">
            <button class="lang-btn active en" onclick="setLang('en')">ENG</button>
            <button class="lang-btn np" onclick="setLang('np')">नेपाली</button>
        </div>
    </div>

    <div class="visualizer-container">
        <div class="core" id="core">
            <div class="core-inner"></div>
        </div>
    </div>

    <div class="chat-container">
        <div class="messages-box" id="msgBox">
            <div class="msg ai">System Online. How can I help?</div>
        </div>
        
        <div class="input-area">
            <button class="action-btn mic-btn" id="micBtn" onclick="toggleMic()">
                <i class="fas fa-microphone"></i>
            </button>
            <input type="text" class="chat-input" id="chatInput" placeholder="Type a message..." onkeypress="handleEnter(event)">
            <button class="action-btn send-btn" onclick="sendText()">
                <i class="fas fa-paper-plane"></i>
            </button>
        </div>
    </div>

    <script>
        const core = document.getElementById('core');
        const msgBox = document.getElementById('msgBox');
        const micBtn = document.getElementById('micBtn');
        const chatInput = document.getElementById('chatInput');
        const btns = document.querySelectorAll('.lang-btn');

        let recognition;
        let isListening = false;
        let wasListeningBeforeSpeaking = false; // Memory state
        let currentLang = 'en-US'; 
        let synth = window.speechSynthesis;

        // Initialize Speech Recognition
        function initRecognition() {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                recognition = new SpeechRecognition();
                recognition.continuous = false; // We handle restarting manually
                recognition.interimResults = false;
                recognition.lang = currentLang;

                recognition.onstart = () => {
                    isListening = true;
                    core.classList.add('listening');
                    micBtn.classList.add('active');
                };

                recognition.onend = () => {
                    isListening = false;
                    core.classList.remove('listening');
                    micBtn.classList.remove('active');
                    // Note: We don't auto-restart here immediately to avoid loops, 
                    // unless handled by the speak function logic.
                };

                recognition.onresult = async (event) => {
                    const text = event.results[0][0].transcript;
                    addMessage(text, 'user');
                    processQuery(text);
                };
            } else {
                addMessage("Browser does not support voice API.", 'ai');
            }
        }

        function setLang(lang) {
            btns.forEach(b => b.classList.remove('active'));
            if(lang === 'en') {
                document.querySelector('.en').classList.add('active');
                currentLang = 'en-US';
                core.classList.remove('nepali-mode');
            } else {
                document.querySelector('.np').classList.add('active');
                currentLang = 'ne-NP'; 
                core.classList.add('nepali-mode');
            }
            if(recognition) {
                recognition.stop();
                initRecognition();
            }
        }

        function toggleMic() {
            if (isListening) {
                recognition.stop();
            } else {
                try { recognition.start(); } catch(e) { initRecognition(); recognition.start(); }
            }
        }

        function handleEnter(e) {
            if (e.key === 'Enter') sendText();
        }

        function sendText() {
            const text = chatInput.value.trim();
            if(!text) return;
            addMessage(text, 'user');
            chatInput.value = '';
            processQuery(text);
        }

        function addMessage(text, sender) {
            const div = document.createElement('div');
            div.classList.add('msg', sender);
            if(sender === 'ai' && currentLang === 'ne-NP') div.classList.add('nepali');
            div.innerText = text;
            msgBox.appendChild(div);
            msgBox.scrollTop = msgBox.scrollHeight;
        }

        async function processQuery(text) {
            core.classList.add('processing');
            
            // 1. Temporarily stop listening so we don't hear the response processing or noise
            if(isListening) {
                wasListeningBeforeSpeaking = true;
                recognition.stop();
            } else {
                wasListeningBeforeSpeaking = false;
            }

            try {
                const res = await fetch('/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ message: text, lang: currentLang })
                });
                const data = await res.json();
                
                core.classList.remove('processing');
                addMessage(data.response, 'ai');
                speak(data.response);

            } catch (e) {
                console.error(e);
                addMessage("Connection Error.", 'ai');
                core.classList.remove('processing');
            }
        }

        function speak(text) {
            synth.cancel(); // Stop any previous speech
            const utterance = new SpeechSynthesisUtterance(text);
            
            // Voice Selection Logic
            const voices = synth.getVoices();
            let selectedVoice = null;

            if (currentLang === 'ne-NP') {
                selectedVoice = voices.find(v => v.lang.includes('ne')) || 
                                voices.find(v => v.lang.includes('hi')) || voices[0];
                utterance.rate = 1.0; 
            } else {
                selectedVoice = voices.find(v => v.lang === 'en-IN') || 
                                voices.find(v => v.lang.includes('en')) || voices[0];
                utterance.rate = 1.1; 
            }
            if(selectedVoice) utterance.voice = selectedVoice;
            
            // SMART LOGIC: When AI starts speaking, ensure Mic is OFF
            utterance.onstart = () => {
                if(isListening) recognition.stop();
            };

            // SMART LOGIC: When AI finishes, Auto-Turn Mic ON (if it was on before or user used voice)
            utterance.onend = () => {
                // If user was using voice mode, turn mic back on for natural conversation
                // OR if you want it to ALWAYS turn on after a reply, just use toggleMic()
                if (wasListeningBeforeSpeaking || document.activeElement !== chatInput) {
                   try { recognition.start(); } catch(e) {}
                }
            };

            synth.speak(utterance);
        }

        // Init
        initRecognition();
    </script>
</body>
</html>
"""

# ==================================================================================
# 5. BACKEND LOGIC
# ==================================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        raw_input = data.get('message', '').strip()
        lang = data.get('lang', 'en-US') 
        
        if not raw_input:
            return jsonify({'success': False, 'response': "..."})

        # 1. NOISE CANCELLATION
        clean_input = noise_filter.clean(raw_input)
        print(f" [{lang}] Raw: '{raw_input}' -> Clean: '{clean_input}'")

        # 2. PERCEPTION
        perception = nlp_brain.analyze(clean_input, lang)

        if lang == 'ne-NP':
            perception['language_instruction'] = "Response MUST be in NEPALI language (Devanagari script)."

        response_text = ""
        
        if rag_pipeline:
            # 3. PIPELINE
            response = rag_pipeline.chat(
                user_input=clean_input, 
                is_voice=True, 
                perception_data=perception 
            )
            response_text = response.get('answer', "Error in Logic Core.")
        else:
            # Simulation
            if lang == 'ne-NP':
                response_text = f"मैले बुझें: {clean_input}. (Simulated Response)"
            else:
                response_text = f"I heard: {clean_input}. (Simulated Response)"

        return jsonify({'success': True, 'response': response_text})

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'response': "System Critical Failure."})

if __name__ == '__main__':
    print(" Server running on http://0.0.0.0:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)