#define BLYNK_TEMPLATE_ID "TMPL3RvORlrpn"
#define BLYNK_TEMPLATE_NAME "SL Project"
#define BLYNK_AUTH_TOKEN "uQcOFSmKoKYwxHxJ-2trKV5tkCDYjqnU"
#include <BlynkSimpleEsp32.h>
#include <WiFi.h>


// -------- WIFI --------
const char *ssid = "iPhone";
const char *password = "1234567890";

// -------- LED PINS --------
int ledPins[] = {5, 18, 19};
int numLeds = 3;

// -------- STATE --------
int ledState[3] = {0, 0, 0};
int brightness = 150;

// -------- SETUP --------
void setup() {
  Serial.begin(115200);

  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
    analogWrite(ledPins[i], 0);
  }

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, password);
  Serial.println("System Ready!");
}

// -------- APPLY LED STATE --------
void applyLEDs() {
  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], ledState[i] ? brightness : 0);
  }

  // Keep Blynk UI in sync
  Blynk.virtualWrite(V0, ledState[0]);
  Blynk.virtualWrite(V1, ledState[1]);
  Blynk.virtualWrite(V2, ledState[2]);

  int allState = (ledState[0] && ledState[1] && ledState[2]) ? 1 : 0;
  Blynk.virtualWrite(V3, allState);
}

// -------- BLYNK HANDLERS --------

// Individual LED controls
BLYNK_WRITE(V0) {
  ledState[0] = param.asInt();
  applyLEDs();
}

BLYNK_WRITE(V1) {
  ledState[1] = param.asInt();
  applyLEDs();
}

BLYNK_WRITE(V2) {
  ledState[2] = param.asInt();
  applyLEDs();
}

// Master toggle (all on / all off)
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

// -------- LOOP --------
void loop() { Blynk.run(); }
