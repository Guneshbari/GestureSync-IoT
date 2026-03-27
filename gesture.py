import cv2
import mediapipe as mp  # type: ignore
import requests
import math
import time

BLYNK_TOKEN = "uQcOFSmKoKYwxHxJ-2trKV5tkCDYjqnU"
BLYNK_BASE = "https://blynk.cloud/external/api"

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,
    min_detection_confidence=0.8,
    min_tracking_confidence=0.7
)

mp_drawing = mp.solutions.drawing_utils


class GestureController:

    def __init__(self):
        self.last_action_time = 0.0
        self.action_delay = 0.5

    # ---------------- SEND TO BLYNK ----------------

    def set_led(self, index, value):
        try:
            requests.get(
                f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V{index}={value}",
                timeout=1
            )
        except:
            pass

    def set_all(self, value):
        try:
            for i in range(3):
                requests.get(
                    f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V{i}={value}",
                    timeout=1
                )
        except:
            pass

    # ---------------- FINGER DETECTION ----------------

    def get_finger_states(self, landmarks):
        lm = [[p.x, p.y] for p in landmarks]

        fingers = []
        tips = [8, 12, 16]
        pips = [6, 10, 14]

        for tip, pip in zip(tips, pips):
            fingers.append(1 if lm[tip][1] < lm[pip][1] else 0)

        return fingers

    # ---------------- MAIN ----------------

def main():
    cap = cv2.VideoCapture(0)
    controller = GestureController()

    print("Controls:")
    print("Index → LED1")
    print("Middle → LED2")
    print("Ring → LED3")
    print("Combinations → exact LED combinations")
    print("Fist + fingers → turn OFF LEDs")
    print("Q → Quit")

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

                landmarks = hand.landmark
                fingers = controller.get_finger_states(landmarks)
                hands_data.append(fingers)

            # -------- DELAY CONTROL --------
            if current_time - controller.last_action_time > controller.action_delay:

                # -------- SINGLE HAND (ON / EXACT MAPPING) --------
                if len(hands_data) == 1:

                    fingers = hands_data[0]

                    # Direct mapping (IMPORTANT FIX)
                    for i in range(3):
                        controller.set_led(i, fingers[i])

                # -------- TWO HANDS (OFF) --------
                elif len(hands_data) == 2:

                    h1, h2 = hands_data

                    # detect fist + active hand
                    if sum(h1) == 0:
                        on_hand = h2
                    elif sum(h2) == 0:
                        on_hand = h1
                    else:
                        on_hand = None

                    if on_hand:
                        # Turn OFF only those LEDs
                        for i in range(3):
                            if on_hand[i] == 1:
                                controller.set_led(i, 0)

                controller.last_action_time = current_time

        cv2.imshow("Gesture Smart Switch", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()