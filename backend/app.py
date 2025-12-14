"""
ADARSHA AI - GEMINI LIVE-STYLE VOICE SERVER
Real-time WebSocket-based voice conversation with <1s response time
"""

import os
import sys
import importlib.util
import json
import time
from flask import Flask, request, render_template_string, Response, stream_with_context, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# ==================================================================================
# CONFIGURATION
# ==================================================================================

current_dir = os.path.dirname(os.path.abspath(__file__))
rag_file_path = os.path.join(current_dir, "pipeline.py")

rag_pipeline = None
sessions = {}

print("\n" + "="*70)
print(" ADARSHA AI - GEMINI LIVE-STYLE SERVER")
print(" Sub-second Response | Barge-in Support | Full-Duplex")
print("="*70)

# Load RAG Pipeline
if os.path.exists(rag_file_path):
    try:
        spec = importlib.util.spec_from_file_location("pipeline", rag_file_path)
        rag_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rag_module)
        if hasattr(rag_module, 'get_chatbot'):
            rag_pipeline = rag_module.get_chatbot()
            print(" [SUCCESS] RAG Pipeline loaded with streaming support")
    except Exception as e:
        print(f" [ERROR] Pipeline load failed: {e}")
else:
    print(" [INFO] pipeline.py not found.")

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', ping_timeout=60)

