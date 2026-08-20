"""
Greencell NueGo Internship Assignment
Data Visualization & Interpretation - Battery Voltage Analysis
================================================================
This script analyzes battery voltage data from an electric bus fleet.
It performs:
  1. Voltage vs Time chart with trendline
  2. 5-day moving average overlay
  3. Local peaks and lows detection
  4. Below-20 voltage instances (tabulated)
  5. Downward slope acceleration detection (bonus)
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for saving files
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.signal import find_peaks
from scipy.ndimage import uniform_filter1d
import os
import warnings
warnings.filterwarnings('ignore')

# ──────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────
CSV_PATH = "voltage_data.csv"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Plot styling
plt.rcParams.update({
    'figure.facecolor': '#0f172a',
    'axes.facecolor': '#1e293b',
    'axes.edgecolor': '#334155',
    'axes.labelcolor': '#e2e8f0',
    'xtick.color': '#94a3b8',
    'ytick.color': '#94a3b8',
    'text.color': '#e2e8f0',
    'grid.color': '#334155',
    'grid.alpha': 0.5,
    'font.family': 'sans-serif',
    'font.size': 11,
})

# ──────────────────────────────────────────────────────────────
# 1. Load & Parse Data
# ──────────────────────────────────────────────────────────────
print("=" * 70)
print("  GREENCELL NueGo — Battery Voltage Analysis")
print("=" * 70)

df = pd.read_csv(CSV_PATH)
df.columns = ['Voltage', 'Timestamp']
df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d-%m-%Y %H:%M')
df = df.sort_values('Timestamp').reset_index(drop=True)

print(f"\n📊 Dataset loaded: {len(df):,} records")
print(f"📅 Date range: {df['Timestamp'].iloc[0]} → {df['Timestamp'].iloc[-1]}")
print(f"⚡ Voltage range: {df['Voltage'].min()}% – {df['Voltage'].max()}%")
print(f"📈 Mean voltage: {df['Voltage'].mean():.1f}%")

# ──────────────────────────────────────────────────────────────
# 2. Compute Moving Average (5-day) — time-based window
# ──────────────────────────────────────────────────────────────
# Use a proper time-based rolling window for accuracy
df_indexed = df.set_index('Timestamp')
df['MA_5day'] = df_indexed['Voltage'].rolling(
    window='5D', center=True, min_periods=1
).mean().values

print(f"\n📉 5-day moving average: time-based window (5D)")

# ──────────────────────────────────────────────────────────────
# 3. Detect Local Peaks and Lows
# ──────────────────────────────────────────────────────────────
# Smooth voltage slightly to avoid noise peaks while preserving true turning points
from scipy.ndimage import uniform_filter1d as uf1d
voltage_smooth_peaks = uf1d(df['Voltage'].values.astype(float), size=15)

# Adaptive distance: roughly 1 hour of data minimum between peaks
points_per_hour = len(df) / ((df['Timestamp'].iloc[-1] - df['Timestamp'].iloc[0]).total_seconds() / 3600)
min_distance = max(10, int(points_per_hour * 1.5))  # at least 1.5 hours apart

# Find peaks (local maxima)
peak_indices, peak_props = find_peaks(
    voltage_smooth_peaks,
    distance=min_distance,
    prominence=5,   # at least 5% prominent
    width=3,        # must span at least a few data points
)

# Find lows (local minima) by inverting the signal
low_indices, low_props = find_peaks(
    -voltage_smooth_peaks,
    distance=min_distance,
    prominence=5,
    width=3,
)

peaks_df = df.iloc[peak_indices][['Timestamp', 'Voltage']].copy()
peaks_df = peaks_df.rename(columns={'Voltage': 'Peak_Voltage'})

lows_df = df.iloc[low_indices][['Timestamp', 'Voltage']].copy()
lows_df = lows_df.rename(columns={'Voltage': 'Low_Voltage'})

print(f"\n🔺 Local peaks found: {len(peaks_df)}")
print("-" * 50)
print(peaks_df.to_string(index=False))

print(f"\n🔻 Local lows found: {len(lows_df)}")
print("-" * 50)
print(lows_df.to_string(index=False))

# ──────────────────────────────────────────────────────────────
# 4. Find Voltage Below 20
# ──────────────────────────────────────────────────────────────
below_20 = df[df['Voltage'] < 20].copy()

print(f"\n⚠️  Instances where voltage went below 20%: {len(below_20)}")
if len(below_20) > 0:
    print("-" * 50)
    print(below_20[['Timestamp', 'Voltage']].to_string(index=False))
else:
    # Check the actual minimum to explain
    print(f"   (Minimum voltage in dataset: {df['Voltage'].min()}%)")
    print("   No instances found. The voltage never dropped below 20%.")

    # Let's also check below 30 for context
    below_30 = df[df['Voltage'] < 30].copy()
    if len(below_30) > 0:
        # Group consecutive below-30 readings into episodes
        below_30['gap'] = (below_30.index - below_30.index.to_series().shift(1) > 1).cumsum()
        episodes = below_30.groupby('gap').agg(
            Start=('Timestamp', 'first'),
            End=('Timestamp', 'last'),
            Min_Voltage=('Voltage', 'min'),
            Count=('Voltage', 'count')
        )
        print(f"\n   ℹ️  For reference, instances below 30% ({len(below_30)} records, {len(episodes)} episodes):")
        print("-" * 70)
        print(episodes.to_string())

# ──────────────────────────────────────────────────────────────
# 5. Bonus: Downward Slope Acceleration Detection
# ──────────────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
print("  BONUS: Downward Slope Acceleration Detection")
print("=" * 70)

# Compute first derivative (slope) using time-based differences
df['time_seconds'] = (df['Timestamp'] - df['Timestamp'].iloc[0]).dt.total_seconds()

# Smooth the voltage slightly to reduce noise before differentiation
smooth_window = max(5, len(df) // 2000)
df['Voltage_smooth'] = uniform_filter1d(df['Voltage'].values, size=smooth_window)

# First derivative: dV/dt (rate of voltage change)
df['dV_dt'] = np.gradient(df['Voltage_smooth'], df['time_seconds'])

# Second derivative: d²V/dt² (acceleration of voltage change)
df['d2V_dt2'] = np.gradient(df['dV_dt'], df['time_seconds'])

# A downward slope accelerates when:
#   1. The voltage is decreasing (dV/dt < 0)
#   2. The decrease is getting faster (d²V/dt² < 0, i.e. slope becomes more negative)
# We need meaningful thresholds to avoid noise
dv_threshold = -0.0005  # Voltage is clearly decreasing
d2v_threshold = -5e-9   # Acceleration threshold

acceleration_mask = (df['dV_dt'] < dv_threshold) & (df['d2V_dt2'] < d2v_threshold)
accel_df = df[acceleration_mask].copy()

if len(accel_df) > 0:
    # Group into contiguous episodes
    accel_df = accel_df.copy()
    accel_df['gap'] = (accel_df.index - accel_df.index.to_series().shift(1) > 1).cumsum()
    episodes = accel_df.groupby('gap').agg(
        Start_Time=('Timestamp', 'first'),
        End_Time=('Timestamp', 'last'),
        Start_Voltage=('Voltage', 'first'),
        End_Voltage=('Voltage', 'last'),
        Max_Slope=('dV_dt', 'min'),  # Most negative slope
        Records=('Voltage', 'count')
    )
    # Filter out very short episodes (noise)
    episodes = episodes[episodes['Records'] >= 3]

    print(f"\n🔽 Found {len(episodes)} episodes of accelerating downward slope:")
    print("-" * 90)
    for idx, row in episodes.iterrows():
        print(f"  📍 {row['Start_Time']} → {row['End_Time']}  |  "
              f"Voltage: {row['Start_Voltage']:.0f}% → {row['End_Voltage']:.0f}%  |  "
              f"Points: {row['Records']}")
else:
    print("\n   No significant downward slope acceleration episodes found.")

# ──────────────────────────────────────────────────────────────
# 6. Generate Charts
# ──────────────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
print("  Generating Charts...")
print("=" * 70)

# ── Chart 1: Main Voltage Chart with Trendline ──
fig, ax = plt.subplots(figsize=(16, 7))

# Plot voltage
ax.plot(df['Timestamp'], df['Voltage'], color='#38bdf8', linewidth=0.6,
        alpha=0.8, label='Voltage (%)')

# Trendline (polynomial fit)
x_numeric = np.arange(len(df))
z = np.polyfit(x_numeric, df['Voltage'].values, 3)
p = np.poly1d(z)
ax.plot(df['Timestamp'], p(x_numeric), color='#f97316', linewidth=2,
        linestyle='--', alpha=0.9, label='Trendline (cubic)')

ax.set_xlabel('Timestamp', fontsize=13, fontweight='bold')
ax.set_ylabel('Voltage (%)', fontsize=13, fontweight='bold')
ax.set_title('Battery Voltage Over Time — NueGo Electric Bus Fleet',
             fontsize=16, fontweight='bold', pad=15)
ax.legend(loc='upper right', fontsize=11, framealpha=0.8,
          facecolor='#1e293b', edgecolor='#475569')
ax.grid(True, linestyle='--', alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax.xaxis.set_major_locator(mdates.DayLocator())
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'chart1_voltage_trendline.png'), dpi=150)
print("  ✅ chart1_voltage_trendline.png saved")
plt.close()

# ── Chart 2: Voltage with 5-Day Moving Average ──
fig, ax = plt.subplots(figsize=(16, 7))

ax.plot(df['Timestamp'], df['Voltage'], color='#38bdf8', linewidth=0.5,
        alpha=0.5, label='Voltage (%)')
ax.plot(df['Timestamp'], df['MA_5day'], color='#22c55e', linewidth=2.5,
        alpha=0.95, label='5-Day Moving Average')

ax.set_xlabel('Timestamp', fontsize=13, fontweight='bold')
ax.set_ylabel('Voltage (%)', fontsize=13, fontweight='bold')
ax.set_title('Battery Voltage with 5-Day Moving Average',
             fontsize=16, fontweight='bold', pad=15)
ax.legend(loc='upper right', fontsize=11, framealpha=0.8,
          facecolor='#1e293b', edgecolor='#475569')
ax.grid(True, linestyle='--', alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax.xaxis.set_major_locator(mdates.DayLocator())
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'chart2_moving_average.png'), dpi=150)
print("  ✅ chart2_moving_average.png saved")
plt.close()

# ── Chart 3: Peaks and Lows ──
fig, ax = plt.subplots(figsize=(16, 7))

ax.plot(df['Timestamp'], df['Voltage'], color='#38bdf8', linewidth=0.6,
        alpha=0.7, label='Voltage (%)')

# Mark peaks
if len(peak_indices) > 0:
    ax.scatter(df['Timestamp'].iloc[peak_indices], df['Voltage'].iloc[peak_indices],
               color='#ef4444', s=80, zorder=5, marker='^',
               edgecolors='white', linewidths=0.8, label=f'Peaks ({len(peak_indices)})')

# Mark lows
if len(low_indices) > 0:
    ax.scatter(df['Timestamp'].iloc[low_indices], df['Voltage'].iloc[low_indices],
               color='#a855f7', s=80, zorder=5, marker='v',
               edgecolors='white', linewidths=0.8, label=f'Lows ({len(low_indices)})')

ax.set_xlabel('Timestamp', fontsize=13, fontweight='bold')
ax.set_ylabel('Voltage (%)', fontsize=13, fontweight='bold')
ax.set_title('Battery Voltage — Local Peaks & Lows Detection',
             fontsize=16, fontweight='bold', pad=15)
ax.legend(loc='upper right', fontsize=11, framealpha=0.8,
          facecolor='#1e293b', edgecolor='#475569')
ax.grid(True, linestyle='--', alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax.xaxis.set_major_locator(mdates.DayLocator())
plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'chart3_peaks_lows.png'), dpi=150)
print("  ✅ chart3_peaks_lows.png saved")
plt.close()

# ── Chart 4: Downward Slope Acceleration ──
fig, axes = plt.subplots(2, 1, figsize=(16, 10), sharex=True,
                          gridspec_kw={'height_ratios': [2, 1]})

# Top: Voltage with acceleration zones highlighted
ax1 = axes[0]
ax1.plot(df['Timestamp'], df['Voltage'], color='#38bdf8', linewidth=0.6,
         alpha=0.7, label='Voltage (%)')

if len(accel_df) > 0:
    ax1.scatter(accel_df['Timestamp'], accel_df['Voltage'],
                color='#ef4444', s=3, alpha=0.6, label='Accelerating Discharge', zorder=4)

ax1.set_ylabel('Voltage (%)', fontsize=13, fontweight='bold')
ax1.set_title('Battery Voltage — Downward Slope Acceleration Analysis (Bonus)',
              fontsize=16, fontweight='bold', pad=15)
ax1.legend(loc='upper right', fontsize=11, framealpha=0.8,
           facecolor='#1e293b', edgecolor='#475569')
ax1.grid(True, linestyle='--', alpha=0.3)

# Bottom: Rate of change
ax2 = axes[1]
ax2.plot(df['Timestamp'], df['dV_dt'] * 3600, color='#fbbf24', linewidth=0.5,
         alpha=0.7, label='dV/dt (%/hour)')
ax2.axhline(y=0, color='#64748b', linewidth=1, linestyle='-')
ax2.set_ylabel('Rate of Change\n(%/hour)', fontsize=11, fontweight='bold')
ax2.set_xlabel('Timestamp', fontsize=13, fontweight='bold')
ax2.legend(loc='lower right', fontsize=10, framealpha=0.8,
           facecolor='#1e293b', edgecolor='#475569')
ax2.grid(True, linestyle='--', alpha=0.3)
ax2.xaxis.set_major_formatter(mdates.DateFormatter('%b %d\n%H:%M'))
ax2.xaxis.set_major_locator(mdates.DayLocator())

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, 'chart4_slope_acceleration.png'), dpi=150)
print("  ✅ chart4_slope_acceleration.png saved")
plt.close()

# ──────────────────────────────────────────────────────────────
# 7. Data Interpretation (5 Sentences)
# ──────────────────────────────────────────────────────────────
print(f"\n{'=' * 70}")
print("  DATA INTERPRETATION (5 Sentences)")
print("=" * 70)

interpretation = """
1. The battery voltage data exhibits clear cyclical charge-discharge patterns 
   typical of electric bus operations, with the voltage repeatedly rising to 
   100% (full charge) and declining to approximately 25-30% before recharging, 
   indicating consistent daily operational cycles.

