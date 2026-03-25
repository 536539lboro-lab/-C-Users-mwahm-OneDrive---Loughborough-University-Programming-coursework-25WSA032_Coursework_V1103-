#include <Arduino.h>
#include <math.h>

const int PIN_TEMP_SENSOR = A0;
const long B_VALUE        = 4275;
const long R0             = 100000L;

#define NUM_SAMPLES 60

float tempSamples[NUM_SAMPLES];
float currentRate = 1.0f; // Hz

float read_temperature() {
    int raw = analogRead(PIN_TEMP_SENSOR);
    if (raw <= 0) {
        Serial.println(F("ERROR: Sensor read invalid. Check wiring."));
        return -999.0f;
    }
    float R    = (1023.0f / (float)raw - 1.0f) * R0;
    float temp = 1.0f / (log(R / R0) / B_VALUE + 1.0f / 298.15f) - 273.15f;
    return temp;
}

void collect_temperature_data(float sampleRateHz) {
    unsigned long intervalMs = (unsigned long)(1000.0f / sampleRateHz);
    Serial.print(F("Collecting "));
    Serial.print(NUM_SAMPLES);
    Serial.print(F(" samples at "));
    Serial.print(sampleRateHz, 3);
    Serial.println(F(" Hz ..."));

    for (int i = 0; i < NUM_SAMPLES; i++) {
        float t = read_temperature();
        if (t < -50.0f || t > 150.0f) {
            t = (i > 0) ? tempSamples[i - 1] : 20.0f;
        }
        tempSamples[i] = t;
        delay(intervalMs);
    }
}

void setup() {
    Serial.begin(9600);
    Serial.println(F("=== Temperature Monitor ==="));
}

void loop() {
    collect_temperature_data(currentRate);
    Serial.println(F("Collection complete."));
}