# ==================================================================================
# GEMINI LIVE-STYLE FRONTEND
# ==================================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Adarsha AI - Live Voice</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
    <style>
        :root {
            --bg: #0a0a0a;
            --surface: #111;
            --accent: #00ff88;
            --accent-glow: rgba(0,255,136,0.4);
            --user-msg: #1a5fb4;
            --ai-msg: #1a1a1a;
            --text: #e8e8e8;
            --text-dim: #666;
            --warning: #ff6b6b;
            --processing: #ffd93d;
            --speaking: #6bcfff;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: var(--bg);
            color: var(--text);
            height: 100vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        /* HEADER */
        .header {
            background: rgba(17, 17, 17, 0.95);
            padding: 14px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid #222;
            backdrop-filter: blur(20px);
            z-index: 100;
        }

        .brand {
            font-weight: 700;
            font-size: 1.15rem;
            color: var(--accent);
            display: flex;
            align-items: center;
            gap: 10px;
            letter-spacing: -0.5px;
        }
        .brand i { font-size: 1.4rem; }

        .connection-status {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.75rem;
            color: var(--text-dim);
        }
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--warning);
            transition: background 0.3s;
        }
        .status-indicator.connected { background: var(--accent); animation: pulse 2s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

        .lang-toggle {
            display: flex;
            background: #1a1a1a;
            border-radius: 10px;
            padding: 4px;
        }
        .lang-btn {
            background: transparent;
            border: none;
            color: #555;
            padding: 8px 16px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 600;
            transition: all 0.2s;
        }
        .lang-btn:hover { color: #999; }
        .lang-btn.active { background: var(--accent); color: #000; }

        /* CHAT CONTAINER */
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            scroll-behavior: smooth;
        }

        .message {
            max-width: 82%;
            padding: 14px 18px;
            border-radius: 20px;
            font-size: 0.95rem;
            line-height: 1.65;
            animation: msgSlide 0.25s ease-out;
            position: relative;
        }
        @keyframes msgSlide { 
            from { opacity: 0; transform: translateY(10px); } 
            to { opacity: 1; transform: translateY(0); } 
        }

        .message.user {
            align-self: flex-end;
            background: linear-gradient(135deg, #1a5fb4, #1e88e5);
            color: #fff;
            border-bottom-right-radius: 6px;
        }

        .message.ai {
            align-self: flex-start;
            background: var(--ai-msg);
            color: var(--text);
            border-bottom-left-radius: 6px;
            border: 1px solid #2a2a2a;
        }

        .message.ai.streaming {
            border-color: var(--accent);
        }
        .message.ai.streaming::after {
            content: '▊';
            animation: cursorBlink 0.6s infinite;
            color: var(--accent);
            margin-left: 2px;
        }
        @keyframes cursorBlink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }

        .message.ai.speaking {
            border-color: var(--speaking);
            box-shadow: 0 0 20px rgba(107, 207, 255, 0.2);
        }

        /* TYPING INDICATOR */
        .typing-indicator {
            display: flex;
            gap: 5px;
            padding: 15px 20px;
            align-items: center;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: var(--accent);
            border-radius: 50%;
            animation: typingBounce 1.4s infinite ease-in-out;
        }
        .typing-indicator span:nth-child(1) { animation-delay: 0s; }
        .typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
        .typing-indicator span:nth-child(3) { animation-delay: 0.4s; }
        @keyframes typingBounce {
            0%, 80%, 100% { transform: scale(0.7); opacity: 0.5; }
            40% { transform: scale(1); opacity: 1; }
        }

        /* INPUT AREA */
        .input-area {
            background: var(--surface);
            padding: 16px 20px;
            border-top: 1px solid #222;
            display: flex;
            gap: 12px;
            align-items: center;
        }

        .text-input {
            flex: 1;
            padding: 14px 24px;
            background: #0d0d0d;
            border: 1px solid #333;
            color: #fff;
            border-radius: 28px;
            outline: none;
            font-size: 1rem;
            transition: all 0.2s;
        }
        .text-input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }
        .text-input::placeholder { color: #444; }

        .action-btn {
            width: 54px;
            height: 54px;
            border-radius: 50%;
            border: none;
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 1.25rem;
        }
        .action-btn:disabled { opacity: 0.4; cursor: not-allowed; }

        .voice-btn {
            background: rgba(0,255,136,0.1);
            color: var(--accent);
            border: 2px solid transparent;
        }
        .voice-btn:hover:not(:disabled) { 
            border-color: var(--accent);
            background: rgba(0,255,136,0.2);
            transform: scale(1.05);
        }

        .send-btn {
            background: var(--accent);
            color: #000;
        }
        .send-btn:hover:not(:disabled) { 
            background: #00e67a;
            transform: scale(1.05);
        }

        /* ================================================================
           VOICE OVERLAY - GEMINI LIVE STYLE
           ================================================================ */
        .voice-overlay {
            position: fixed;
            inset: 0;
            background: radial-gradient(ellipse at 50% 30%, #0d1117 0%, #000 100%);
            z-index: 1000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.4s ease;
        }
        .voice-overlay.active {
            opacity: 1;
            pointer-events: all;
        }

        /* Central Orb Container */
        .orb-container {
            position: relative;
            width: 300px;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Ambient Rings */
        .ambient-ring {
            position: absolute;
            border: 1px solid rgba(255,255,255,0.05);
            border-radius: 50%;
            animation: ringPulse 4s infinite ease-out;
        }
        .ambient-ring:nth-child(1) { width: 200px; height: 200px; animation-delay: 0s; }
        .ambient-ring:nth-child(2) { width: 250px; height: 250px; animation-delay: 1s; }
        .ambient-ring:nth-child(3) { width: 300px; height: 300px; animation-delay: 2s; }
        @keyframes ringPulse {
            0% { transform: scale(0.9); opacity: 0.3; }
            100% { transform: scale(1.3); opacity: 0; }
        }

        /* The Main Orb */
        .orb {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            position: relative;
            z-index: 10;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
        }

        /* ORB STATES */
        .orb.idle {
            background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
            box-shadow: 
                0 0 60px rgba(255,255,255,0.05),
                inset 0 0 30px rgba(255,255,255,0.02);
            animation: idleBreath 4s infinite ease-in-out;
        }
        @keyframes idleBreath {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.03); }
        }

        .orb.listening {
            background: linear-gradient(145deg, #ffffff, #e0e0e0);
            box-shadow: 
                0 0 80px rgba(255,255,255,0.4),
                0 0 120px rgba(255,255,255,0.2);
            animation: none;
        }

        .orb.listening.active {
            transform: scale(1.2);
            background: linear-gradient(145deg, var(--accent), #00cc6a);
            box-shadow: 
                0 0 100px var(--accent-glow),
                0 0 150px rgba(0,255,136,0.3);
        }

        .orb.processing {
            background: linear-gradient(145deg, var(--processing), #ffb347);
            box-shadow: 0 0 80px rgba(255,217,61,0.4);
            animation: processingPulse 0.8s infinite ease-in-out;
        }
        @keyframes processingPulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
        }

        .orb.speaking {
            background: linear-gradient(145deg, var(--speaking), #4fc3f7);
            box-shadow: 0 0 80px rgba(107,207,255,0.5);
            animation: speakingWave 1s infinite ease-in-out;
        }
        @keyframes speakingWave {
            0%, 100% { transform: scale(1); border-radius: 50%; }
            25% { transform: scale(1.05) rotate(2deg); border-radius: 48% 52% 52% 48%; }
            50% { transform: scale(1.1); border-radius: 52% 48% 48% 52%; }
            75% { transform: scale(1.05) rotate(-2deg); border-radius: 48% 52% 52% 48%; }
        }

        .orb.error {
            background: linear-gradient(145deg, var(--warning), #ff5252);
            box-shadow: 0 0 60px rgba(255,107,107,0.4);
            animation: errorShake 0.5s ease-in-out;
        }
        @keyframes errorShake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-5px); }
            75% { transform: translateX(5px); }
        }

        /* Voice Status Text */
        .voice-status {
            margin-top: 50px;
            font-size: 0.85rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #555;
            font-weight: 600;
            transition: all 0.3s;
        }
        .voice-status.active { color: var(--accent); }

        /* Live Transcript */
        .live-transcript {
            margin-top: 25px;
            max-width: 85%;
            text-align: center;
            font-size: 1.15rem;
            color: #888;
            min-height: 60px;
            line-height: 1.6;
            transition: color 0.3s;
        }
        .live-transcript.user-speaking { color: #fff; }
        .live-transcript.ai-speaking { color: var(--speaking); }

        /* Response Time Display */
        .response-time {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 0.7rem;
            color: #444;
            font-family: 'SF Mono', monospace;
        }
        .response-time.fast { color: var(--accent); }
        .response-time.medium { color: var(--processing); }
        .response-time.slow { color: var(--warning); }

        /* Close Button */
        .close-voice-btn {
            position: absolute;
            bottom: 50px;
            width: 60px;
            height: 60px;
            border-radius: 50%;
            background: rgba(255,255,255,0.03);
            border: 1px solid #333;
            color: #666;
            font-size: 1.4rem;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            transition: all 0.3s;
        }
        .close-voice-btn:hover {
            background: var(--warning);
            border-color: var(--warning);
            color: #fff;
            transform: rotate(90deg);
        }

        /* Interrupt Hint */
        .interrupt-hint {
            position: absolute;
            bottom: 130px;
            font-size: 0.7rem;
            color: #444;
            letter-spacing: 1px;
        }

        /* Waveform Visualization */
        .waveform {
            position: absolute;
            bottom: 180px;
            display: flex;
            gap: 3px;
            align-items: center;
            height: 40px;
            opacity: 0;
            transition: opacity 0.3s;
        }
        .waveform.active { opacity: 1; }
        .waveform-bar {
            width: 4px;
            background: var(--accent);
            border-radius: 2px;
            animation: wave 0.8s infinite ease-in-out;
        }
        .waveform-bar:nth-child(1) { animation-delay: 0s; }
        .waveform-bar:nth-child(2) { animation-delay: 0.1s; }
        .waveform-bar:nth-child(3) { animation-delay: 0.2s; }
        .waveform-bar:nth-child(4) { animation-delay: 0.3s; }
        .waveform-bar:nth-child(5) { animation-delay: 0.4s; }
        .waveform-bar:nth-child(6) { animation-delay: 0.3s; }
        .waveform-bar:nth-child(7) { animation-delay: 0.2s; }
        .waveform-bar:nth-child(8) { animation-delay: 0.1s; }
        .waveform-bar:nth-child(9) { animation-delay: 0s; }
        @keyframes wave {
            0%, 100% { height: 8px; }
            50% { height: 35px; }
        }

        /* Scrollbar */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #444; }

        /* Mobile Responsive */
        @media (max-width: 600px) {
            .header { padding: 12px 16px; }
            .brand { font-size: 1rem; }
            .message { max-width: 90%; padding: 12px 16px; font-size: 0.9rem; }
            .orb { width: 120px; height: 120px; }
            .orb-container { width: 260px; height: 260px; }
        }
    </style>
</head>
<body>

    <!-- HEADER -->
    <div class="header">
        <div class="brand">
            <i class="fas fa-atom"></i>
            <span>ADARSHA AI</span>
        </div>
        <div class="connection-status">
            <div class="status-indicator" id="statusIndicator"></div>
            <span id="statusText">Connecting...</span>
        </div>
        <div class="lang-toggle">
            <button class="lang-btn active" id="btnEn" onclick="setLanguage('en')">EN</button>
            <button class="lang-btn" id="btnNp" onclick="setLanguage('np')">नेपाली</button>
        </div>
    </div>

    <!-- CHAT CONTAINER -->
    <div class="chat-container" id="chatContainer">
        <div class="message ai">Hello! I'm Adarsha AI. How can I assist you today?</div>
    </div>

    <!-- INPUT AREA -->
    <div class="input-area">
        <button class="action-btn voice-btn" id="voiceBtn" onclick="openVoiceMode()" title="Voice Mode">
            <i class="fas fa-microphone"></i>
        </button>
        <input type="text" class="text-input" id="textInput" placeholder="Type your message..." 
               onkeypress="handleKeyPress(event)" autocomplete="off">
        <button class="action-btn send-btn" id="sendBtn" onclick="sendTextMessage()">
            <i class="fas fa-arrow-up"></i>
        </button>
    </div>

    <!-- VOICE OVERLAY -->
    <div class="voice-overlay" id="voiceOverlay">
        <div class="response-time" id="responseTime"></div>
        
        <div class="orb-container">
            <div class="ambient-ring"></div>
            <div class="ambient-ring"></div>
            <div class="ambient-ring"></div>
            <div class="orb idle" id="orb" onclick="handleOrbClick()"></div>
        </div>

        <div class="voice-status" id="voiceStatus">TAP TO START</div>
        <div class="live-transcript" id="liveTranscript"></div>

        <div class="waveform" id="waveform">
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
        </div>

        <div class="interrupt-hint" id="interruptHint">SPEAK TO INTERRUPT</div>

        <button class="close-voice-btn" onclick="closeVoiceMode()">
            <i class="fas fa-times"></i>
        </button>
    </div>

<script>
// =====================================================================
// GEMINI LIVE-STYLE VOICE ENGINE
// =====================================================================

// Configuration
const CONFIG = {
    silenceTimeout: 1200,      // 1.2s silence = end of speech
    minSpeechLength: 2,        // Minimum chars to process
    langEn: 'en-US',
    langNp: 'ne-NP',
    ttsRateEn: 1.08,
    ttsRateNp: 0.95,
    sentenceDelimiters: /[.!?।]+/g,
    maxHistoryDisplay: 50
};

// State
const STATE = {
    socket: null,
    isConnected: false,
    isVoiceMode: false,
    isListening: false,
    isProcessing: false,
    isSpeaking: false,
    currentLang: CONFIG.langEn,
    recognition: null,
    synth: window.speechSynthesis,
    currentUtterances: [],
    pendingSentences: [],
    finalTranscript: '',
    interimTranscript: '',
    silenceTimer: null,
    requestStartTime: null,
    currentAiMessage: null,
    fullResponse: ''
};

// DOM Elements
const DOM = {
    chatContainer: document.getElementById('chatContainer'),
    textInput: document.getElementById('textInput'),
    voiceOverlay: document.getElementById('voiceOverlay'),
    orb: document.getElementById('orb'),
    voiceStatus: document.getElementById('voiceStatus'),
    liveTranscript: document.getElementById('liveTranscript'),
    responseTime: document.getElementById('responseTime'),
    waveform: document.getElementById('waveform'),
    interruptHint: document.getElementById('interruptHint'),
    statusIndicator: document.getElementById('statusIndicator'),
    statusText: document.getElementById('statusText')
};

// =====================================================================
// WEBSOCKET CONNECTION
// =====================================================================

function initSocket() {
    STATE.socket = io({
        transports: ['websocket'],
        upgrade: false,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: 10
    });

    STATE.socket.on('connect', () => {
        STATE.isConnected = true;
        updateConnectionStatus(true);
        console.log('[Socket] Connected');
    });

    STATE.socket.on('disconnect', () => {
        STATE.isConnected = false;
        updateConnectionStatus(false);
        console.log('[Socket] Disconnected');
    });

    // Streaming token response
    STATE.socket.on('token', (data) => {
        handleStreamToken(data.token);
    });

    // Stream complete
    STATE.socket.on('stream_end', (data) => {
        handleStreamEnd(data);
    });

    // Error handling
    STATE.socket.on('error', (data) => {
        console.error('[Socket Error]', data);
        setOrbState('error');
        setTimeout(() => {
            if (STATE.isVoiceMode) setOrbState('listening');
        }, 1000);
    });
}

function updateConnectionStatus(connected) {
    DOM.statusIndicator.classList.toggle('connected', connected);
    DOM.statusText.textContent = connected ? 'Connected' : 'Reconnecting...';
}

// =====================================================================
// SPEECH RECOGNITION (VAD + Continuous)
// =====================================================================

function initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert('Speech recognition not supported. Please use Chrome.');
        return;
    }

    STATE.recognition = new SpeechRecognition();
    STATE.recognition.continuous = true;
    STATE.recognition.interimResults = true;
    STATE.recognition.lang = STATE.currentLang;

    STATE.recognition.onstart = () => {
        STATE.isListening = true;
        if (STATE.isVoiceMode && !STATE.isProcessing && !STATE.isSpeaking) {
            setOrbState('listening');
            DOM.voiceStatus.textContent = 'LISTENING';
            DOM.voiceStatus.classList.add('active');
        }
    };

    STATE.recognition.onend = () => {
        STATE.isListening = false;
        // Auto-restart in voice mode
        if (STATE.isVoiceMode && !STATE.isProcessing) {
            setTimeout(startListening, 100);
        }
    };

    STATE.recognition.onerror = (e) => {
        console.log('[Recognition Error]', e.error);
        if (e.error === 'no-speech' && STATE.isVoiceMode) {
            setTimeout(startListening, 100);
        }
    };

    STATE.recognition.onresult = handleRecognitionResult;
}

function handleRecognitionResult(event) {
    if (!STATE.isVoiceMode || STATE.isProcessing) return;

    // BARGE-IN: If AI is speaking and user starts talking
    if (STATE.isSpeaking) {
        interruptAI();
    }

    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
            STATE.finalTranscript += transcript + ' ';
        } else {
            interim += transcript;
        }
    }

    STATE.interimTranscript = interim;
    
    // Update UI
    const displayText = (STATE.finalTranscript + interim).trim();
    DOM.liveTranscript.textContent = displayText;
    DOM.liveTranscript.classList.add('user-speaking');
    DOM.liveTranscript.classList.remove('ai-speaking');

    // Visual feedback
    if (displayText.length > 0) {
        DOM.orb.classList.add('active');
        DOM.waveform.classList.add('active');
    }

    // Silence detection (debounce)
    clearTimeout(STATE.silenceTimer);
    if (STATE.finalTranscript.trim().length >= CONFIG.minSpeechLength) {
        STATE.silenceTimer = setTimeout(commitUserSpeech, CONFIG.silenceTimeout);
    }
}

