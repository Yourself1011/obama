// Basic ESP32 Test Code
// Blinks onboard LED and sends serial output

#define LED_BUILTIN 2  // Most ESP32 boards have onboard LED at GPIO 2

void setup() {
  // Initialize Serial Monitor
  Serial.begin(115200);
  delay(1000); // Give some time to establish connection

  // Initialize LED pin as output
  pinMode(LED_BUILTIN, OUTPUT);

  Serial.println("ESP32 Test Code Running...");
}

void loop() {
  // Turn LED on
  digitalWrite(LED_BUILTIN, HIGH);
  Serial.println("LED ON");
  delay(100);

  // Turn LED off
  digitalWrite(LED_BUILTIN, LOW);
  Serial.println("LED OFF");
  delay(100);
}
