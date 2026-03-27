import cv2
import mediapipe as mp  # type: ignore
import requests
import math
import time
import threading

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
        self.current_led_state = [0, 0, 0]
        self.last_action_time = 0
        self.action_delay = 0.4

        self.blynk_busy = False

        # Idle sync — only runs when no hand is present
        self.last_sync_time = 0
        self.sync_interval = 3.0  # sync from Blynk every 3 seconds when idle

    # ---------------- PUSH ONLY (no read — local state is trusted) ----------------

    def _push_to_blynk(self, state, brightness):
        """Just pushes state to Blynk. No read. No stale data interference."""
        try:
            for i, pin in enumerate(["V0", "V1", "V2"]):
                requests.get(
                    f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&{pin}={state[i]}",
                    timeout=2
                )
            requests.get(
                f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V4={brightness}",
                timeout=2
            )
            all_on = 1 if all(s == 1 for s in state) else 0
            requests.get(
                f"{BLYNK_BASE}/update?token={BLYNK_TOKEN}&V3={all_on}",
                timeout=2
            )
            print(f"LED pushed: {state} | Brightness: {brightness}")
        except Exception as e:
            print(f"Blynk push error: {e}")
        finally:
            self.blynk_busy = False

    def trigger_blynk(self, state, brightness):
        if self.blynk_busy:
            return
        self.blynk_busy = True
        t = threading.Thread(
            target=self._push_to_blynk,
            args=(state, brightness),
            daemon=True
        )
        t.start()

    # ---------------- IDLE SYNC (runs when no hand detected) ----------------

    def _sync_from_blynk(self):
        """Reads Blynk state when idle — picks up any switch changes."""
        try:
            synced = []
            for pin in ["V0", "V1", "V2"]:
                r = requests.get(
                    f"{BLYNK_BASE}/get?token={BLYNK_TOKEN}&{pin}",
                    timeout=2
                )
                synced.append(int(float(r.text.strip())))
            self.current_led_state = synced
            print(f"Idle sync from Blynk: {synced}")
        except Exception as e:
            print(f"Blynk sync error: {e}")
        finally:
            self.blynk_busy = False

    def trigger_idle_sync(self):
        if self.blynk_busy:
            return
        self.blynk_busy = True
        t = threading.Thread(
            target=self._sync_from_blynk,
            daemon=True
        )
        t.start()

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

            hands_data = []
            brightness = 150

            for hand in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)

                landmarks = hand.landmark
                fingers = controller.get_finger_states(landmarks)
                hands_data.append(fingers)

                brightness = controller.palm_brightness(landmarks)

            if current_time - controller.last_action_time > controller.action_delay:

                # Local state is source of truth — no Blynk read here
                new_state = controller.current_led_state.copy()

                # -------- SINGLE HAND (ON) --------
                if len(hands_data) == 1:

                    fingers = hands_data[0]
                    count = sum(fingers)

                    if count == 3:
                        new_state = [1, 1, 1]

                    elif count == 1:
                        for i in range(3):
                            if fingers[i] == 1:
                                new_state[i] = 1

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
                        count = sum(on_hand)

                        if count == 3:
                            new_state = [0, 0, 0]

                        elif count == 1:
                            for i in range(3):
                                if on_hand[i] == 1:
                                    new_state[i] = 0

                # Only push if state actually changed
                if new_state != controller.current_led_state:
                    controller.current_led_state = new_state  # update immediately
                    controller.trigger_blynk(new_state, brightness)

                controller.last_action_time = current_time

        # ---------------- NO HAND — IDLE SYNC ----------------
        else:
            # Periodically sync from Blynk to catch switch changes
            if current_time - controller.last_sync_time > controller.sync_interval:
                controller.trigger_idle_sync()
                controller.last_sync_time = current_time

        cv2.imshow("ESP32 Gesture Smart Switch", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()