function commitUserSpeech() {
    const text = STATE.finalTranscript.trim();
    STATE.finalTranscript = '';
    STATE.interimTranscript = '';
    
    DOM.orb.classList.remove('active');
    DOM.waveform.classList.remove('active');

    if (!text) {
        setOrbState('listening');
        return;
    }

    // Stop recognition during processing
    STATE.recognition.stop();

    // Add to chat
    addMessage(text, 'user');
    
    // Send via WebSocket for streaming response
    sendVoiceQuery(text);
}

// =====================================================================
// BARGE-IN: INTERRUPT AI SPEECH
// =====================================================================

function interruptAI() {
    console.log('[Barge-in] User interrupted AI');
    
    // Stop all TTS
    STATE.synth.cancel();
    STATE.currentUtterances = [];
    STATE.pendingSentences = [];
    STATE.isSpeaking = false;

    // Visual feedback
    setOrbState('listening');
    DOM.voiceStatus.textContent = 'LISTENING';
    DOM.interruptHint.style.opacity = '0';

    // Stop processing flag
    STATE.isProcessing = false;

    // Clear current AI message streaming indicator
    if (STATE.currentAiMessage) {
        STATE.currentAiMessage.classList.remove('streaming', 'speaking');
    }
}

// =====================================================================
// QUERY PROCESSING
// =====================================================================

