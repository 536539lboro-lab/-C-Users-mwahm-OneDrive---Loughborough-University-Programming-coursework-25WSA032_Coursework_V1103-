# temperature_analysis.py
# 25WSA032 Task 4 - Temperature Data Analysis
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