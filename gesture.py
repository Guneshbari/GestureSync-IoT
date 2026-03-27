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
        self.last_action_time = 0
        self.action_delay = 0.5   # slightly increased for stability

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

    # ---------------- BRIGHTNESS ----------------

    def palm_brightness(self, landmarks):
        wrist = landmarks[0]
        middle = landmarks[12]

        distance = math.sqrt(
            (wrist.x - middle.x) ** 2 +
            (wrist.y - middle.y) ** 2
        )

        min_d = 0.05
        max_d = 0.25

        brightness = int(((distance - min_d) / (max_d - min_d)) * 255)
        return max(0, min(255, brightness))


# ---------------- MAIN ----------------

def main():
    cap = cv2.VideoCapture(0)
    controller = GestureController()

    print("Controls:")
    print("1 finger → ON specific LED")
    print("3 fingers → ALL ON")
    print("fist + 1 finger → OFF specific LED")
    print("fist + 3 fingers → ALL OFF")
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

                # -------- SINGLE HAND (TURN ON) --------
                if len(hands_data) == 1:

                    fingers = hands_data[0]
                    count = sum(fingers)

                    if count == 3:
                        controller.set_all(1)

                    elif count == 1:
                        for i in range(3):
                            if fingers[i] == 1:
                                controller.set_led(i, 1)

                # -------- TWO HANDS (TURN OFF) --------
                elif len(hands_data) == 2:

                    h1, h2 = hands_data

                    if sum(h1) == 0:
                        on_hand = h2
                    elif sum(h2) == 0:
                        on_hand = h1
                    else:
                        on_hand = None

                    if on_hand:
                        count = sum(on_hand)

                        if count == 3:
                            controller.set_all(0)

                        elif count == 1:
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