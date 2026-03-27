// State Machine
const systemState = {
    lights: {
        1: false,
        2: false,
        3: false
    },
    motor: false,
    listening: false
};

const cssVars = getComputedStyle(document.documentElement);
const primaryColor = cssVars.getPropertyValue('--primary').trim();
const accentColor = cssVars.getPropertyValue('--accent').trim();
const secondaryColor = cssVars.getPropertyValue('--secondary').trim();

// Elements
const statusMsg = document.getElementById('status-message');
const statusDot = document.getElementById('status-indicator');
const micBtn = document.getElementById('mic-trigger');

// Notification handler
function setStatus(message, type = 'default') {
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

// Toggle Individual Lights
window.toggleLight = function(id) {
    const card = document.getElementById(`light-${id}`);
    systemState.lights[id] = !systemState.lights[id];
    
    if (systemState.lights[id]) {
        card.classList.add('active');
        setStatus(`Light ${id} Turned ON`, 'active');
    } else {
        card.classList.remove('active');
        setStatus(`Light ${id} Turned OFF`, 'default');
    }
    
    // Interaction feedback
    navigator.vibrate && navigator.vibrate(50);
};

// Toggle Motor
window.toggleMotor = function() {
    const card = document.getElementById(`motor-1`);
    systemState.motor = !systemState.motor;
    
    if (systemState.motor) {
        card.classList.add('active');
        setStatus(`Motor Activated`, 'accent');
    } else {
        card.classList.remove('active');
        setStatus(`Motor Deactivated`, 'default');
    }
    
    navigator.vibrate && navigator.vibrate([50, 50, 50]);
};

// Global Operations
window.setGlobalState = function(isOn) {
    // Update Lights
    [1, 2, 3].forEach(id => {
        systemState.lights[id] = isOn;
        const card = document.getElementById(`light-${id}`);
        isOn ? card.classList.add('active') : card.classList.remove('active');
    });
    
    // Update Motor target
    systemState.motor = isOn;
    const motorCard = document.getElementById(`motor-1`);
    isOn ? motorCard.classList.add('active') : motorCard.classList.remove('active');

    if(isOn) {
        setStatus('All Devices Activated', 'active');
    } else {
        setStatus('System entering sleep mode', 'default');
    }
    
    navigator.vibrate && navigator.vibrate(100);
};

// Voice Simulator 
window.toggleVoice = function() {
    systemState.listening = !systemState.listening;

    if (systemState.listening) {
        micBtn.classList.add('listening');
        setStatus('Listening...', 'active');
        navigator.vibrate && navigator.vibrate(50);

        // Simulate processing delay
        setTimeout(() => {
            if (systemState.listening) {
                toggleVoice(); // Disable mic
                simulateVoiceCommand();
            }
        }, 2500);
    } else {
        micBtn.classList.remove('listening');
        if (statusMsg.textContent === 'Listening...') {
            setStatus('Voice command cancelled', 'default');
        }
    }
};

function simulateVoiceCommand() {
    // Random demo command
    setGlobalState(true);
    setStatus('Voice execution: "Turn on everything"', 'accent');
}
