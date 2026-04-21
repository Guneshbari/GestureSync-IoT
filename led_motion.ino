#define BLYNK_TEMPLATE_ID "TMPL36W9Mprce"
#define BLYNK_TEMPLATE_NAME "SL Project"
#define BLYNK_AUTH_TOKEN "Pyg4QC6R_zPxW6HeYkttfLLW3-47q1aF"

#include <BlynkSimpleEsp32.h>
#include <WiFi.h>


// -------- WIFI --------
const char *ssid = "iPhone";
const char *password = "1234567890";

// -------- LED PINS --------
int ledPins[] = {13, 14, 27};
int numLeds = 3;

// -------- MOTOR PIN --------
int motorPin = 33;

// -------- STATE --------
int ledState[3] = {0, 0, 0};
int brightness = 150;

// -------- SETUP --------
void setup() {
  Serial.begin(115200);

  // Set pins as OUTPUT (IMPORTANT)
  for (int i = 0; i < numLeds; i++) {
    pinMode(ledPins[i], OUTPUT);
  }
  pinMode(motorPin, OUTPUT);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nConnected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  Blynk.begin(BLYNK_AUTH_TOKEN, ssid, password);

  Serial.println("System Ready!");
}

// -------- SYNC ON CONNECT --------
BLYNK_CONNECTED() {
  Serial.println("Blynk Connected!");
  Blynk.syncAll();
}

// -------- APPLY LED STATE --------
void applyLEDs() {
  Serial.println("Applying LED states...");

  for (int i = 0; i < numLeds; i++) {
    analogWrite(ledPins[i], ledState[i] ? brightness : 0);
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
  int val = param.asInt();
  Serial.print("V0: ");
  Serial.println(val);

  ledState[0] = val;
  applyLEDs();
}

// Light 2
BLYNK_WRITE(V1) {
  int val = param.asInt();
  Serial.print("V1: ");
  Serial.println(val);

  ledState[1] = val;
  applyLEDs();
}

// Light 3
BLYNK_WRITE(V2) {
  int val = param.asInt();
  Serial.print("V2: ");
  Serial.println(val);

  ledState[2] = val;
  applyLEDs();
}

// ALL LIGHTS
BLYNK_WRITE(V3) {
  int val = param.asInt();
  Serial.print("V3 (ALL): ");
  Serial.println(val);

  for (int i = 0; i < numLeds; i++) {
    ledState[i] = val;
  }
  applyLEDs();
}

// Brightness
BLYNK_WRITE(V4) {
  brightness = param.asInt();
  Serial.print("Brightness: ");
  Serial.println(brightness);

  applyLEDs();
}

// -------- MOTOR CONTROL --------
BLYNK_WRITE(V5) {
  int val = param.asInt();
  Serial.print("Motor: ");
  Serial.println(val);

  digitalWrite(motorPin, val ? HIGH : LOW);
}

// -------- LOOP --------
void loop() { Blynk.run(); }