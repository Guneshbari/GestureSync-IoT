#include <WiFi.h>

const char *ssid = "iPhone";
const char *password = "1234567890";

WiFiServer server(80);

// LED pins - using different pins that work better
int ledPins[] = {5, 18, 19, 21, 22}; // your 5 LEDs
int numLeds = 5;

// PWM settings
int freq = 5000;
int resolution = 8;

void setup() {
  Serial.begin(115200);

  // Setup each LED for PWM using ESP32 Board Manager 3.0 API
  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
    ledcAttach(ledPins[i], freq, resolution);
    analogWrite(ledPins[i], 0); // start OFF
  }

  Serial.println("Testing LEDs on startup...");
  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], 100);
    delay(200);
    analogWrite(ledPins[i], 0);
    delay(100);
  }
  Serial.println("LED test complete");

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("ESP32 IP: ");
  Serial.println(WiFi.localIP());

  server.begin();
  Serial.println("TCP Server started on port 80");
}

void loop() {
  WiFiClient client = server.available();

  if (client) {
    Serial.println("New client connected!");

    while (client.connected()) {
      if (client.available()) {
        String request = client.readStringUntil('\n');
        request.trim();

        Serial.println("Received: " + request);

        // Parse different commands
        if (request.startsWith("FINGERS:")) {
          // Format: "FINGERS:count,brightness"
          int comma = request.indexOf(',');
          if (comma > 0) {
            int fingerCount = request.substring(8, comma).toInt();
            int brightness = request.substring(comma + 1).toInt();

            controlFingerLEDs(fingerCount, brightness);
            client.println("OK");
          }
        } else if (request == "CLEAR") {
          turnOffAllLEDs();
          client.println("CLEARED");
        } else if (request == "TEST") {
          testAllLEDs();
          client.println("TESTED");
        } else {
          // Simple brightness control
          int brightness = request.toInt();
          if (brightness >= 0 && brightness <= 255) {
            setAllLEDs(brightness);
            client.println("OK");
          }
        }
      }
    }

    client.stop();
    Serial.println("Client disconnected");
  }
}

void controlFingerLEDs(int fingerCount, int brightness) {
  fingerCount = constrain(fingerCount, 0, 5);
  brightness = constrain(brightness, 0, 255);

  Serial.printf("Fingers: %d, Brightness: %d\n", fingerCount, brightness);

  for (int i = 0; i < numLeds; i++) {
    if (i < fingerCount) {
      analogWrite(ledPins[i], brightness);
    } else {
      analogWrite(ledPins[i], 0);
    }
  }
}

void setAllLEDs(int brightness) {
  brightness = constrain(brightness, 0, 255);
  Serial.printf("All LEDs brightness: %d\n", brightness);

  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], brightness);
  }
}

void turnOffAllLEDs() {
  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], 0);
  }
  Serial.println("All LEDs OFF");
}

void testAllLEDs() {
  Serial.println("Testing all LEDs...");

  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], 150);
    delay(300);
    analogWrite(ledPins[i], 0);
    delay(100);
  }

  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], 100);
  }
  delay(1000);

  turnOffAllLEDs();
  Serial.println("Test complete");
}
