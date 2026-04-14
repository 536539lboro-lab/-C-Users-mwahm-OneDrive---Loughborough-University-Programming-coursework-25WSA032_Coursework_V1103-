#include <Arduino.h>
#include <math.h>

const int PIN_TEMP_SENSOR = A0;
const int B_VALUE = 4275;
const int R0 = 100000;

#define NUM_SAMPLES 60

const float FREQ_HIGH  = 0.5;
const float FREQ_MED   = 0.1;
const int   IDLE_LIMIT = 5;

#define ACTIVE     0
#define IDLE_MODE  1
#define POWER_DOWN 2

float tempSamples[NUM_SAMPLES];
float currentRate  = 1.0;
int   currentMode  = ACTIVE;
int   idleCount    = 0;

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
        freqArray[k] = ((float)k * sampleRateHz) / (float)n;
    }
}

// decides which power mode to use based on dominant frequency
int decide_power_mode(float dominantFreqHz) {
    int newMode;
    if (dominantFreqHz > FREQ_HIGH) {
        // temperature changing fast - stay in active mode
        newMode = ACTIVE;
        idleCount = 0;
    } else if (dominantFreqHz > FREQ_MED) {
        // moderate changes - idle is enough
        newMode = IDLE_MODE;
        idleCount++;
    } else {
        // very stable - count towards power down
        newMode = IDLE_MODE;
        idleCount++;
    }
    if (idleCount >= IDLE_LIMIT) {
        newMode = POWER_DOWN;
    }
    return newMode;
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

    // find dominant frequency - skip k=0 (that's just the DC average)
    float dominantFreq = 0.0;
    float maxMag = 0.0;
    for (int k = 1; k < halfN; k++) {
        float real_k = 0.0, imag_k = 0.0;
        for (int n = 0; n < NUM_SAMPLES; n++) {
            float angle = (2.0 * M_PI * k * n) / NUM_SAMPLES;
            real_k +=  tempSamples[n] * cos(angle);
            imag_k += -tempSamples[n] * sin(angle);
        }
        float mag = sqrt(real_k * real_k + imag_k * imag_k);
        if (mag > maxMag) { maxMag = mag; dominantFreq = freqArray[k]; }
    }

    currentMode = decide_power_mode(dominantFreq);

    Serial.print("Mode: ");
    if      (currentMode == ACTIVE)    Serial.println("ACTIVE");
    else if (currentMode == IDLE_MODE) Serial.println("IDLE");
    else                               Serial.println("POWER_DOWN");
}