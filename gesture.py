import cv2
import mediapipe as mp  # type: ignore
import requests
import time

BLYNK_TOKEN = "uQcOFSmKoKYwxHxJ-2trKV5tkCDYjqnU"
BLYNK_BASE = "https://blynk.cloud/external/api"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    model_complexity=0,   # 🔥 faster model
    min_detection_confidence=0.7,
    min_tracking_confidence=0.6
)

mp_drawing = mp.solutions.drawing_utils


class GestureController:

    def __init__(self):
        self.last_action_time = 0
        self.action_delay = 0.3

        # 🔥 NEW: state tracking (avoid repeated calls)
        self.prev_state = [-1, -1, -1]

        # 🔥 NEW: detection smoothing
        self.hand_present = False
        self.hand_detected_time = 0
        self.warmup_delay = 0.3

    # ---------------- SEND TO BLYNK ----------------

    def set_led(self, index, value):
        try:
            requests.get(
                f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V{index}={value}",
                timeout=1
            )
        except:
            pass


# ---------------- MAIN ----------------

def main():
    cap = cv2.VideoCapture(0)

    # 🔥 Reduce resolution (helps stability)
    cap.set(3, 640)
    cap.set(4, 480)

    controller = GestureController()

    print("Gesture Smart Switch Ready")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)

        current_time = time.time()

        # ---------------- HAND DETECTED ----------------
        if results.multi_hand_landmarks:

            # 🔥 Warmup handling
            if not controller.hand_present:
                controller.hand_present = True
                controller.hand_detected_time = current_time

            if current_time - controller.hand_detected_time < controller.warmup_delay:
                cv2.imshow("Gesture Smart Switch", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                continue

            hands_data = []

            for hand in results.multi_hand_landmarks:
                # Optional: comment for extra FPS
                # mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                landmarks = hand.landmark

                lm = [[p.x, p.y] for p in landmarks]
                tips = [8, 12, 16]
                pips = [6, 10, 14]

                fingers = []
                for tip, pip in zip(tips, pips):
                    fingers.append(1 if lm[tip][1] < lm[pip][1] else 0)

                hands_data.append(fingers)

            # -------- CONTROL LOGIC --------
            if current_time - controller.last_action_time > controller.action_delay:

                # -------- SINGLE HAND (ON / EXACT MAPPING) --------
                if len(hands_data) == 1:

                    fingers = hands_data[0]

                    for i in range(3):
                        if fingers[i] != controller.prev_state[i]:
                            controller.set_led(i, fingers[i])
                            time.sleep(0.05)  # 🔥 prevent burst

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
                            if on_hand[i] == 1 and controller.prev_state[i] != 0:
                                controller.set_led(i, 0)
                                time.sleep(0.05)

                        controller.prev_state = [0 if on_hand[i] == 1 else controller.prev_state[i] for i in range(3)]

                controller.last_action_time = current_time

        else:
            # 🔥 Reset detection state
            controller.hand_present = False

        cv2.imshow("Gesture Smart Switch", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()