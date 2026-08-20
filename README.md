# Greencell Mobility (NueGo) — EV Battery Voltage Analysis & Interactive Dashboard

An end-to-end time-series analysis of electric-bus battery voltage data for **Greencell Mobility (NueGo)**, combining Python-based statistical and signal-processing analysis with an interactive Plotly.js web dashboard.

The project analyzes **21,919 battery-voltage records** collected between **26 June 2024 and 3 July 2024**, identifying recurring charge/discharge patterns, long-term trends, local extrema, critical low-voltage events, and potential discharge-rate acceleration.

---

## Project Snapshot

| Metric                                  |                        Result |
| --------------------------------------- | ----------------------------: |
| Records analyzed                        |                    **21,919** |
| Observation period                      | **26 Jun 2024 → 03 Jul 2024** |
| Mean voltage                            |                     **67.3%** |
| Minimum voltage                         |                       **25%** |
| Maximum voltage                         |                      **100%** |
| Standard deviation                      |                     **21.8%** |
| Local peaks detected                    |                        **22** |
| Local lows detected                     |                        **22** |
| Readings below 20%                      |                         **0** |
| 5-day moving average                    |   **Yes — time-based (`5D`)** |
| Significant slope-acceleration episodes |                         **0** |

---

## Objectives

The analysis was built to answer four practical questions:

1. What does the battery-voltage profile look like over time?
2. How consistently do charge and discharge cycles occur?
3. Is there an observable long-term change in the operating voltage range?
4. Are there periods where the discharge rate accelerates significantly?

---

## Tech Stack

### Data Analysis

* **Python**
* **Pandas** — CSV parsing, timestamp handling, rolling analysis
* **NumPy** — numerical operations and derivatives
* **SciPy** — signal smoothing and peak detection
* **Matplotlib** — static visualization

### Interactive Dashboard

* **HTML5**
* **CSS3** — responsive dark-theme interface
* **Vanilla JavaScript**
* **Plotly.js 2.35.0** — interactive WebGL/time-series visualization
* **Google Fonts / Inter**

---

## Repository Structure

```text
.
├── analysis.py
├── voltage_data.csv
├── interpretation.txt
├── README.md
│
├── dashboard/
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── data.json
│
└── output/
    ├── chart1_voltage_trendline.png
    ├── chart2_moving_average.png
    ├── chart3_peaks_lows.png
    └── chart4_slope_acceleration.png
```

### Main Files

**`analysis.py`**
Complete Python analysis pipeline covering data loading, timestamp parsing, moving-average calculation, peak/low detection, critical-threshold analysis, derivative-based discharge analysis, static chart generation, and dashboard-data export.

**`voltage_data.csv`**
Raw battery-voltage dataset containing `Values` and `Timestamp`.

**`dashboard/data.json`**
Generated web-ready data containing all **21,919 observations**, moving-average values, peaks, lows, summary statistics, and slope-analysis results.

**`dashboard/index.html` / `app.js` / `style.css`**
Interactive dashboard implementation.

**`output/`**
Generated static PNG charts.

**`interpretation.txt`**
Five-line analytical interpretation supplied with the assignment.

---

## 🔬 Analysis Methodology

### 1. Data Loading & Cleaning

The pipeline reads the CSV using Pandas and standardizes the fields to:

```text
Voltage
Timestamp
```

Timestamps are parsed using:

```text
DD-MM-YYYY HH:MM
```

The records are sorted chronologically before analysis.

The dataset contains **21,919 observations**, with values ranging from **25% to 100%**.

---

### 2. Five-Day Time-Based Moving Average

A true time-based rolling window is used:

```python
rolling(window='5D', center=True, min_periods=1)
```

This reduces short-term charge/discharge fluctuations and exposes the underlying multi-day trend.

---

### 3. Local Peak & Low Detection

The voltage signal is first smoothed using:

```python
scipy.ndimage.uniform_filter1d
```

with a **15-sample smoothing window**.

Local extrema are then detected using:

```python
scipy.signal.find_peaks
```

Detection parameters include:

* Prominence: **5**
* Width: **3**
* Adaptive minimum separation based on approximately **1.5 hours** of observations

The inverted signal is used to detect local lows.

### Results

* **22 local peaks**
* **22 local lows**

The detected peak values repeatedly reach or approach full charge, while the detected lows extend down to **25%**.

<img width="1393" height="613" alt="image" src="https://github.com/user-attachments/assets/dd6881af-6466-4790-99fc-3cb2811cdbf1" />


---

### 4. Critical Low-Voltage Detection

The pipeline explicitly checks for:

```python
Voltage < 20
```

### Result

**0 observations were below 20%.**

The minimum recorded voltage is **25%**.

For additional context, the pipeline also checks observations below 30%.

---

### 5. Downward Slope Acceleration — Bonus Analysis

The bonus analysis evaluates whether a declining voltage signal is becoming progressively steeper.

The processing flow is:

```text
Voltage
   ↓
Smoothed Signal
   ↓
First Derivative (dV/dt)
   ↓
Second Derivative (d²V/dt²)
   ↓
Acceleration Threshold
   ↓
Episode Detection
```

Thresholds implemented in the analysis:

```python
dV_dt < -0.0005
d2V_dt2 < -5e-9
```