function sendVoiceQuery(text) {
    STATE.isProcessing = true;
    STATE.requestStartTime = performance.now();
    STATE.fullResponse = '';
    STATE.pendingSentences = [];

    setOrbState('processing');
    DOM.voiceStatus.textContent = 'THINKING';
    DOM.liveTranscript.textContent = '';
    DOM.responseTime.textContent = '';

    // Create AI message container
    STATE.currentAiMessage = document.createElement('div');
    STATE.currentAiMessage.className = 'message ai streaming';
    DOM.chatContainer.appendChild(STATE.currentAiMessage);
    scrollToBottom();

    // Send via WebSocket
    STATE.socket.emit('voice_query', {
        message: text,
        lang: STATE.currentLang,
        voice: true
    });
}

function sendTextMessage() {
    const text = DOM.textInput.value.trim();
    if (!text || STATE.isProcessing) return;

    DOM.textInput.value = '';
    addMessage(text, 'user');

    STATE.isProcessing = true;
    STATE.requestStartTime = performance.now();
    STATE.fullResponse = '';

    // Create AI message container
    STATE.currentAiMessage = document.createElement('div');
    STATE.currentAiMessage.className = 'message ai streaming';
    DOM.chatContainer.appendChild(STATE.currentAiMessage);
    scrollToBottom();

    // Send via WebSocket
    STATE.socket.emit('text_query', {
        message: text,
        lang: STATE.currentLang,
        voice: false
    });
}

