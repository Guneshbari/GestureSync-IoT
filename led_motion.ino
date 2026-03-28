#define BLYNK_TEMPLATE_ID "TMPL3RvORlrpn"
#define BLYNK_TEMPLATE_NAME "SL Project"
#define BLYNK_AUTH_TOKEN "uQcOFSmKoKYwxHxJ-2trKV5tkCDYjqnU"

#include <BlynkSimpleEsp32.h>
#include <WiFi.h>

// -------- WIFI --------
const char *ssid = "iPhone";
const char *password = "1234567890";

// -------- LED PINS --------
int ledPins[] = {13, 14, 27};
int numLeds = 3;

// -------- MOTOR PIN --------
int motorPin = 26;

// -------- PWM SETTINGS --------
int freq = 5000;
int resolution = 8;

// -------- STATE --------
int ledState[3] = {0, 0, 0};
int brightness = 150;

// -------- SETUP --------
void setup() {
  Serial.begin(115200);

  // LED SETUP
  for (int i = 0; i < numLeds; i++) {
    ledcAttach(ledPins[i], freq, resolution);
    ledcWrite(ledPins[i], 0);
  }

  // MOTOR SETUP
  ledcAttach(motorPin, freq, resolution);
  ledcWrite(motorPin, 0);

  // Blynk
  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, password);

  Serial.println("System Ready!");
}

// -------- APPLY LED STATE --------
void applyLEDs() {
  for (int i = 0; i < numLeds; i++) {
    ledcWrite(ledPins[i], ledState[i] ? brightness : 0);
  }

  // Sync UI
  Blynk.virtualWrite(V0, ledState[0]);
  Blynk.virtualWrite(V1, ledState[1]);
  Blynk.virtualWrite(V2, ledState[2]);

  int allState = (ledState[0] && ledState[1] && ledState[2]) ? 1 : 0;
  Blynk.virtualWrite(V3, allState);
}

// -------- BLYNK HANDLERS --------

// Light 1
BLYNK_WRITE(V0) {
  ledState[0] = param.asInt();
  applyLEDs();
}

// Light 2
BLYNK_WRITE(V1) {
  ledState[1] = param.asInt();
  applyLEDs();
}

// Light 3
BLYNK_WRITE(V2) {
  ledState[2] = param.asInt();
  applyLEDs();
}

// ALL LIGHTS
BLYNK_WRITE(V3) {
  int val = param.asInt();
  for (int i = 0; i < numLeds; i++) {
    ledState[i] = val;
  }
  applyLEDs();
}

// Brightness
BLYNK_WRITE(V4) {
  brightness = param.asInt();
  applyLEDs();
}

// -------- MOTOR CONTROL --------
BLYNK_WRITE(V5) {
  int val = param.asInt();
  ledcWrite(motorPin, val ? 255 : 0);

  Serial.print("Motor State: ");
  Serial.println(val ? "ON" : "OFF");
}

// -------- LOOP --------
void loop() { Blynk.run(); }