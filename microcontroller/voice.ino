#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "Audio.h"  // From ESP32-audioI2S library

// Replace with your Wi-Fi credentials
const char* ssid = "HackTheNorth";
const char* password = "HTN2025!";

// Endpoints
const char* gen_url = "http://example.com/api/generate";
String fetch_url = "http://example.com/api/fetch/";

// Audio player
Audio audio;

void setup() {
  Serial.begin(115200);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println(" Connected!");

  // Step 1: Initiate generation
  HTTPClient http;
  http.begin(gen_url);
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    Serial.println("Generation Response: " + payload);

    // Parse JSON
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    String id = doc["id"];
    fetch_url += id;
  } else {
    Serial.println("Generation request failed!");
    return;
  }
  http.end();

  // Step 2: Fetch MP3 URL
  http.begin(fetch_url);
  httpCode = http.GET();
  String mp3url;
  if (httpCode == 200) {
    String payload = http.getString();
    Serial.println("Fetch Response: " + payload);

    // Parse JSON
    DynamicJsonDocument doc(1024);
    deserializeJson(doc, payload);
    mp3url = doc["url"].as<String>();
    Serial.println("MP3 URL: " + mp3url);
  } else {
    Serial.println("Fetch request failed!");
    return;
  }
  http.end();

  // Step 3: Play MP3 from URL
  // I2S pin setup (adjust for your wiring + amp)
  audio.setPinout(26, 25, 22); // BCLK, LRC, DOUT
  audio.setVolume(15);         // 0...21
  audio.connecttohost(mp3url.c_str());
}

void loop() {
  // Keep feeding audio stream
  audio.loop();
}
