# GestureSync-IoT

GestureSync-IoT is a real-time, multimodal smart home control system that leverages computer vision and voice recognition to control physical devices (such as LEDs) without physical switches. The system simultaneously tracks hand gestures via a webcam and listens for spoken commands, bridging these commands instantly over the cloud to a microcontroller.

## System Architecture

The project is built around three core components:

1. **Multimodal Client (Python)**
2. **IoT Broker (Blynk Cloud)**
3. **Hardware Controller (ESP32)**

```mermaid
graph LR
    A[Webcam] -->|Video feed| B[Python Client (`gesture.py`)]
    M[Microphone] -->|Audio input| B
    B -->|MediaPipe Analysis + Voice Recognition| B
    B -->|HTTP GET Requests| C[Blynk Cloud]
    C -->|Blynk Protocol| D[ESP32 Microcontroller]
    D -->|PWM Signals| E[LEDs]
```

### 1. Multimodal Client (`gesture.py`)
This script acts as the brains of the operation, capturing hardware sensory input (video and audio) simultaneously to issue commands.

**Gesture Control (Powered by MediaPipe Hands):**
Translates hand configurations into mapped states:
*   **One Hand (Control Modality):**
    *   Maps Index, Middle, and Ring fingers independently to LEDs 1, 2, and 3. Raising the finger turns its mapped LED **ON**, lowering it turns it **OFF**.
*   **Two Hands (Off-Modifier Modality):**
    *   One hand closed (Fist) acts as a modifier.
    *   Fist + 3 fingers up: Turns **ALL** LEDs OFF safely.
    *   Fist + specific fingers up: Turns **specific** LEDs OFF.
*   **Optimization Framework:** To prevent spamming the Blynk API and introducing latency, the script tracks the `prev_state` array locally, broadcasting changes **only** when a new, distinct physical posture is detected.

**Voice Control (Powered by SpeechRecognition):**
A daemon thread continuously listens for audio using ambient noise adjustment. Spoken phrases are automatically normalized (e.g., "one" to "1", "to" to "2").
*   Supports explicit targeting: "*Turn on light one*" or "*Deactivate light 3*".
*   Supports global actions: "*Turn off all lights!*" or "*Start all*".

### 2. IoT Broker (Blynk Cloud)
The Blynk Cloud API serves as the low-latency middleware hub.
*   `V0`, `V1`, `V2`: Act as virtual boolean pins corresponding to individual LED states.

### 3. Hardware Controller (`led_motion.ino`)
An ESP32 microcontroller that translates cloud states back into the physical layer:
*   Establishes a Wi-Fi link.
*   Reacts immediately to virtual pin updates via `BLYNK_WRITE()` interrupts.
*   Outputs matching states by triggering physical hardware PWM (`analogWrite()`) targeting GPIO pins `5`, `18`, and `19`.

## Hardware Requirements
*   PC/Laptop equipped with a **Webcam** and **Microphone** (or headset).
*   ESP32 or compatible Wi-Fi microcontroller.
*   3x LEDs + adequate current-limiting resistors.
*   Breadboard and hook-up wiring.

## Software Dependencies

### Python Environment
*   Python 3.8+
*   `opencv-python`
*   `mediapipe`
*   `requests`
*   `SpeechRecognition`
*   `PyAudio` (Often required natively by SpeechRecognition to access the microphone)

### ESP32 Config
*   Arduino IDE with the official ESP32 Board Packages.
*   `BlynkSimpleEsp32` library.

## Getting Started

1.  **Hardware Assembly:** Wire the 3 LEDs to your ESP32 board. Connect the signal leads to GPIO pins `5`, `18`, and `19`, and complete the circuit through the resistors to the ground pin.
2.  **Flash the ESP32:** 
    *   Open `led_motion.ino`.
    *   Input your local Wi-Fi credentials (`ssid` and `password`).
    *   Confirm your `BLYNK_AUTH_TOKEN` correctly reflects your Blynk template configuration.
    *   Compile, verify, and upload the code to the board via USB.
3.  **Run the Multimodal Client:**
    *   Install the required software libraries:
        ```bash
        pip install opencv-python mediapipe requests SpeechRecognition PyAudio
        ```
    *   In a terminal, execute the main script:
        ```bash
        python gesture.py
        ```
4.  **Experience:** Show your hand combinations to the camera or speak into the microphone to trigger physical events!
