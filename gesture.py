import cv2
import mediapipe as mp  # type: ignore
import socket
import math
import time

ESP32_IP = "172.20.10.3"
ESP32_PORT = 80

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,  # IMPORTANT: 2 hands
    min_detection_confidence=0.8,
    min_tracking_confidence=0.7
)

mp_drawing = mp.solutions.drawing_utils


class GestureController:

    def __init__(self):
        self.socket = None
        self.current_led_state = [0, 0, 0]

        # Delay lock (prevents repeated triggers)
        self.last_action_time = 0
        self.action_delay = 0.4

    # ---------------- ESP32 CONNECTION ----------------

    def connect_esp32(self):
        try:
            if self.socket:
                self.socket.close()

            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(3)
            self.socket.connect((ESP32_IP, ESP32_PORT))

            print("Connected to ESP32")
            return True

        except:
            self.socket = None
            print("ESP32 connection failed")
            return False

    def send_command(self, command):
        if not self.socket:
            if not self.connect_esp32():
                return False

        try:
            self.socket.send((command + '\n').encode())
            self.socket.recv(1024)
            return True

        except:
            self.socket = None
            return False

    # ---------------- FINGER DETECTION ----------------

    def get_finger_states(self, landmarks):
        lm = [[p.x, p.y] for p in landmarks]

        fingers = []

        # Only Index, Middle, Ring
        tips = [8, 12, 16]
        pips = [6, 10, 14]

        for tip, pip in zip(tips, pips):
            if lm[tip][1] < lm[pip][1]:
                fingers.append(1)
            else:
                fingers.append(0)

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
        brightness = max(0, min(255, brightness))

        return brightness

    # ---------------- CLEANUP ----------------

    def cleanup(self):
        if self.socket:
            self.socket.close()


# ---------------- MAIN ----------------

def main():
    cap = cv2.VideoCapture(0)
    controller = GestureController()

    controller.connect_esp32()

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
            brightness = 150  # default

            for hand in results.multi_hand_landmarks:

                mp_drawing.draw_landmarks(
                    frame,
                    hand,
                    mp_hands.HAND_CONNECTIONS
                )

                landmarks = hand.landmark

                fingers = controller.get_finger_states(landmarks)
                hands_data.append(fingers)

                brightness = controller.palm_brightness(landmarks)

            # ---------------- ACTION LOCK ----------------
            if current_time - controller.last_action_time > controller.action_delay:

                # -------- SINGLE HAND → TURN ON --------
                if len(hands_data) == 1:

                    fingers = hands_data[0]

                    # ALL ON
                    if sum(fingers) == 3:
                        controller.current_led_state = [1, 1, 1]

                    else:
                        for i in range(3):
                            if fingers[i] == 1:
                                controller.current_led_state[i] = 1

                # -------- TWO HANDS → TURN OFF --------
                elif len(hands_data) == 2:

                    h1, h2 = hands_data

                    # Find fist hand
                    if sum(h1) == 0:
                        off_hand = h1
                        on_hand = h2
                    elif sum(h2) == 0:
                        off_hand = h2
                        on_hand = h1
                    else:
                        on_hand = None

                    if on_hand:

                        # ALL OFF
                        if sum(on_hand) == 3:
                            controller.current_led_state = [0, 0, 0]

                        else:
                            for i in range(3):
                                if on_hand[i] == 1:
                                    controller.current_led_state[i] = 0

                # -------- SEND COMMAND --------
                led_string = ",".join(map(str, controller.current_led_state))
                command = f"LED:{led_string},{brightness}"

                controller.send_command(command)

                print(f"LED State: {controller.current_led_state}")

                controller.last_action_time = current_time

        cv2.imshow("ESP32 Gesture Smart Switch", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break
        elif key == ord('c'):
            controller.send_command("CLEAR")
        elif key == ord('t'):
            controller.send_command("TEST")

    controller.cleanup()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()