// =====================================================================
// STREAMING TOKEN HANDLER
// =====================================================================

function handleStreamToken(token) {
    // Show response time on first token
    if (STATE.fullResponse === '' && STATE.requestStartTime) {
        const latency = Math.round(performance.now() - STATE.requestStartTime);
        showResponseTime(latency);
        
        // Start speaking mode
        if (STATE.isVoiceMode) {
            setOrbState('speaking');
            DOM.voiceStatus.textContent = 'SPEAKING';
            DOM.interruptHint.style.opacity = '1';
            DOM.liveTranscript.classList.remove('user-speaking');
            DOM.liveTranscript.classList.add('ai-speaking');
        }
    }

    STATE.fullResponse += token;

    // Update chat display
    if (STATE.currentAiMessage) {
        STATE.currentAiMessage.textContent = STATE.fullResponse;
        scrollToBottom();
    }

    // Update voice transcript
    if (STATE.isVoiceMode) {
        DOM.liveTranscript.textContent = STATE.fullResponse.slice(-150); // Last 150 chars
    }

    // Sentence-level TTS (speak as sentences complete)
    if (STATE.isVoiceMode) {
        checkAndSpeakSentences();
    }
}

function handleStreamEnd(data) {
    // Remove streaming indicator
    if (STATE.currentAiMessage) {
        STATE.currentAiMessage.classList.remove('streaming');
    }

    // Speak any remaining text
    if (STATE.isVoiceMode && STATE.fullResponse) {
        const remaining = STATE.fullResponse.replace(STATE.pendingSentences.join(''), '').trim();
        if (remaining) {
            speakText(remaining, true);
        }
    }

    // If not in voice mode, reset processing
    if (!STATE.isVoiceMode) {
        STATE.isProcessing = false;
        STATE.currentAiMessage = null;
    }
}