Episodes must contain at least **3 records** to survive the noise filter.

### Result

**No significant downward slope-acceleration episodes were detected.**

This is a valid analytical result: the project tested for accelerating discharge, but no events met the implemented criteria.

---

## 📈 Static Visualizations

### 1. Voltage Trend + Cubic Trendline

![Voltage Trend](./output/chart1_voltage_trendline.png)

The raw battery-voltage signal is plotted against timestamp together with a third-degree polynomial trendline.

---

### 2. Five-Day Moving Average

![Five-Day Moving Average](./output/chart2_moving_average.png)

The time-based five-day moving average smooths high-frequency fluctuations and highlights longer-term behavior.

---

### 3. Local Peaks & Lows

![Peaks and Lows](./output/chart3_peaks_lows.png)

The signal-processing pipeline identifies **22 peaks and 22 lows**, providing an algorithmic view of recurring operating cycles.

---

### 4. Downward Slope Acceleration

![Slope Acceleration](./output/chart4_slope_acceleration.png)

The bonus visualization contains:

* Battery voltage with detected acceleration points
* Voltage rate of change (`dV/dt`) in `%/hour`

For this dataset, **no qualifying acceleration episodes remain after thresholding and filtering**.

---

## 🖥️ Interactive Dashboard

The repository includes a browser-based dashboard for exploring the complete dataset.

### Features

* Full **21,919-point** dataset
* Plotly.js WebGL rendering
* Interactive voltage chart
* Cubic trendline
* Five-day moving average
* Peak/low visualization
* Peak and low data tables
* `<20%` critical-voltage check
* Slope-acceleration result section
* Embedded analytical interpretation
* Responsive dark-theme UI
* Hover crosshair/spike lines
* Scroll-wheel zoom
* Click-and-drag panning
* Double-click reset

### Synchronized Charts

The three main Plotly charts share the same X-axis range.

Zooming or panning one chart automatically synchronizes the time range across the other charts, making it easier to compare voltage behavior, moving averages, and detected extrema within the same time window.

---

## Run Locally

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd <repository-folder>
```

### 2. Install dependencies

```bash
pip install pandas numpy scipy matplotlib
```

### 3. Run the analysis

```bash
python analysis.py
```

This generates:

```text
output/*.png
dashboard/data.json
```

### 4. Start a local HTTP server

```bash
python -m http.server 8765
```

### 5. Open the dashboard

```text
http://localhost:8765/dashboard/index.html
```

The local server is recommended because the dashboard loads `data.json` using `fetch()`.

---

## Data Format

The raw CSV contains:

| Column      | Description                            |
| ----------- | -------------------------------------- |
| `Values`    | Battery voltage / operating percentage |
| `Timestamp` | Observation timestamp                  |

Example:

```csv
Values,Timestamp
100,26-06-2024 06:17
100,26-06-2024 06:18
100,26-06-2024 06:18
```

---

## Key Findings

### Repeated Operating Cycles

The dataset contains clear recurring rises and falls. The algorithm detects **22 major local peaks and 22 local lows**.

### Operating Range

The observed voltage range is **25%–100%**, with a mean of **67.3%** and standard deviation of **21.8%**.

### No Critical <20% Events

There are **zero readings below 20%**. The minimum recorded value is **25%**.

### Long-Term Trend

The five-day moving average suppresses short-term cycling and provides a clearer view of multi-day baseline behavior.

### No Significant Accelerating Discharge

The derivative-based analysis detects **0 qualifying slope-acceleration episodes** using the implemented thresholds.

---

## Interpretation & Limitations

This project analyzes **battery-voltage data only** over an approximately eight-day observation period.

Voltage alone cannot definitively establish:

* Battery State of Health
* Actual remaining capacity
* Battery degradation rate
* Exact instantaneous power demand
* The physical cause of a particular discharge event

Therefore:

* A moving-average decline should be treated as an observed short-term trend rather than proof of degradation.
* Voltage changes cannot independently confirm hill climbing, HVAC usage, passenger load, or another operational cause.
* Detected peaks/lows are algorithmic signal turning points, not direct measurements of complete physical battery cycles.
* The 20% threshold is an analysis criterion used by the project, not a universal battery-safety limit.
* Zero slope-acceleration events means no observations met the implemented criteria; it does not mean power demand never increased.

Additional telemetry such as **current, temperature, power, State of Charge, GPS, route, HVAC activity, and passenger load** would enable stronger battery-health and operational analysis.

---

## Possible Extensions

* State-of-Charge estimation
* State-of-Health estimation
* Battery degradation tracking
* Temperature correlation
* Current and power analysis
* Route-level energy consumption
* Regenerative-braking analysis
* Automated anomaly detection
* GPS/telemetry event correlation
* Real-time fleet monitoring

---

##  Author

**Shiv Pratap Singh**

B.Tech — Computer Science / Information Technology

**Data Analysis • Python • Time-Series Analysis • Signal Processing • Interactive Visualization**

---

##  Project Context

**Greencell Mobility (NueGo) — Data Visualization & Interpretation Internship Assignment**

This project demonstrates an end-to-end workflow from raw battery telemetry to statistical analysis, signal processing, static visualization, and interactive web-based exploration.
