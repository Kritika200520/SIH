/*
 * Robo Raksha — Robot Firmware (Team Member A)
 * Microcontroller: ESP32 / Arduino
 * Reads sensors (flame, sound, vibration, ultrasonic distance)
 * and POSTs JSON telemetry to Person 1's Server.
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

// Wi-Fi Configuration
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Server Endpoint (Person 1's Laptop IP)
const char* SERVER_TELEMETRY_URL = "http://192.168.1.100:5000/api/telemetry";

// Pin Definitions
#define FLAME_PIN 34
#define SOUND_PIN 35
#define VIBRATION_PIN 32
#define TRIG_PIN 5
#define ECHO_PIN 18

void setup() {
  Serial.begin(115200);
  pinMode(FLAME_PIN, INPUT);
  pinMode(SOUND_PIN, INPUT);
  pinMode(VIBRATION_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  Serial.println("Robo Raksha Firmware Initializing...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWi-Fi Connected!");
}

int readDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH);
  return duration * 0.034 / 2;
}

void loop() {
  int flameVal = digitalRead(FLAME_PIN) == LOW ? 1 : 0; // Active low on many flame modules
  int soundVal = analogRead(SOUND_PIN);
  int vibrationVal = digitalRead(VIBRATION_PIN);
  int distanceVal = readDistanceCM();

  // Print to Serial Monitor (Week 1-2 Task)
  Serial.printf("Sensors -> Flame: %d | Sound: %d | Vibration: %d | Distance: %d cm\n",
                flameVal, soundVal, vibrationVal, distanceVal);

  if (WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(SERVER_TELEMETRY_URL);
    http.addHeader("Content-Type", "application/json");

    StaticJsonDocument<200> doc;
    doc["flame"] = flameVal;
    doc["sound"] = soundVal;
    doc["vibration"] = vibrationVal;
    doc["distance_cm"] = distanceVal;

    String jsonString;
    serializeJson(doc, jsonString);

    int httpCode = http.POST(jsonString);
    if (httpCode > 0) {
      Serial.printf("Posted Telemetry -> Server HTTP %d\n", httpCode);
    } else {
      Serial.printf("HTTP POST Error: %s\n", http.errorToString(httpCode).c_str());
    }
    http.end();
  }

  delay(1000);
}
