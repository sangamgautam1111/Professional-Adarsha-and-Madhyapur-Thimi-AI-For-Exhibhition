"""
ADARSHA AI - GEMINI LIVE-STYLE VOICE SERVER
Version 3.0 - Enhanced Voice Support with Human-like TTS
Fixed: Spacing issues, natural voice accent, fast responses
"""

import os
import sys
import importlib.util
import json
import time
import textwrap
from flask import Flask, request, render_template_string, jsonify
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
print(" ADARSHA AI - GEMINI LIVE-STYLE SERVER v3.0")
print(" Enhanced Voice Support | Human-like TTS | Fast Response")
print("="*70)

# Load RAG Pipeline
if os.path.exists(rag_file_path):
    try:
        spec = importlib.util.spec_from_file_location("pipeline", rag_file_path)
        rag_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rag_module)
        if hasattr(rag_module, 'get_chatbot'):
            rag_pipeline = rag_module.get_chatbot()
            print(" [SUCCESS] RAG Pipeline loaded with voice support")
    except Exception as e:
        print(f" [ERROR] Pipeline load failed: {e}")
        import traceback
        traceback.print_exc()
else:
    print(" [INFO] pipeline.py not found.")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode='threading',
    ping_timeout=120,
    ping_interval=25
)

# ==================================================================================
# CLI BUBBLE UI
# ==================================================================================
def print_bubble(role, message, response_time=None, is_voice=False):
    """Print beautiful CLI bubbles"""
    width = 70
    mode_indicator = "🎤" if is_voice else "📝"
    
    if role == "user":
        icon = "👤"
        color = "\033[94m"
        border_top = "┌" + "─" * (width - 2) + "┐"
        border_bot = "└" + "─" * (width - 2) + "┘"
    else:
        icon = "🤖"
        color = "\033[92m"
        border_top = "╭" + "─" * (width - 2) + "╮"
        border_bot = "╰" + "─" * (width - 2) + "╯"
    
    reset = "\033[0m"
    wrapped = textwrap.fill(message, width=width-6)
    lines = wrapped.split('\n')
    
    print(f"\n{color}{border_top}{reset}")
    print(f"{color}│{reset} {icon} {mode_indicator} {role.upper():<{width-9}}{color}│{reset}")
    print(f"{color}│{reset}{' ' * (width-2)}{color}│{reset}")
    
    for line in lines:
        print(f"{color}│{reset}  {line:<{width-5}}{color}│{reset}")
    
    if response_time:
        time_str = f"⚡ {response_time}ms"
        print(f"{color}│{reset}  {time_str:<{width-5}}{color}│{reset}")
    
    print(f"{color}{border_bot}{reset}")