// =====================================================================
// SENTENCE-LEVEL STREAMING TTS
// =====================================================================

function checkAndSpeakSentences() {
    const sentences = STATE.fullResponse.split(CONFIG.sentenceDelimiters).filter(s => s.trim());
    const alreadySpoken = STATE.pendingSentences.length;
    
    // Speak new complete sentences
    for (let i = alreadySpoken; i < sentences.length - 1; i++) {
        const sentence = sentences[i].trim();
        if (sentence) {
            STATE.pendingSentences.push(sentence);
            speakText(sentence, false);
        }
    }
}

function speakText(text, isFinal = false) {
    const utterance = new SpeechSynthesisUtterance(cleanTextForSpeech(text));
    
    // Voice selection
    const voices = STATE.synth.getVoices();
    let voice = null;
    
    if (STATE.currentLang === CONFIG.langNp) {
        voice = voices.find(v => v.lang === 'ne-NP') ||
                voices.find(v => v.lang.includes('hi'));
        utterance.rate = CONFIG.ttsRateNp;
    } else {
        voice = voices.find(v => v.name.includes('Google') && v.lang.includes('en-IN')) ||
                voices.find(v => v.lang === 'en-IN') ||
                voices.find(v => v.lang.includes('en-US'));
        utterance.rate = CONFIG.ttsRateEn;
        utterance.pitch = 1.05;
    }
    
    if (voice) utterance.voice = voice;

    utterance.onstart = () => {
        STATE.isSpeaking = true;
        if (STATE.currentAiMessage) {
            STATE.currentAiMessage.classList.add('speaking');
        }
    };

    utterance.onend = () => {
        STATE.currentUtterances = STATE.currentUtterances.filter(u => u !== utterance);
        
        if (STATE.currentUtterances.length === 0 && isFinal) {
            STATE.isSpeaking = false;
            STATE.isProcessing = false;
            
            if (STATE.currentAiMessage) {
                STATE.currentAiMessage.classList.remove('speaking');
            }
            
            if (STATE.isVoiceMode) {
                DOM.liveTranscript.textContent = '';
                DOM.interruptHint.style.opacity = '0';
                setOrbState('listening');
                DOM.voiceStatus.textContent = 'LISTENING';
                setTimeout(startListening, 200);
            }
            
            STATE.currentAiMessage = null;
        }
    };

    STATE.currentUtterances.push(utterance);
    STATE.synth.speak(utterance);
}

