#include <Arduino.h>
#include <math.h>

// put function declarations here:
const int PIN_TEMP_SENSOR = A0;
const long B_VALUE        = 4275;
const long R0             = 100000L;

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

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  Serial.println(F("=== Temperature Monitor ==="));
}

void loop() {
  float t = read_temperature();
  Serial.print(F("Temperature: "));
  Serial.print(t, 2);
  Serial.println(F(" C"));
  delay(1000);
}

