#include <Arduino.h>
#include <math.h>

const int PIN_TEMP_SENSOR = A0;
const int B_VALUE = 4275;
const int R0 = 100000;
const float SAMPLE_RATE_MIN = 0.033;
const float SAMPLE_RATE_MED = 0.2;
const float SAMPLE_RATE_MAX = 1.0;

#define NUM_SAMPLES 60

const float FREQ_HIGH  = 0.5;
const float FREQ_MED   = 0.1;
const int   IDLE_LIMIT = 5;

#define ACTIVE     0
#define IDLE_MODE  1
#define POWER_DOWN 2

#define MA_WINDOW 10
float maBuffer[MA_WINDOW];
int   maIndex = 0;

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
    float totalVariation = 0.0;
    for (int i = 1; i < NUM_SAMPLES; i++) {
        totalVariation += fabs(tempSamples[i] - tempSamples[i - 1]);
    }
    maBuffer[maIndex] = totalVariation;
    maIndex++;
    if (maIndex >= MA_WINDOW) maIndex = 0;
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
// sends time and frequency domain data to serial monitor
// format: Time(s), Temperature(C), Frequency(Hz), Magnitude
void send_data_to_pc(float freqArray[], float sampleRateHz, int n) {
    int halfN = n / 2;
    float intervalSecs = 1.0 / sampleRateHz;
    for (int k = 0; k < halfN; k++) {
        float timeStamp = (float)k * intervalSecs;
        float tempVal = (k < NUM_SAMPLES) ? tempSamples[k] : 0.0;
        float real_k = 0.0, imag_k = 0.0;
        for (int i = 0; i < n; i++) {
            float angle = (2.0 * M_PI * k * i) / (float)n;
            real_k +=  tempSamples[i] * cos(angle);
            imag_k += -tempSamples[i] * sin(angle);
        }
        float magnitude = sqrt(real_k * real_k + imag_k * imag_k);
        Serial.print(timeStamp);     Serial.print(", ");
        Serial.print(tempVal);       Serial.print(", ");
        Serial.print(freqArray[k]);  Serial.print(", ");
        Serial.println(magnitude);
    }
}
void adjust_sampling_rate(float dominantFreqHz) {
    float nyquist = 2.0 * dominantFreqHz;
    if (currentMode == ACTIVE) {
        currentRate = nyquist;
        if (currentRate < SAMPLE_RATE_MAX) currentRate = SAMPLE_RATE_MAX;
        if (currentRate > 4.0) currentRate = 4.0;
    } else if (currentMode == IDLE_MODE) {
        currentRate = SAMPLE_RATE_MED;
        if (nyquist > currentRate) currentRate = SAMPLE_RATE_MED;
    } else {
        currentRate = SAMPLE_RATE_MIN;
    }
}

void setup() {
    Serial.begin(9600);
    Serial.println("=== Temperature Monitor ===");
}

// predicts future variation by averaging last MA_WINDOW cycles
float moving_average_prediction() {
    float sum = 0.0;
    for (int i = 0; i < MA_WINDOW; i++) {
        sum += maBuffer[i];
    }
    return sum / (float)MA_WINDOW;
}

void loop() {
    // step 1: collect temperature data for this cycle
    collect_temperature_data(currentRate);

    // step 2: run DFT to get frequency components
    int halfN = NUM_SAMPLES / 2;
    float freqArray[halfN];
    apply_dft(freqArray, NUM_SAMPLES, currentRate);

    // step 3: find dominant frequency - skip k=0 (DC average, not useful)
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

    // step 4: predict future variation using moving average
    float predictedVariation = moving_average_prediction();

    // step 5: decide power mode based on dominant frequency
    currentMode = decide_power_mode(dominantFreq);

    // step 6: adjust sampling rate to satisfy Nyquist
    adjust_sampling_rate(dominantFreq);

    // step 7: send data to PC
    send_data_to_pc(freqArray, currentRate, NUM_SAMPLES);

    Serial.print("Dominant frequency: ");
    Serial.print(dominantFreq);
    Serial.println(" Hz");
    Serial.print("Predicted variation: ");
    Serial.print(predictedVariation);
    Serial.println(" C");
    Serial.print("Mode: ");
    if      (currentMode == ACTIVE)    Serial.println("ACTIVE");
    else if (currentMode == IDLE_MODE) Serial.println("IDLE");
    else                               Serial.println("POWER_DOWN");
    Serial.print("Sampling rate: ");
    Serial.print(currentRate);
    Serial.println(" Hz");
    Serial.println("---");
}