2. The discharge curves show a non-linear pattern where voltage drops more 
   steeply in the mid-range (60-40%) compared to the upper range (100-80%), 
   which is characteristic of lithium-ion battery discharge behavior and 
   suggests the batteries are performing within expected electrochemical norms.

3. A slight overall downward trend is observable across the 8-day period, with 
   the 5-day moving average showing a gradual decline, which could indicate 
   minor degradation effects, ambient temperature variations, or changing 
   route demands on the fleet.

4. The local peaks consistently reach 100% and the lows cluster around 25-30%, 
   suggesting disciplined charging practices — the buses are being fully 
   charged and the fleet management system appears to trigger recharging 
   before the battery drops to dangerously low levels.

5. Several episodes of accelerating discharge (where the rate of voltage drop 
   increases) are detectable during the mid-range voltage zones, likely 
   corresponding to periods of heavy demand such as hill climbing, air 
   conditioning usage, or high passenger loads during peak hours.
"""

print(interpretation)

# ──────────────────────────────────────────────────────────────
# 8. Export data for web dashboard (ALL data points for precision)
# ──────────────────────────────────────────────────────────────
print("Exporting data for web dashboard...")

import json

# Export ALL data points — no sampling, for precision
all_data = df[['Timestamp', 'Voltage', 'MA_5day']].copy()
all_data['Timestamp'] = all_data['Timestamp'].dt.strftime('%Y-%m-%d %H:%M')

# Use the actual peak/low values from the original data (not smoothed)
dashboard_data = {
    "voltage": all_data[['Timestamp', 'Voltage']].values.tolist(),
    "moving_avg": all_data[['Timestamp', 'MA_5day']].dropna().values.tolist(),
    "peaks": [
        [df['Timestamp'].iloc[i].strftime('%Y-%m-%d %H:%M'), int(df['Voltage'].iloc[i])]
        for i in peak_indices
    ],
    "lows": [
        [df['Timestamp'].iloc[i].strftime('%Y-%m-%d %H:%M'), int(df['Voltage'].iloc[i])]
        for i in low_indices
    ],
    "below_20_count": len(below_20),
    "min_voltage": int(df['Voltage'].min()),
    "stats": {
        "total_records": len(df),
        "date_start": df['Timestamp'].iloc[0].strftime('%Y-%m-%d %H:%M'),
        "date_end": df['Timestamp'].iloc[-1].strftime('%Y-%m-%d %H:%M'),
        "mean_voltage": round(df['Voltage'].mean(), 1),
        "min_voltage": int(df['Voltage'].min()),
        "max_voltage": int(df['Voltage'].max()),
        "std_voltage": round(df['Voltage'].std(), 1),
    }
}

# Add slope acceleration episodes
if len(accel_df) > 0:
    accel_df_clean = accel_df.copy()
    accel_df_clean['gap'] = (accel_df_clean.index - accel_df_clean.index.to_series().shift(1) > 1).cumsum()
    ep = accel_df_clean.groupby('gap').agg(
        Start_Time=('Timestamp', 'first'),
        End_Time=('Timestamp', 'last'),
        Start_Voltage=('Voltage', 'first'),
        End_Voltage=('Voltage', 'last'),
        Records=('Voltage', 'count')
    )
    ep = ep[ep['Records'] >= 3]
    dashboard_data["slope_episodes"] = [
        {
            "start": row['Start_Time'].strftime('%Y-%m-%d %H:%M'),
            "end": row['End_Time'].strftime('%Y-%m-%d %H:%M'),
            "start_v": int(row['Start_Voltage']),
            "end_v": int(row['End_Voltage']),
            "points": int(row['Records'])
        }
        for _, row in ep.iterrows()
    ]

with open(os.path.join('dashboard', 'data.json'), 'w') as f:
    json.dump(dashboard_data, f)

print(f"  ✅ dashboard/data.json exported ({len(all_data):,} data points)")

print(f"\n{'=' * 70}")
print("  ✅ ANALYSIS COMPLETE — All charts saved to ./output/")
print("=" * 70)
