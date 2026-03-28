/**
 * Smart Control Dashboard Integration - Production Grade
 * Connects the UI to Blynk Cloud API and Web Speech API
 */

// --- 1. CONFIGURATION ---
const TOKEN = 'uQcOFSmKoKYwxHxJ-2trKV5tkCDYjqnU'; // Active project token
const BLYNK_BASE = 'https://blynk.cloud/external/api';

const PIN_MAP = {
    'light-1': 'V0',
    'light-2': 'V1',
    'light-3': 'V2',
    'brightness': 'V4',
    'motor-1': 'V5'
};

// --- 2. STATE LOGIC & DOM ELEMENTS ---
const systemState = {
    'light-1': null,
    'light-2': null,
    'light-3': null,
    'motor-1': null,
    listening: false
};

const cssVars = getComputedStyle(document.documentElement);
const primaryColor = cssVars.getPropertyValue('--primary').trim();
const accentColor = cssVars.getPropertyValue('--accent').trim();
const secondaryColor = cssVars.getPropertyValue('--secondary').trim();

const statusMsg = document.getElementById('status-message');
const statusDot = document.getElementById('status-indicator');
const micBtn = document.getElementById('mic-trigger');

function setStatus(message, type = 'default') {
    if (!statusMsg || !statusDot) return;

    statusMsg.textContent = message;

    if (type === 'active') {
        statusDot.style.backgroundColor = primaryColor;
        statusDot.style.boxShadow = `0 0 10px ${primaryColor}`;
        statusMsg.style.color = '#FFFFFF';
    } else if (type === 'accent') {
        statusDot.style.backgroundColor = accentColor;
        statusDot.style.boxShadow = `0 0 10px ${accentColor}`;
        statusMsg.style.color = '#FFFFFF';
    } else {
        statusDot.style.backgroundColor = secondaryColor;
        statusDot.style.boxShadow = 'none';
        statusMsg.style.color = secondaryColor;
    }
}

// Ensure UI State matches physical state without flickering
function updateUIState(id, isActive) {
    if (systemState[id] === isActive) return;
    systemState[id] = isActive;

    const card = document.getElementById(id);
    if (!card) return;

    if (isActive) {
        card.classList.add('active');
    } else {
        card.classList.remove('active');
    }
}


// --- 3. RELIABLE API COMMUNICATION LAYER ---
async function blynkUpdate(pin, value) {
    try {
        const response = await fetch(`${BLYNK_BASE}/update?token=${TOKEN}&${pin}=${value}`, { method: 'GET' });
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        console.log(`[Blynk] Transmitted: ${pin} = ${value}`);
    } catch (error) {
        console.error('[Blynk] Update Error:', error);
        setStatus('Cloud connection error', 'default');
    }
}

async function blynkGet(pin) {
    try {
        const response = await fetch(`${BLYNK_BASE}/get?token=${TOKEN}&${pin}`, { method: 'GET' });
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        const text = await response.text();

        // Remove brackets/quotes safely for stable boolean evaluation
        const cleanText = text.replace(/[^a-zA-Z0-9.\-]/g, '');
        return cleanText === '1' || cleanText === 'true';
    } catch (error) {
        console.error(`[Blynk] Read Error for ${pin}:`, error);
        return null;
    }
}

// --- 4. STABILIZED STATE SYNCHRONIZATION ---
let isSyncing = false;

async function syncState() {
    // Avoid dropping sync cycles while syncing, or while voice is interacting
    if (systemState.listening || isSyncing) return;

    isSyncing = true;
    const pinsToSync = ['light-1', 'light-2', 'light-3', 'motor-1'];

    try {
        // Run concurrent fetches for low latency
        const promises = pinsToSync.map(async (id) => {
            const val = await blynkGet(PIN_MAP[id]);
            if (val !== null) {
                updateUIState(id, val);
            }
        });
        await Promise.all(promises);
    } catch (e) {
        console.error("[Blynk] Sync Cycle Failed:", e);
    } finally {
        isSyncing = false;
    }
}

// Poll state continuously
setInterval(syncState, 2000);

// --- 5. UI CONTROL BINDINGS ---
window.toggleLight = async function (id) {
    const cardId = `light-${id}`;
    const newState = !systemState[cardId];

    updateUIState(cardId, newState);
    setStatus(`Light ${id} Turned ${newState ? 'ON' : 'OFF'}`, newState ? 'active' : 'default');

    // Non-blocking fire and forget
    blynkUpdate(PIN_MAP[cardId], newState ? 1 : 0);
    if (navigator.vibrate) navigator.vibrate(50);
};

window.toggleMotor = async function () {
    const cardId = 'motor-1';
    const newState = !systemState[cardId];

    updateUIState(cardId, newState);
    setStatus(`Motor ${newState ? 'Activated' : 'Deactivated'}`, newState ? 'accent' : 'default');

    blynkUpdate(PIN_MAP[cardId], newState ? 1 : 0);
    if (navigator.vibrate) navigator.vibrate([50, 50, 50]);
};

window.setGlobalState = async function (isOn) {
    setStatus(isOn ? 'All Lights Activated' : 'All Lights OFF', isOn ? 'active' : 'default');

    const updates = [];

    // Process lights only
    [1, 2, 3].forEach(i => {
        const id = `light-${i}`;
        updateUIState(id, isOn);
        updates.push(blynkUpdate(PIN_MAP[id], isOn ? 1 : 0));
    });

    await Promise.all(updates);
    if (navigator.vibrate) navigator.vibrate(100);
};

