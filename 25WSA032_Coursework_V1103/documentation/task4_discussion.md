# Task 4 - Temperature Data Analysis Discussion

## Data Collection
Temperature data was recorded using the Arduino adaptive monitoring system
built in Task 2. The sensor was placed near a PS4 vent to generate a
meaningful temperature change. Data was recorded as CSV via the Serial Monitor.

## Time-domain behaviour
The temperature dropped from around 38C to 26C over 145 seconds as the
sensor cooled down after being near a heat source. The signal was smooth
with no sudden jumps or noise.

## Frequency-domain behaviour
The DFT showed a large spike at 0Hz which is the DC component representing
the average temperature. There were small magnitudes at very low frequencies
matching the slow cooling trend. No high frequency components were present.

## System behaviour
The system switched to IDLE mode after the first cycle because the temperature
was changing slowly rather than oscillating rapidly. This is correct behaviour
for this type of signal, though it means the system might stay in IDLE even
during large but gradual changes.

## Data quality
The 30 data points at 0.2Hz were enough to capture the cooling curve clearly.
More data points would not have changed the overall shape.