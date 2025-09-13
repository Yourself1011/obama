#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Audio.h>

// Your WiFi
const char* ssid = "HackTheNorth";
const char* password = "HTN2025!";

// API endpoints
const char* generate_url = "https://example.com/api/generate";  // triggers mp3 generation
String mp3_url = "";  // will be filled from JSON

// I2S pins (adjust for your wiring)
#define I2S_BCLK 26
#define I2S_LRC 25
#define I2S_DOUT 22

Audio audio;

void setup() {
  Serial.begin(115200);

  // WiFi connect
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");

  // Step 1: Trigger MP3 generation
  HTTPClient http;
  http.begin(generate_url);
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    Serial.println("Generation response:");
    Serial.println(payload);

    // Step 2: Parse JSON for mp3_url
    StaticJsonDocument<1024> doc;
    DeserializationError err = deserializeJson(doc, payload);
    if (!err && doc["mp3_url"]) {
      mp3_url = String((const char*)doc["mp3_url"]);
      Serial.println("MP3 URL: " + mp3_url);
    } else {
      Serial.println("Could not parse mp3_url!");
    }
  } else {
    Serial.printf("HTTP request failed, code: %d\n", httpCode);
  }
  http.end();

  // Step 3: Setup I2S output
  audio.setPinout(I2S_BCLK, I2S_LRC, I2S_DOUT);
  audio.setVolume(18); // 0–21

  // Step 4: Stream MP3 if we got a URL
  if (mp3_url.length() > 0) {
    Serial.println("Starting playback...");
    audio.connecttohost(mp3_url.c_str());
  }
}

void loop() {
  audio.loop();  // must be called repeatedly
}

// Optional debug callback
void audio_info(const char* info) {
  Serial.print("Audio info: ");
  Serial.println(info);
}