# ==================================================================================
# HTML TEMPLATE - ENHANCED VOICE SUPPORT WITH HUMAN-LIKE TTS
# ==================================================================================
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Adarsha AI - Live Voice</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
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
        .status-indicator.connected { 
            background: var(--accent); 
            animation: pulse 2s infinite; 
        }
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
            white-space: pre-wrap;
            word-wrap: break-word;
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

        /* VOICE OVERLAY */
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

        .orb-container {
            position: relative;
            width: 300px;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

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

        .orb {
            width: 140px;
            height: 140px;
            border-radius: 50%;
            position: relative;
            z-index: 10;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
        }

        .orb.idle {
            background: linear-gradient(145deg, #2a2a2a, #1a1a1a);
            box-shadow: 0 0 60px rgba(255,255,255,0.05);
            animation: idleBreath 4s infinite ease-in-out;
        }
        @keyframes idleBreath {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.03); }
        }

        .orb.listening {
            background: linear-gradient(145deg, #ffffff, #e0e0e0);
            box-shadow: 0 0 80px rgba(255,255,255,0.4);
        }

        .orb.listening.active {
            transform: scale(1.2);
            background: linear-gradient(145deg, var(--accent), #00cc6a);
            box-shadow: 0 0 100px var(--accent-glow);
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
            25% { transform: scale(1.05); border-radius: 48% 52% 52% 48%; }
            50% { transform: scale(1.1); border-radius: 52% 48% 48% 52%; }
            75% { transform: scale(1.05); border-radius: 48% 52% 52% 48%; }
        }

        .orb.error {
            background: linear-gradient(145deg, var(--warning), #ff5252);
            box-shadow: 0 0 60px rgba(255,107,107,0.4);
        }

        .voice-status {
            margin-top: 50px;
            font-size: 0.85rem;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: #555;
            font-weight: 600;
        }
        .voice-status.active { color: var(--accent); }

        .live-transcript {
            margin-top: 25px;
            max-width: 85%;
            text-align: center;
            font-size: 1.15rem;
            color: #888;
            min-height: 60px;
            line-height: 1.6;
        }
        .live-transcript.user-speaking { color: #fff; }
        .live-transcript.ai-speaking { color: var(--speaking); }

        .response-time {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 0.75rem;
            color: #444;
            font-family: monospace;
        }
        .response-time.fast { color: var(--accent); }
        .response-time.medium { color: var(--processing); }
        .response-time.slow { color: var(--warning); }

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

        .interrupt-hint {
            position: absolute;
            bottom: 130px;
            font-size: 0.7rem;
            color: #444;
            letter-spacing: 1px;
            opacity: 0;
        }

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

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 3px; }

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
            <button class="lang-btn active" id="btnEn">EN</button>
            <button class="lang-btn" id="btnNp">नेपाली</button>
        </div>
    </div>

    <div class="chat-container" id="chatContainer">
        <div class="message ai">Hello! I am Adarsha AI, your intelligent assistant for Adarsha Secondary School. How can I help you today? You can type your question or click the microphone to speak with me.</div>
    </div>

    <div class="input-area">
        <button class="action-btn voice-btn" id="voiceBtn" title="Voice Mode">
            <i class="fas fa-microphone"></i>
        </button>
        <input type="text" class="text-input" id="textInput" placeholder="Type your message..." autocomplete="off">
        <button class="action-btn send-btn" id="sendBtn">
            <i class="fas fa-arrow-up"></i>
        </button>
    </div>

    <div class="voice-overlay" id="voiceOverlay">
        <div class="response-time" id="responseTime"></div>
        
        <div class="orb-container">
            <div class="ambient-ring"></div>
            <div class="ambient-ring"></div>
            <div class="ambient-ring"></div>
            <div class="orb idle" id="orb"></div>
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

        <button class="close-voice-btn" id="closeVoiceBtn">
            <i class="fas fa-times"></i>
        </button>
    </div>

<script>
(function() {
    'use strict';
    
    // =====================================================================
    // CONFIGURATION - OPTIMIZED FOR HUMAN-LIKE VOICE
    // =====================================================================
    const CONFIG = {
        silenceTimeout: 1200,        // Faster response after user stops speaking
        minSpeechLength: 2,
        langEn: 'en-US',
        langNp: 'ne-NP',
        
        // TTS Settings for natural human-like voice
        ttsSettings: {
            en: {
                rate: 0.92,          // Slightly slower for clarity
                pitch: 1.0,          // Natural pitch
                volume: 1.0
            },
            np: {
                rate: 0.85,
                pitch: 1.0,
                volume: 1.0
            }
        },
        
        maxHistory: 50,
        sentenceEndPattern: /[.!?।]+\s*/,
        
        // Voice preferences (in order of priority)
        preferredVoices: {
            en: [
                'Google UK English Female',
                'Google UK English Male', 
                'Google US English',
                'Microsoft Zira',
                'Microsoft David',
                'Samantha',
                'Karen',
                'Daniel'
            ],
            np: [
                'Google हिन्दी',
                'Microsoft Hemant',
                'hi-IN'
            ]
        }
    };
    
    // =====================================================================
    // STATE
    // =====================================================================
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
        utteranceQueue: [],
        finalTranscript: '',
        silenceTimer: null,
        requestStartTime: null,
        currentAiMessage: null,
        fullResponse: '',
        spokenLength: 0,
        voices: [],
        selectedVoice: null
    };
    
    // =====================================================================
    // DOM ELEMENTS
    // =====================================================================
    const DOM = {
        chatContainer: document.getElementById('chatContainer'),
        textInput: document.getElementById('textInput'),
        sendBtn: document.getElementById('sendBtn'),
        voiceBtn: document.getElementById('voiceBtn'),
        voiceOverlay: document.getElementById('voiceOverlay'),
        orb: document.getElementById('orb'),
        voiceStatus: document.getElementById('voiceStatus'),
        liveTranscript: document.getElementById('liveTranscript'),
        responseTime: document.getElementById('responseTime'),
        waveform: document.getElementById('waveform'),
        interruptHint: document.getElementById('interruptHint'),
        statusIndicator: document.getElementById('statusIndicator'),
        statusText: document.getElementById('statusText'),
        closeVoiceBtn: document.getElementById('closeVoiceBtn'),
        btnEn: document.getElementById('btnEn'),
        btnNp: document.getElementById('btnNp')
    };
    
    // =====================================================================
    // VOICE SELECTION - GET BEST HUMAN-LIKE VOICE
    // =====================================================================
    function selectBestVoice(lang) {
        const isNepali = lang === CONFIG.langNp;
        const preferredList = isNepali ? CONFIG.preferredVoices.np : CONFIG.preferredVoices.en;
        
        // Try to find a preferred voice
        for (const preferred of preferredList) {
            const voice = STATE.voices.find(v => 
                v.name.includes(preferred) || v.lang.includes(preferred)
            );
            if (voice) {
                console.log('[TTS] Selected voice:', voice.name);
                return voice;
            }
        }
        
        // Fallback: find any English/Hindi voice
        if (isNepali) {
            return STATE.voices.find(v => v.lang.includes('hi')) ||
                   STATE.voices.find(v => v.lang.includes('en'));
        } else {
            return STATE.voices.find(v => v.lang.includes('en-US')) ||
                   STATE.voices.find(v => v.lang.includes('en-GB')) ||
                   STATE.voices.find(v => v.lang.includes('en'));
        }
    }
    
    function loadVoices() {
        STATE.voices = STATE.synth.getVoices();
        if (STATE.voices.length > 0) {
            STATE.selectedVoice = selectBestVoice(STATE.currentLang);
            console.log('[TTS] Loaded', STATE.voices.length, 'voices');
        }
    }
    
    // =====================================================================
    // SOCKET CONNECTION
    // =====================================================================
    function initSocket() {
        console.log('[Socket] Initializing...');
        
        STATE.socket = io({
            transports: ['polling', 'websocket'],
            upgrade: true,
            reconnection: true,
            reconnectionDelay: 500,
            reconnectionAttempts: 10,
            timeout: 15000
        });
        
        STATE.socket.on('connect', function() {
            STATE.isConnected = true;
            updateConnectionStatus(true);
            console.log('[Socket] Connected:', STATE.socket.id);
        });
        
        STATE.socket.on('disconnect', function() {
            STATE.isConnected = false;
            updateConnectionStatus(false);
            console.log('[Socket] Disconnected');
        });
        
        STATE.socket.on('connect_error', function(error) {
            console.error('[Socket] Error:', error.message);
            updateConnectionStatus(false);
        });
        
        STATE.socket.on('token', function(data) {
            handleStreamToken(data.token);
        });
        
        STATE.socket.on('stream_end', function(data) {
            handleStreamEnd(data);
        });
        
        STATE.socket.on('error', function(data) {
            console.error('[Socket] Server Error:', data);
            setOrbState('error');
            setTimeout(function() {
                if (STATE.isVoiceMode) setOrbState('listening');
            }, 1500);
        });
    }
    
    function updateConnectionStatus(connected) {
        if (connected) {
            DOM.statusIndicator.classList.add('connected');
            DOM.statusText.textContent = 'Connected';
        } else {
            DOM.statusIndicator.classList.remove('connected');
            DOM.statusText.textContent = 'Reconnecting...';
        }
    }
    
    // =====================================================================
    // SPEECH RECOGNITION
    // =====================================================================
    function initRecognition() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        
        if (!SpeechRecognition) {
            console.warn('[Speech] Recognition not supported');
            DOM.voiceBtn.disabled = true;
            return;
        }
        
        STATE.recognition = new SpeechRecognition();
        STATE.recognition.continuous = true;
        STATE.recognition.interimResults = true;
        STATE.recognition.lang = STATE.currentLang;
        STATE.recognition.maxAlternatives = 1;
        
        STATE.recognition.onstart = function() {
            STATE.isListening = true;
            if (STATE.isVoiceMode && !STATE.isProcessing && !STATE.isSpeaking) {
                setOrbState('listening');
                DOM.voiceStatus.textContent = 'LISTENING';
                DOM.voiceStatus.classList.add('active');
            }
        };
        
        STATE.recognition.onend = function() {
            STATE.isListening = false;
            if (STATE.isVoiceMode && !STATE.isProcessing) {
                setTimeout(startListening, 50);
            }
        };
        
        STATE.recognition.onerror = function(e) {
            console.log('[Recognition] Error:', e.error);
            if (e.error === 'no-speech' && STATE.isVoiceMode) {
                setTimeout(startListening, 50);
            }
        };
        
        STATE.recognition.onresult = function(event) {
            if (!STATE.isVoiceMode || STATE.isProcessing) return;
            
            // Barge-in: interrupt AI if user starts speaking
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
            
            const displayText = (STATE.finalTranscript + interim).trim();
            DOM.liveTranscript.textContent = displayText;
            DOM.liveTranscript.className = 'live-transcript user-speaking';
            
            if (displayText.length > 0) {
                DOM.orb.classList.add('active');
                DOM.waveform.classList.add('active');
            }
            
            clearTimeout(STATE.silenceTimer);
            
            if (STATE.finalTranscript.trim().length >= CONFIG.minSpeechLength) {
                STATE.silenceTimer = setTimeout(commitUserSpeech, CONFIG.silenceTimeout);
            }
        };
    }
    
    function startListening() {
        try {
            STATE.recognition.start();
        } catch (e) {
            // Already started
        }
    }
    
    function commitUserSpeech() {
        const text = STATE.finalTranscript.trim();
        STATE.finalTranscript = '';
        
        DOM.orb.classList.remove('active');
        DOM.waveform.classList.remove('active');
        
        if (!text) {
            setOrbState('listening');
            return;
        }
        
        STATE.recognition.stop();
        addMessage(text, 'user');
        sendQuery(text, true);
    }
    
    // =====================================================================
    // BARGE-IN: INTERRUPT AI
    // =====================================================================
    function interruptAI() {
        console.log('[Barge-in] Interrupting AI');
        
        STATE.synth.cancel();
        STATE.utteranceQueue = [];
        STATE.isSpeaking = false;
        STATE.isProcessing = false;
        STATE.spokenLength = 0;
        
        setOrbState('listening');
        DOM.voiceStatus.textContent = 'LISTENING';
        DOM.interruptHint.style.opacity = '0';
        
        if (STATE.currentAiMessage) {
            STATE.currentAiMessage.classList.remove('streaming', 'speaking');
        }
    }
    
    // =====================================================================
    // QUERY PROCESSING
    // =====================================================================
    function sendQuery(text, isVoice) {
        STATE.isProcessing = true;
        STATE.requestStartTime = performance.now();
        STATE.fullResponse = '';
        STATE.spokenLength = 0;
        
        if (isVoice) {
            setOrbState('processing');
            DOM.voiceStatus.textContent = 'THINKING';
            DOM.liveTranscript.textContent = '';
            DOM.responseTime.textContent = '';
        }
        
        STATE.currentAiMessage = document.createElement('div');
        STATE.currentAiMessage.className = 'message ai streaming';
        DOM.chatContainer.appendChild(STATE.currentAiMessage);
        scrollToBottom();
        
        const eventName = isVoice ? 'voice_query' : 'text_query';
        STATE.socket.emit(eventName, {
            message: text,
            lang: STATE.currentLang,
            voice: isVoice
        });
    }
    
    // =====================================================================
    // STREAMING TOKEN HANDLER - FIXED SPACING
    // =====================================================================
    function handleStreamToken(token) {
        // First token - show response time
        if (STATE.fullResponse === '' && STATE.requestStartTime) {
            const latency = Math.round(performance.now() - STATE.requestStartTime);
            showResponseTime(latency);
            
            if (STATE.isVoiceMode) {
                setOrbState('speaking');
                DOM.voiceStatus.textContent = 'SPEAKING';
                DOM.interruptHint.style.opacity = '1';
                DOM.liveTranscript.className = 'live-transcript ai-speaking';
            }
        }
        
        // Append token directly - spacing is preserved from server
        STATE.fullResponse += token;
        
        if (STATE.currentAiMessage) {
            STATE.currentAiMessage.textContent = STATE.fullResponse;
            scrollToBottom();
        }
        
        // Voice mode: progressive TTS
        if (STATE.isVoiceMode) {
            DOM.liveTranscript.textContent = STATE.fullResponse.slice(-200);
            progressiveTTS();
        }
    }
    
    function handleStreamEnd(data) {
        if (STATE.currentAiMessage) {
            STATE.currentAiMessage.classList.remove('streaming');
        }
        
        // Speak any remaining text
        if (STATE.isVoiceMode && STATE.fullResponse) {
            const remaining = STATE.fullResponse.substring(STATE.spokenLength).trim();
            if (remaining) {
                speakText(remaining, true);
            }
        }
        
        if (!STATE.isVoiceMode) {
            STATE.isProcessing = false;
            STATE.currentAiMessage = null;
        }
    }
    
    // =====================================================================
    // PROGRESSIVE TEXT-TO-SPEECH - HUMAN-LIKE VOICE
    // =====================================================================
    function progressiveTTS() {
        const unspoken = STATE.fullResponse.substring(STATE.spokenLength);
        const match = unspoken.match(CONFIG.sentenceEndPattern);
        
        if (match) {
            const sentenceEnd = match.index + match[0].length;
            const sentence = unspoken.substring(0, sentenceEnd).trim();
            
            if (sentence) {
                STATE.spokenLength += sentenceEnd;
                speakText(sentence, false);
            }
        }
    }
    
    function speakText(text, isFinal) {
        // Text should already be clean from server, but do minimal cleanup
        let cleanText = text
            .replace(/\*+/g, '')
            .replace(/#+/g, '')
            .replace(/`/g, '')
            .replace(/_+/g, '')
            .trim();
        
        if (!cleanText) return;
        
        const utterance = new SpeechSynthesisUtterance(cleanText);
        
        // Use selected voice
        if (STATE.selectedVoice) {
            utterance.voice = STATE.selectedVoice;
        }
        
        // Apply TTS settings for natural speech
        const isNepali = STATE.currentLang === CONFIG.langNp;
        const settings = isNepali ? CONFIG.ttsSettings.np : CONFIG.ttsSettings.en;
        
        utterance.rate = settings.rate;
        utterance.pitch = settings.pitch;
        utterance.volume = settings.volume;
        
        utterance.onstart = function() {
            STATE.isSpeaking = true;
            if (STATE.currentAiMessage) {
                STATE.currentAiMessage.classList.add('speaking');
            }
        };
        
        utterance.onend = function() {
            STATE.utteranceQueue = STATE.utteranceQueue.filter(u => u !== utterance);
            
            if (STATE.utteranceQueue.length === 0 && isFinal) {
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
        
        utterance.onerror = function(e) {
            console.log('[TTS] Error:', e.error);
        };
        
        STATE.utteranceQueue.push(utterance);
        STATE.synth.speak(utterance);
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
        
        while (DOM.chatContainer.children.length > CONFIG.maxHistory) {
            DOM.chatContainer.removeChild(DOM.chatContainer.firstChild);
        }
    }
    
    function scrollToBottom() {
        DOM.chatContainer.scrollTop = DOM.chatContainer.scrollHeight;
    }
    
    function showResponseTime(ms) {
        DOM.responseTime.textContent = ms + 'ms';
        if (ms < 600) {
            DOM.responseTime.className = 'response-time fast';
        } else if (ms < 1200) {
            DOM.responseTime.className = 'response-time medium';
        } else {
            DOM.responseTime.className = 'response-time slow';
        }
    }
    
    function setLanguage(lang) {
        DOM.btnEn.classList.toggle('active', lang === 'en');
        DOM.btnNp.classList.toggle('active', lang === 'np');
        STATE.currentLang = (lang === 'np') ? CONFIG.langNp : CONFIG.langEn;
        
        // Update voice for new language
        STATE.selectedVoice = selectBestVoice(STATE.currentLang);
        
        if (STATE.recognition) {
            STATE.recognition.lang = STATE.currentLang;
            if (STATE.isVoiceMode && STATE.isListening) {
                STATE.recognition.stop();
                setTimeout(startListening, 100);
            }
        }
        
        const msg = (lang === 'np') 
            ? 'नेपाली मोडमा स्विच गरियो।' 
            : 'Switched to English mode.';
        addMessage(msg, 'ai');
    }
    
    // =====================================================================
    // VOICE MODE CONTROL
    // =====================================================================
    function openVoiceMode() {
        STATE.isVoiceMode = true;
        DOM.voiceOverlay.classList.add('active');
        setOrbState('idle');
        DOM.voiceStatus.textContent = 'TAP ORB TO START';
        DOM.voiceStatus.classList.remove('active');
        DOM.liveTranscript.textContent = '';
        DOM.interruptHint.style.opacity = '0';
    }
    
    function closeVoiceMode() {
        STATE.isVoiceMode = false;
        STATE.isProcessing = false;
        STATE.isSpeaking = false;
        DOM.voiceOverlay.classList.remove('active');
        
        if (STATE.recognition) STATE.recognition.stop();
        STATE.synth.cancel();
        
        STATE.finalTranscript = '';
        STATE.utteranceQueue = [];
        STATE.spokenLength = 0;
    }
    
    function handleOrbClick() {
        if (!STATE.isVoiceMode) return;
        
        if (STATE.isSpeaking) {
            interruptAI();
        } else if (!STATE.isProcessing && !STATE.isListening) {
            startListening();
        }
    }
    
    function sendTextMessage() {
        const text = DOM.textInput.value.trim();
        if (!text || STATE.isProcessing) return;
        
        DOM.textInput.value = '';
        addMessage(text, 'user');
        sendQuery(text, false);
    }
    
    function handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendTextMessage();
        }
    }
    
    // =====================================================================
    // EVENT LISTENERS
    // =====================================================================
    DOM.sendBtn.addEventListener('click', sendTextMessage);
    DOM.textInput.addEventListener('keypress', handleKeyPress);
    DOM.voiceBtn.addEventListener('click', openVoiceMode);
    DOM.closeVoiceBtn.addEventListener('click', closeVoiceMode);
    DOM.orb.addEventListener('click', handleOrbClick);
    DOM.btnEn.addEventListener('click', function() { setLanguage('en'); });
    DOM.btnNp.addEventListener('click', function() { setLanguage('np'); });
    
    // =====================================================================
    // INITIALIZATION
    // =====================================================================
    function init() {
        initSocket();
        initRecognition();
        
        // Load voices
        loadVoices();
        if (typeof speechSynthesis !== 'undefined') {
            speechSynthesis.onvoiceschanged = loadVoices;
        }
        
        console.log('[App] Adarsha AI Voice Interface v3.0 Initialized');
    }
    
    // Start
    init();
})();
</script>

</body>
</html>'''

# ==================================================================================
# WEBSOCKET EVENT HANDLERS
# ==================================================================================
@socketio.on('connect')
def handle_connect():
    print(f'\n\033[92m🔌 Client connected: {request.sid}\033[0m')
    sessions[request.sid] = []

@socketio.on('disconnect')
def handle_disconnect():
    print(f'\n\033[91m🔌 Client disconnected: {request.sid}\033[0m')
    if request.sid in sessions:
        del sessions[request.sid]

@socketio.on('voice_query')
def handle_voice_query(data):
    """Handle voice mode queries - AI knows user is speaking"""
    handle_query(data, is_voice=True)

@socketio.on('text_query')
def handle_text_query(data):
    """Handle text mode queries"""
    handle_query(data, is_voice=False)

def handle_query(data, is_voice):
    user_input = data.get('message', '').strip()
    lang = data.get('lang', 'en-US')
    session_id = request.sid
    
    if not user_input:
        emit('error', {'message': 'Empty input'})
        return
    
    print_bubble("USER", user_input, is_voice=is_voice)
    
    if session_id not in sessions:
        sessions[session_id] = []
    
    perception = {
        'language': lang,
        'history': sessions[session_id][-10:],
        'is_voice_mode': is_voice
    }
    
    start_time = time.time()
    
    try:
        if rag_pipeline:
            full_response = ""
            
            # Pass is_voice to the pipeline for proper formatting
            for token in rag_pipeline.chat_stream(user_input, is_voice=is_voice, perception_data=perception):
                full_response += token
                emit('token', {'token': token})
                socketio.sleep(0)
            
            response_time = int((time.time() - start_time) * 1000)
            print_bubble("AI", full_response, response_time, is_voice=is_voice)
            
            # Update session history
            sessions[session_id].append({'role': 'user', 'content': user_input})
            sessions[session_id].append({'role': 'assistant', 'content': full_response})
            
            # Trim history
            if len(sessions[session_id]) > 20:
                sessions[session_id] = sessions[session_id][-20:]
            
            emit('stream_end', {'success': True})
        else:
            emit('token', {'token': 'Pipeline not loaded. Please check server logs.'})
            emit('stream_end', {'success': False})
            
    except Exception as e:
        print(f'\n\033[91m❌ Error: {e}\033[0m')
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)})
        emit('stream_end', {'success': False})

# ==================================================================================
# HTTP ROUTES
# ==================================================================================
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'pipeline': rag_pipeline is not None,
        'websocket': True,
        'sessions': len(sessions),
        'version': '3.0'
    })

# ==================================================================================
# MAIN
# ==================================================================================
if __name__ == '__main__':
    print("\n" + "="*50)
    print(" 🚀 Server: http://localhost:5000")
    print(" 🔌 WebSocket: Enabled")
    print(" 🎤 Voice Mode: Human-like TTS")
    print(" ✅ Pipeline:", "Loaded" if rag_pipeline else "Not Found")
    print("="*50 + "\n")
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True
    )