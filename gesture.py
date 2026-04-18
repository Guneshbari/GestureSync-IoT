import cv2
import mediapipe as mp  # type: ignore
import requests
import time
import threading
import speech_recognition as sr
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BLYNK_TOKEN = os.environ.get("BLYNK_TOKEN")
BLYNK_BASE = "https://blynk.cloud/external/api"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=0,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)

mp_drawing = mp.solutions.drawing_utils


# ---------------- CONTROLLER ----------------

class Controller:

    def __init__(self):
        self.prev_state = [-1, -1, -1]
        self.last_action_time = 0
        self.action_delay = 0.3

    def set_device(self, pin, value):
        try:
            requests.get(
                f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V{pin}={value}",
                timeout=1
            )
        except:
            pass


controller = Controller()


# ---------------- VOICE HELPERS ----------------

def normalize_command(command):
    command = command.lower()

    replacements = {
        "one": "1",
        "two": "2",
        "too": "2",
        "to": "2",
        "three": "3",
        "first": "1",
        "second": "2",
        "third": "3"
    }

    for k, v in replacements.items():
        command = command.replace(k, v)

    return command


def extract_lights(command):
    lights = []
    for i in ["1", "2", "3"]:
        if i in command:
            lights.append(int(i) - 1)
    return list(set(lights))


def detect_action(command):
    if any(word in command for word in ["on", "start", "activate"]):
        return "on"
    elif any(word in command for word in ["off", "stop", "deactivate"]):
        return "off"
    return None


def control_motor(command, action):
    if "fan" in command or "motor" in command:
        if action == "on":
            controller.set_device(5, 1)   # V5
        elif action == "off":
            controller.set_device(5, 0)
        return True
    return False


# ---------------- VOICE CONTROL ----------------

def voice_listener():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source)
                print("🎤 Listening...")
                audio = recognizer.listen(source, phrase_time_limit=3)

            command = recognizer.recognize_google(audio).lower()
            print("You said:", command)

            command = normalize_command(command)
            print("Normalized:", command)

            lights = extract_lights(command)
            action = detect_action(command)

            # -------- MOTOR --------
            if control_motor(command, action):
                pass

            # -------- ALL LIGHTS --------
            elif "all" in command and action:
                for i in range(3):
                    controller.set_device(i, 1 if action == "on" else 0)

            # -------- INDIVIDUAL LIGHTS --------
            elif lights and action:
                for i in lights:
                    controller.set_device(i, 1 if action == "on" else 0)

            else:
                print("⚠️ No valid command")

        except Exception as e:
            print("Error:", e)
            continue


# Run voice in background
threading.Thread(target=voice_listener, daemon=True).start()


# ---------------- GESTURE ----------------

def main():
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)

    print("System Ready (Gesture + Voice + Motor)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        current_time = time.time()

        if results.multi_hand_landmarks:

            hands_data = []

            for hand in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS
                )

                lm = [[p.x, p.y] for p in hand.landmark]
                tips = [8, 12, 16]
                pips = [6, 10, 14]

                fingers = []
                for tip, pip in zip(tips, pips):
                    fingers.append(1 if lm[tip][1] < lm[pip][1] else 0)

                hands_data.append(fingers)

            if current_time - controller.last_action_time > controller.action_delay:

                # -------- SINGLE HAND --------
                if len(hands_data) == 1:
                    fingers = hands_data[0]

                    for i in range(3):
                        if fingers[i] != controller.prev_state[i]:
                            controller.set_device(i, fingers[i])
                            time.sleep(0.05)

                    controller.prev_state = fingers.copy()

                # -------- TWO HANDS (OFF) --------
                elif len(hands_data) == 2:

                    h1, h2 = hands_data

                    if sum(h1) == 0:
                        on_hand = h2
                    elif sum(h2) == 0:
                        on_hand = h1
                    else:
                        on_hand = None

                    if on_hand:
                        for i in range(3):
                            if on_hand[i] == 1:
                                controller.set_device(i, 0)

                controller.last_action_time = current_time

        cv2.imshow("Smart Control System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()