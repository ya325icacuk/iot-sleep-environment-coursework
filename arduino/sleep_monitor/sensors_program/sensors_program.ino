/*
 * Sleep Environment Monitor
 * Board: Heltec WiFi LoRa 32 V3 (ESP32-S3)
 *
 * Sensors:
 *   - KY-015 DHT11 (temp & humidity)  -> GPIO 7  (digital)
 *   - ELB0604 photoresistor (light)   -> GPIO 1  (digital)
 *   - KY-038 microphone (sound)       -> GPIO 2  (analog)
 *
 * Sends 5 comma-separated values over USB Serial every 1 minute:
 *   temperature_c, humidity_pct, light_detected, sound_avg, sound_peak
 *
 * The Python notebook adds timestamps from the laptop clock.
 * Study period: 9-22 February 2026 (14 nights).
 */

#include "DHT.h"

// === PINS ===
#define DHT_PIN    7
#define LIGHT_PIN  1
#define SOUND_PIN  2
#define DHT_TYPE   DHT11

// === SETTINGS ===
const unsigned long LOG_INTERVAL_MS = 60000;  // Log every 60 seconds
const unsigned long SOUND_SAMPLE_MS = 5;      // Sample sound every 5ms

// === GLOBALS ===
DHT dht(DHT_PIN, DHT_TYPE);

unsigned long lastLogTime    = 0;
unsigned long lastSampleTime = 0;

// Sound tracking (resets each minute)
long soundSum   = 0;
long soundCount = 0;
int  soundPeak  = 0;

// ======================== SETUP =================================
void setup() {
  Serial.begin(115200);
  delay(3000);  // Let serial + DHT11 settle

  dht.begin();
  delay(2000);
  pinMode(LIGHT_PIN, INPUT);
  analogReadResolution(12);  // 0-4095 range for sound sensor

  Serial.println("// Sleep Environment Monitor ready");
  Serial.println("// Format: temperature_c,humidity_pct,light_detected,sound_avg,sound_peak");

  lastLogTime    = millis();
  lastSampleTime = millis();
}

// ======================== MAIN LOOP =============================
void loop() {
  unsigned long now = millis();

  // --- Continuously sample sound ---
  if (now - lastSampleTime >= SOUND_SAMPLE_MS) {
    lastSampleTime = now;
    int val = analogRead(SOUND_PIN);
    soundSum += val;
    soundCount++;
    if (val > soundPeak) {
      soundPeak = val;
    }
  }

  // --- Every 60 seconds, read all sensors and send CSV line ---
  if (now - lastLogTime >= LOG_INTERVAL_MS) {
    lastLogTime = now;

    // Read DHT11 (retry up to 3 times)
    float temp     = NAN;
    float humidity  = NAN;
    for (int i = 0; i < 3; i++) {
      temp     = dht.readTemperature();
      humidity = dht.readHumidity();
      if (!isnan(temp) && !isnan(humidity)) break;
      delay(500);
    }

    // Read light sensor (inverted: ELB0604 outputs 0 for light, 1 for dark)
    // Flip so that 1 = light detected, 0 = dark
    int light = !digitalRead(LIGHT_PIN);

    // Compute sound average
    int soundAvg = (soundCount > 0) ? (int)(soundSum / soundCount) : 0;

    // Send CSV line: temp,humidity,light,sound_avg,sound_peak
    if (!isnan(temp)) {
      Serial.print(temp, 1);
    } else {
      Serial.print("ERR");
    }
    Serial.print(",");

    if (!isnan(humidity)) {
      Serial.print(humidity, 1);
    } else {
      Serial.print("ERR");
    }
    Serial.print(",");

    Serial.print(light);
    Serial.print(",");
    Serial.print(soundAvg);
    Serial.print(",");
    Serial.println(soundPeak);

    // Reset sound tracking
    soundSum   = 0;
    soundCount = 0;
    soundPeak  = 0;
  }
}