// --- 6. OPTIMIZED BRIGHTNESS SETTER ---
let brightnessTimeout = null;
window.setBrightness = function (value) {
    // Expected value range: 0 - 255
    if (brightnessTimeout) clearTimeout(brightnessTimeout);

    // Heavily debounce the scroll/slider input to protect API limits
    brightnessTimeout = setTimeout(() => {
        blynkUpdate(PIN_MAP['brightness'], value);
    }, 200);
};


// --- 7. BROWSER VOICE CONTROL (WEB SPEECH API) ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = function () {
        systemState.listening = true;
        if (micBtn) micBtn.classList.add('listening');
        setStatus('Listening...', 'active');
        if (navigator.vibrate) navigator.vibrate(50);
    };

    recognition.onresult = function (event) {
        const transcript = event.results[0][0].transcript.toLowerCase();
        console.log("[Voice] Captured:", transcript);
        handleVoiceCommand(transcript);
    };

    recognition.onerror = function (event) {
        console.error('[Voice] Error:', event.error);
        stopListening();
        setStatus('Voice engine error', 'default');
    };

    recognition.onend = function () {
        stopListening();
    };
} else {
    console.warn("[Initial Setup] Web Speech API not natively supported.");
}

function stopListening() {
    systemState.listening = false;
    if (micBtn) micBtn.classList.remove('listening');
    if (statusMsg && statusMsg.textContent === 'Listening...') {
        setStatus('Voice standby', 'default');
    }
}

window.toggleVoice = function () {
    if (!recognition) {
        setStatus('Voice API unsupported here', 'default');
        return;
    }
    systemState.listening ? recognition.stop() : recognition.start();
};

function normalizeNumbersFromCommand(command) {
    const map = {
        "one": "1", "first": "1",
        "two": "2", "too": "2", "to": "2", "second": "2",
        "three": "3", "third": "3"
    };

    const words = command.split(/\s+/);
    const nums = [];

    words.forEach(w => {
        if (map[w]) {
            nums.push(map[w]);
        } else if (/\d/.test(w)) {
            nums.push(w.match(/\d/)[0]);
        }
    });

    return [...new Set(nums)];
}

function handleVoiceCommand(command) {
    if (/\b(on\s+and\s+off|off\s+and\s+on)\b/i.test(command)) {
        setStatus('Ignored due to ambiguity', 'default');
        return;
    }

    let results = [];
    let lastAction = null;

    // Split command using 'then' first for sequential execution
    const sequences = command.split(/\s+then\s+/);

    sequences.forEach(sequence => {
        // Within each segment, split using 'and' or ','
        const parts = sequence.split(/\s+and\s+|,/);

        parts.forEach(part => {
            part = part.trim();
            if (!part) return;

            const isOn = ["on", "start", "activate"].some(w => part.includes(w));
            const isOff = ["off", "stop", "deactivate", "shut", "halt"].some(w => part.includes(w));

            let targetState = null;

            // Strict action resolution
            if (isOn && !isOff) {
                targetState = true;
                lastAction = true;
            } else if (isOff && !isOn) {
                targetState = false;
                lastAction = false;
            } else if (!isOn && !isOff && lastAction !== null) {
                targetState = lastAction;
            } else {
                // If both ON and OFF are present, or neither is present and no history exists
                return;
            }

            let partTargetsHandled = false;

            // MOTOR
            if (part.includes("fan") || part.includes("motor")) {
                updateUIState('motor-1', targetState);
                blynkUpdate(PIN_MAP['motor-1'], targetState ? 1 : 0);
                results.push(`Motor ${targetState ? 'ON' : 'OFF'}`);
                partTargetsHandled = true;
            }

            // LIGHTS & CONTEXT
            const isLight = part.includes("light");
            const nums = normalizeNumbersFromCommand(part);
            const isAll = part.includes("all") || part.includes("everything");

            if (isLight || (!partTargetsHandled && nums.length > 0) || (!partTargetsHandled && isAll)) {
                if (isAll) {
                    [1, 2, 3].forEach(i => {
                        const id = `light-${i}`;
                        updateUIState(id, targetState);
                        blynkUpdate(PIN_MAP[id], targetState ? 1 : 0);
                    });
                    results.push(`All Lights ${targetState ? 'ON' : 'OFF'}`);
                    partTargetsHandled = true;
                } else if (nums.length > 0) {
                    nums.forEach(numStr => {
                        const i = parseInt(numStr);
                        if ([1, 2, 3].includes(i)) {
                            const id = `light-${i}`;
                            updateUIState(id, targetState);
                            blynkUpdate(PIN_MAP[id], targetState ? 1 : 0);
                            results.push(`Light ${i} ${targetState ? 'ON' : 'OFF'}`);
                        }
                    });
                    partTargetsHandled = true;
                }
            }

            // GENERIC BEHAVIOR (e.g. "turn on")
            if (!partTargetsHandled && (part.includes("turn") || part.includes("switch"))) {
                [1, 2, 3].forEach(i => {
                    const id = `light-${i}`;
                    updateUIState(id, targetState);
                    blynkUpdate(PIN_MAP[id], targetState ? 1 : 0);
                });
                results.push(`All Lights ${targetState ? 'ON' : 'OFF'}`);
                partTargetsHandled = true;
            }
        });
    });

    // Single final status message
    if (results.length > 0) {
        setStatus(results.join(', '), 'active');
    } else if (!/\b(on\s+and\s+off|off\s+and\s+on)\b/i.test(command)) {
        setStatus('Ignored due to ambiguity or unknown target', 'default');
    }
}

// Boot Sequence
document.addEventListener('DOMContentLoaded', () => {
    syncState();
});