function cleanTextForSpeech(text) {
    return text
        .replace(/\*+/g, '')
        .replace(/#+/g, '')
        .replace(/`/g, '')
        .replace(/\n+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();
}

// =====================================================================
// UI HELPERS
// =====================================================================

function setOrbState(state) {
    DOM.orb.className = 'orb ' + state;
}

function addMessage(text, sender) {
    const div = document.createElement('div');
    div.className = 'message ' + sender;
    div.textContent = text;
    DOM.chatContainer.appendChild(div);
    scrollToBottom();
    
    // Limit history
    while (DOM.chatContainer.children.length > CONFIG.maxHistoryDisplay) {
        DOM.chatContainer.removeChild(DOM.chatContainer.firstChild);
    }
}

function scrollToBottom() {
    DOM.chatContainer.scrollTop = DOM.chatContainer.scrollHeight;
}

function showResponseTime(ms) {
    DOM.responseTime.textContent = `${ms}ms`;
    DOM.responseTime.className = 'response-time ' + 
        (ms < 800 ? 'fast' : ms < 1500 ? 'medium' : 'slow');
}

function setLanguage(lang) {
    document.getElementById('btnEn').classList.toggle('active', lang === 'en');
    document.getElementById('btnNp').classList.toggle('active', lang === 'np');
    
    STATE.currentLang = (lang === 'np') ? CONFIG.langNp : CONFIG.langEn;
    
    if (STATE.recognition) {
        STATE.recognition.lang = STATE.currentLang;
        if (STATE.isVoiceMode && STATE.isListening) {
            STATE.recognition.stop();
            setTimeout(startListening, 200);
        }
    }
    
    const msg = (lang === 'np') ? 'नेपाली मोडमा स्विच गरियो।' : 'Switched to English mode.';
    addMessage(msg, 'ai');
}

function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendTextMessage();
    }
}

// =====================================================================
// VOICE MODE CONTROL
// =====================================================================

function openVoiceMode() {
    STATE.isVoiceMode = true;
    DOM.voiceOverlay.classList.add('active');
    setOrbState('idle');
    DOM.voiceStatus.textContent = 'TAP TO START';
    DOM.voiceStatus.classList.remove('active');
    DOM.liveTranscript.textContent = '';
    DOM.interruptHint.style.opacity = '0';
}

function handleOrbClick() {
    if (!STATE.isVoiceMode) return;
    
    if (STATE.isSpeaking) {
        interruptAI();
    } else if (!STATE.isProcessing && !STATE.isListening) {
        startListening();
    }
}

function startListening() {
    try {
        STATE.recognition.start();
    } catch (e) {
        console.log('[Recognition] Already started or error:', e);
    }
}

function closeVoiceMode() {
    STATE.isVoiceMode = false;
    STATE.isProcessing = false;
    STATE.isSpeaking = false;
    
    DOM.voiceOverlay.classList.remove('active');
    
    if (STATE.recognition) STATE.recognition.stop();
    STATE.synth.cancel();
    
    STATE.finalTranscript = '';
    STATE.interimTranscript = '';
    STATE.pendingSentences = [];
    STATE.currentUtterances = [];
}

// =====================================================================
// INITIALIZATION
// =====================================================================

function init() {
    initSocket();
    initRecognition();
    
    // Preload voices
    STATE.synth.getVoices();
    if (speechSynthesis.onvoiceschanged !== undefined) {
        speechSynthesis.onvoiceschanged = () => {
            console.log('[TTS] Voices loaded:', STATE.synth.getVoices().length);
        };
    }
}

// Start on load
init();

</script>
</body>
</html>
"""

# ==================================================================================
# WEBSOCKET EVENT HANDLERS
# ==================================================================================

@socketio.on('connect')
def handle_connect():
    print(f'[WebSocket] Client connected: {request.sid}')
    sessions[request.sid] = []


@socketio.on('disconnect')
def handle_disconnect():
    print(f'[WebSocket] Client disconnected: {request.sid}')
    if request.sid in sessions:
        del sessions[request.sid]


@socketio.on('voice_query')
def handle_voice_query(data):
    """Handle voice queries with streaming response"""
    handle_query(data, is_voice=True)


@socketio.on('text_query')  
def handle_text_query(data):
    """Handle text queries with streaming response"""
    handle_query(data, is_voice=False)


def handle_query(data, is_voice):
    """Common handler for both voice and text queries"""
    user_input = data.get('message', '').strip()
    lang = data.get('lang', 'en-US')
    session_id = request.sid
    
    if not user_input:
        emit('error', {'message': 'Empty input'})
        return
    
    # Get or create session history
    if session_id not in sessions:
        sessions[session_id] = []
    
    perception = {
        'language': lang,
        'history': sessions[session_id][-10:]
    }
    
    try:
        if rag_pipeline:
            # Stream tokens
            full_response = ""
            for token in rag_pipeline.chat_stream(user_input, is_voice=is_voice, perception_data=perception):
                full_response += token
                emit('token', {'token': token})
                socketio.sleep(0)  # Allow other events to process
            
            # Update session history
            sessions[session_id].append({'role': 'user', 'content': user_input})
            sessions[session_id].append({'role': 'assistant', 'content': full_response})
            
            # Limit history
            if len(sessions[session_id]) > 20:
                sessions[session_id] = sessions[session_id][-20:]
            
            emit('stream_end', {'success': True})
        else:
            emit('token', {'token': 'Pipeline not loaded.'})
            emit('stream_end', {'success': False})
            
    except Exception as e:
        print(f'[Query Error] {e}')
        emit('error', {'message': str(e)})
        emit('stream_end', {'success': False})


# ==================================================================================
# HTTP ROUTES (Fallback)
# ==================================================================================

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'pipeline': rag_pipeline is not None,
        'websocket': True
    })


# ==================================================================================
# MAIN
# ==================================================================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print(" Server: http://0.0.0.0:5000")
    print(" WebSocket: Enabled")
    print(" Mode: Gemini Live-Style")
    print("="*50 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)