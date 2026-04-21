import cv2
import mediapipe as mp
import requests
import time
import threading
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BLYNK_TOKEN = "Pyg4QC6R_zPxW6HeYkttfLLW3-47q1aF"
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

class Controller:
    def __init__(self):
        self.prev_state = [-1, -1, -1]
        self.last_action_time = 0
        self.action_delay = 0.3

    def set_led(self, index, value):
        try:
            requests.get(
                f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V{index}={value}",
                timeout=1
            )
        except:
            pass

controller = Controller()

# ---- Shared state between threads ----
latest_frame = None
latest_results = None
frame_lock = threading.Lock()
results_lock = threading.Lock()
running = True

def processing_thread():
    """Runs MediaPipe in background — never blocks the capture loop."""
    global latest_results
    while running:
        with frame_lock:
            frame = latest_frame
        if frame is None:
            time.sleep(0.01)
            continue
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = hands.process(rgb)
        with results_lock:
            latest_results = result

def main():
    global latest_frame, running

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # minimize buffer lag

    proc = threading.Thread(target=processing_thread, daemon=True)
    proc.start()

    print("Gesture Control Mode | Press 'q' to exit")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        with frame_lock:
            latest_frame = frame.copy()

        # Use last known results — no blocking
        with results_lock:
            results = latest_results

        current_time = time.time()

        if results and results.multi_hand_landmarks:
            hands_data = []
            for hand in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
                lm = [[p.x, p.y] for p in hand.landmark]
                tips = [8, 12, 16]
                pips = [6, 10, 14]
                fingers = [1 if lm[t][1] < lm[p][q1] else 0 for t, p in zip(tips, pips)]
                hands_data.append(fingers)

            if current_time - controller.last_action_time > controller.action_delay:
                if len(hands_data) == 1:
                    fingers = hands_data[0]
                    for i in range(3):
                        if fingers[i] != controller.prev_state[i]:
                            controller.set_led(i, fingers[i])
                            time.sleep(0.05)
                    controller.prev_state = fingers.copy()

                elif len(hands_data) == 2:
                    h1, h2 = hands_data
                    on_hand = h2 if sum(h1) == 0 else (h1 if sum(h2) == 0 else None)
                    if on_hand:
                        for i in range(3):
                            if on_hand[i] == 1:
                                controller.set_led(i, 0)

                controller.last_action_time = current_time

        cv2.imshow("Gesture Only Control", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    running = False
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()