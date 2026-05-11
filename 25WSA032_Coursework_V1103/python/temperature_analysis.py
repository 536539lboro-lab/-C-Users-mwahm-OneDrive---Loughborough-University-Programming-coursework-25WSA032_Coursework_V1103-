"""
Reads temperature and frequency data recorded from the Arduino
and produces 5 plots for analysis.

The temperature dropped from around 38C to 26C over 145 seconds
as the sensor cooled down after being near a heat source. The signal
was smooth with no sudden jumps or noise.

The DFT showed a large spike at 0Hz which is the DC component
representing the average temperature. There were small magnitudes
at very low frequencies matching the slow cooling trend. No high
frequency components were present.

The system switched to IDLE mode after the first cycle because the
temperature was changing slowly rather than oscillating rapidly.
This is correct behaviour for this type of signal, though it means
the system might stay in IDLE even during large but gradual changes.

The 30 data points at 0.2Hz were enough to capture the cooling curve
clearly. More data points would not have changed the overall shape.
"""

# Reads CSV data recorded from Arduino and produces plots

import csv
import matplotlib.pyplot as plt

# lists to store the data
time_data   = []
temp_data   = []
freq_data   = []
mag_data    = []

# read the CSV file
with open('python/temperature_data.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        time_data.append(float(row['Time(s)']))
        temp_data.append(float(row['Temperature(C)']))
        freq_data.append(float(row['Frequency(Hz)']))
        mag_data.append(float(row['Magnitude']))

# print first few rows to check it loaded correctly
print(f"Loaded {len(time_data)} rows of data")
print(f"Time range: {time_data[0]}s to {time_data[-1]}s")
print(f"Temperature range: {min(temp_data)}C to {max(temp_data)}C")

# plot 1 - temperature vs time
plt.figure()
plt.plot(time_data, temp_data, color='steelblue', marker='o', markersize=3)
plt.xlabel('Time (s)')
plt.ylabel('Temperature (C)')
plt.title('Temperature vs Time')
plt.grid(True)
plt.tight_layout()
plt.savefig('python/plot1_temperature_vs_time.png')

# plot 2 - magnitude vs frequency
# including DC component at k=0 which shows the average temperature level
plt.figure()
plt.bar(freq_data, mag_data, width=0.01, color='steelblue')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Magnitude')
plt.title('Magnitude vs Frequency (DFT Result)')
plt.grid(True)
plt.tight_layout()
plt.savefig('python/plot2_magnitude_vs_frequency.png')

# plot 3 - smoothed temperature vs time using moving average
# window size of 5 means each point is averaged with 2 either side
window = 5
smoothed = []
for i in range(len(temp_data)):
    start = max(0, i - window // 2)
    end   = min(len(temp_data), i + window // 2 + 1)
    smoothed.append(sum(temp_data[start:end]) / (end - start))

plt.figure()
plt.plot(time_data, temp_data, color='steelblue', label='Original', alpha=0.5)
plt.plot(time_data, smoothed, color='red', label='Smoothed (MA)')
plt.xlabel('Time (s)')
plt.ylabel('Temperature (C)')
plt.title('Original vs Smoothed Temperature')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('python/plot3_smoothed_temperature.png')

# plot 4 - histogram of temperature readings
plt.figure()
plt.hist(temp_data, bins=10, color='steelblue', edgecolor='black')
plt.xlabel('Temperature (C)')
plt.ylabel('Count')
plt.title('Histogram of Temperature Readings')
plt.grid(True)
plt.tight_layout()
plt.savefig('python/plot4_histogram.png')

# plot 5 - temperature change rate vs time
# calculates how much temperature changed between each sample
change_rate = []
change_time = []
for i in range(1, len(temp_data)):
    rate = temp_data[i] - temp_data[i - 1]
    change_rate.append(rate)
    change_time.append(time_data[i])

plt.figure()
plt.plot(change_time, change_rate, color='steelblue', marker='o', markersize=3)
plt.xlabel('Time (s)')
plt.ylabel('Temperature Change Rate (C)')
plt.title('Temperature Change Rate vs Time')
plt.axhline(y=0, color='red', linestyle='--', alpha=0.5)
plt.grid(True)
plt.tight_layout()
plt.savefig('python/plot5_change_rate.png')

plt.show()