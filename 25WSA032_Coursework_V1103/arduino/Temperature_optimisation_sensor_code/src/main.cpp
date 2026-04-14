#include <Arduino.h>
#include <math.h>

const int PIN_TEMP_SENSOR = A0;
const int B_VALUE = 4275;
const int R0 = 100000;

#define NUM_SAMPLES 60

float tempSamples[NUM_SAMPLES];
float currentRate = 1.0;

float read_temperature() {
    int raw = analogRead(PIN_TEMP_SENSOR);
    if (raw <= 0) {
        Serial.println("ERROR: bad sensor reading, check wiring");
        return -999.0;
    }
    float R = (1023.0 / (float)raw - 1.0) * R0;
    float temp = 1.0 / (log(R / R0) / B_VALUE + 1.0 / 298.15) - 273.15;
    return temp;
}

void collect_temperature_data(float sampleRateHz) {
    unsigned long intervalMs = (unsigned long)(1000.0 / sampleRateHz);
    for (int i = 0; i < NUM_SAMPLES; i++) {
        float t = read_temperature();
        if (t < -50.0 || t > 150.0) {
            t = (i > 0) ? tempSamples[i - 1] : 20.0;
        }
        tempSamples[i] = t;
        delay(intervalMs);
    }
}

// applies DFT to tempSamples[] and stores frequency for each bin
// uses equations 3.1 to 3.5 from the task spec
void apply_dft(float freqArray[], int n, float sampleRateHz) {
    int halfN = n / 2;
    for (int k = 0; k < halfN; k++) {
        float real_k = 0.0;
        float imag_k = 0.0;
        for (int i = 0; i < n; i++) {
            float angle = (2.0 * M_PI * k * i) / (float)n;
            real_k +=  tempSamples[i] * cos(angle);
            imag_k += -tempSamples[i] * sin(angle);
        }
        // frequency value for bin k (Eq 3.2)
        freqArray[k] = ((float)k * sampleRateHz) / (float)n;
    }
}

void setup() {
    Serial.begin(9600);
    Serial.println("=== Temperature Monitor ===");
}

void loop() {
    collect_temperature_data(currentRate);

    int halfN = NUM_SAMPLES / 2;
    float freqArray[halfN];
    apply_dft(freqArray, NUM_SAMPLES, currentRate);

    Serial.println("DFT complete");
}