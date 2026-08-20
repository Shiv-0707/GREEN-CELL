/**
 * NueGo Battery Voltage Dashboard — Plotly.js
 * TradingView-style interactions:
 *   • Drag X-axis labels to stretch/compress time
 *   • Drag Y-axis labels to stretch/compress values
 *   • Scroll wheel zooms (both axes)
 *   • Click + drag on chart to pan
 *   • Double-click to auto-fit / reset
 *   • Range slider at bottom for quick navigation
 *   • Crosshair spike lines on hover
 */

(async function () {
    'use strict';

    // ── Load Data ──
    let DATA;
    try {
        const resp = await fetch('data.json');
        DATA = await resp.json();
    } catch (err) {
        document.body.innerHTML = `<div style="padding:80px;text-align:center;color:#ef4444;font-family:Inter,sans-serif;">
            <h2>Failed to load data.json</h2>
            <p style="color:#94a3b8;">Make sure to run analysis.py first and serve this folder via a local server.</p>
            <pre style="color:#64748b;margin-top:16px;">${err.message}</pre>
        </div>`;
        return;
    }

    // ── Populate Stats ──
    const stats = DATA.stats;
    document.getElementById('val-records').textContent = stats.total_records.toLocaleString();
    document.getElementById('val-range').textContent = `${fmtShort(stats.date_start)} – ${fmtShort(stats.date_end)}`;
    document.getElementById('val-mean').textContent = stats.mean_voltage + '%';
    document.getElementById('val-min').textContent = stats.min_voltage + '%';
    document.getElementById('val-max').textContent = stats.max_voltage + '%';
    document.getElementById('val-std').textContent = '±' + stats.std_voltage + '%';
    document.getElementById('below20-min').textContent = DATA.min_voltage;

    // ── Parse data arrays ──
    const timestamps = DATA.voltage.map(d => d[0]);
    const voltages   = DATA.voltage.map(d => d[1]);
    const maTimestamps = DATA.moving_avg.map(d => d[0]);
    const maValues     = DATA.moving_avg.map(d => d[1]);

    // ── Common Plotly layout (dark theme matching CSS) ──
    const COLORS = {
        bg:       '#1e293b',
        paper:    '#0f172a',
        grid:     '#334155',
        text:     '#94a3b8',
        title:    '#f1f5f9',
        voltage:  '#38bdf8',
        trend:    '#f97316',
        ma:       '#22c55e',
        peak:     '#ef4444',
        low:      '#a855f7',
        spike:    '#64748b',
        slider:   '#1e293b',
    };

    function baseLayout(title, showRangeSlider) {
        return {
            paper_bgcolor: COLORS.paper,
            plot_bgcolor:  COLORS.bg,
            font: { family: 'Inter, sans-serif', color: COLORS.text, size: 12 },
            margin: { l: 60, r: 30, t: 10, b: showRangeSlider ? 90 : 50 },
            hovermode: 'x unified',
            dragmode: 'pan',   // default drag = pan (like TradingView)
            xaxis: {
                gridcolor: COLORS.grid,
                linecolor: COLORS.grid,
                zerolinecolor: COLORS.grid,
                tickfont: { size: 10 },
                title: { text: 'Timestamp', font: { size: 13, color: COLORS.text } },
                // Disable rangeslider to make axis-dragging easier (TradingView style)
                rangeslider: { visible: false },
                // Spike line (crosshair) on hover
                showspikes: true,
                spikemode: 'across',
                spikethickness: 1,
                spikecolor: COLORS.spike,
                spikedash: 'dot',
                // Enable axis zoom by dragging axis labels
                fixedrange: false,
            },
            yaxis: {
                gridcolor: COLORS.grid,
                linecolor: COLORS.grid,
                zerolinecolor: COLORS.grid,
                tickfont: { size: 10 },
                ticksuffix: '%',
                range: [0, 108],
                // Lock the Y-axis panning so user cannot pan into negative voltages
                fixedrange: false,
                constrain: 'domain',
                // Spike line (crosshair) on hover
                showspikes: true,
                spikemode: 'across',
                spikethickness: 1,
                spikecolor: COLORS.spike,
                spikedash: 'dot',
                // Enable axis zoom by dragging axis labels
                fixedrange: false,
            },
            legend: {
                bgcolor: 'rgba(30,41,59,0.8)',
                bordercolor: COLORS.grid,
                borderwidth: 1,
                font: { size: 11, color: COLORS.title },
                x: 0.01, y: 0.99,
                xanchor: 'left', yanchor: 'top',
            },
            modebar: {
                bgcolor: 'rgba(0,0,0,0)',
                color: COLORS.text,
                activecolor: COLORS.voltage,
                orientation: 'v',
            },
        };
    }

    const plotConfig = {
        responsive: true,
        scrollZoom: true,          // scroll wheel zooms
        displaylogo: false,
        modeBarButtonsToAdd: ['resetScale2d'],
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        doubleClick: 'reset+autosize',  // double-click resets
    };

    // ═══════════════════════════════════════
    // Chart 1: Voltage with Trendline
    // ═══════════════════════════════════════
    const trendY = polyTrend(voltages, 3);

    const trace1_voltage = {
        x: timestamps,
        y: voltages,
        type: 'scattergl',
        mode: 'lines',
        name: 'Voltage (%)',
        line: { color: COLORS.voltage, width: 1.2 },
        fill: 'tozeroy',
        fillcolor: 'rgba(56,189,248,0.06)',
        hovertemplate: '%{y}%<extra>Voltage</extra>',
    };

    const trace1_trend = {
        x: timestamps,
        y: trendY,
        type: 'scattergl',
        mode: 'lines',
        name: 'Trendline (cubic)',
        line: { color: COLORS.trend, width: 2.5, dash: 'dash' },
        hovertemplate: '%{y:.1f}%<extra>Trend</extra>',
    };

    Plotly.newPlot('chart-voltage', [trace1_voltage, trace1_trend],
        baseLayout('Voltage Over Time', false), plotConfig);

    // ═══════════════════════════════════════
    // Chart 2: Moving Average
    // ═══════════════════════════════════════
    const trace2_voltage = {
        x: timestamps,
        y: voltages,
        type: 'scattergl',
        mode: 'lines',
        name: 'Voltage (%)',
        line: { color: 'rgba(56,189,248,0.35)', width: 0.9 },
        hovertemplate: '%{y}%<extra>Voltage</extra>',
    };

    const trace2_ma = {
        x: maTimestamps,
        y: maValues,
        type: 'scattergl',
        mode: 'lines',
        name: '5-Day Moving Average',
        line: { color: COLORS.ma, width: 3 },
        hovertemplate: '%{y:.1f}%<extra>5-Day MA</extra>',
    };

    Plotly.newPlot('chart-ma', [trace2_voltage, trace2_ma],
        baseLayout('5-Day Moving Average', false), plotConfig);

    // ═══════════════════════════════════════
    // Chart 3: Peaks & Lows
    // ═══════════════════════════════════════
    const peakX = DATA.peaks.map(p => p[0]);
    const peakY = DATA.peaks.map(p => p[1]);
    const lowX  = DATA.lows.map(l => l[0]);
    const lowY  = DATA.lows.map(l => l[1]);

    const trace3_voltage = {
        x: timestamps,
        y: voltages,
        type: 'scattergl',
        mode: 'lines',
        name: 'Voltage (%)',
        line: { color: 'rgba(56,189,248,0.55)', width: 1 },
        hovertemplate: '%{y}%<extra>Voltage</extra>',
    };

    const trace3_peaks = {
        x: peakX,
        y: peakY,
        type: 'scatter',
        mode: 'markers',
        name: `Peaks (${peakX.length})`,
        marker: {
            symbol: 'triangle-up',
            size: 12,
            color: COLORS.peak,
            line: { color: '#ffffff', width: 1.5 },
        },
        hovertemplate: '<b>Peak</b><br>%{x}<br>%{y}%<extra></extra>',
    };

    const trace3_lows = {
        x: lowX,
        y: lowY,
        type: 'scatter',
        mode: 'markers',
        name: `Lows (${lowX.length})`,
        marker: {
            symbol: 'diamond',
            size: 11,
            color: COLORS.low,
            line: { color: '#ffffff', width: 1.5 },
        },
        hovertemplate: '<b>Low</b><br>%{x}<br>%{y}%<extra></extra>',
    };

    Plotly.newPlot('chart-peaks', [trace3_voltage, trace3_peaks, trace3_lows],
        baseLayout('Local Peaks & Lows', false), plotConfig);

    // ═══════════════════════════════════════
    // Synchronize X-Axis Zoom/Pan Across Charts
    // ═══════════════════════════════════════
    const charts = [
        document.getElementById('chart-voltage'),
        document.getElementById('chart-ma'),
        document.getElementById('chart-peaks')
    ];

    charts.forEach(chart => {
        chart.on('plotly_relayout', function(eventData) {
            // Check if this is an x-axis pan/zoom or a full reset
            const hasXRange = eventData['xaxis.range[0]'] !== undefined || eventData['xaxis.range'] !== undefined;
            const isReset = eventData['xaxis.autorange'] === true || Object.keys(eventData).length === 0;

            if (hasXRange || isReset) {
                // Get the newly applied range from the chart that triggered the event
                const newRange = chart.layout.xaxis.range;
                const update = isReset ? { 'xaxis.autorange': true } : { 'xaxis.range': [newRange[0], newRange[1]] };

                charts.filter(c => c !== chart).forEach(c => {
                    // Only update if the range is actually different, preventing infinite loops
                    const cRange = c.layout.xaxis.range;
                    const needsUpdate = isReset || !cRange || cRange[0] !== newRange[0] || cRange[1] !== newRange[1];
                    
                    if (needsUpdate) {
                        Plotly.relayout(c, update);
                    }
                });
            }
        });
    });

    // ═══════════════════════════════════════
    // Tables
    // ═══════════════════════════════════════
    populateTable('table-peaks', DATA.peaks);
    populateTable('table-lows', DATA.lows);

    // ═══════════════════════════════════════
    // Slope Acceleration
    // ═══════════════════════════════════════
    const slopeEl = document.getElementById('slope-content');
    if (DATA.slope_episodes && DATA.slope_episodes.length > 0) {
        slopeEl.innerHTML = DATA.slope_episodes.map(ep =>
            `<div class="slope-episode">
                <div class="ep-marker"></div>
                <div class="ep-text">
                    <strong>${ep.start}</strong> → <strong>${ep.end}</strong>
                    &nbsp;|&nbsp; Voltage: ${ep.start_v}% → ${ep.end_v}%
                    &nbsp;|&nbsp; ${ep.points} data points
                </div>
            </div>`
        ).join('');
    } else {
        slopeEl.innerHTML = `
            <div class="slope-none">
                <p>No significant downward slope acceleration episodes were detected.</p>
                <p class="note">The discharge patterns in this dataset are relatively smooth and linear within each cycle.
                The voltage decline rate stays consistent rather than accelerating — a positive indicator of healthy battery behavior.</p>
            </div>`;
    }

    // ═══════════════════════════════════════
    // Helpers
    // ═══════════════════════════════════════

    function fmtShort(str) {
        const d = new Date(str);
        return ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][d.getMonth()]
            + ' ' + d.getDate();
    }

    function populateTable(tableId, data) {
        const tbody = document.querySelector(`#${tableId} tbody`);
        tbody.innerHTML = data.map((row, i) => {
            const v = row[1];
            const cls = v >= 80 ? 'voltage-high' : v < 40 ? 'voltage-low' : 'voltage-mid';
            return `<tr><td>${i+1}</td><td>${row[0]}</td><td class="${cls}">${v}%</td></tr>`;
        }).join('');
    }

    /**
     * Compute polynomial trendline via least-squares.
     */
    function polyTrend(values, degree) {
        const n = values.length;
        const x = Array.from({length: n}, (_, i) => i / n);
        const cols = degree + 1;
        const XtX = Array.from({length: cols}, () => new Array(cols).fill(0));
        const XtY = new Array(cols).fill(0);

        for (let i = 0; i < n; i++) {
            let xp = 1;
            const pw = [];
            for (let j = 0; j <= degree; j++) { pw.push(xp); xp *= x[i]; }
            for (let j = 0; j < cols; j++) {
                XtY[j] += pw[j] * values[i];
                for (let k = 0; k < cols; k++) XtX[j][k] += pw[j] * pw[k];
            }
        }

        const c = gaussElim(XtX, XtY);
        return x.map(xi => {
            let y = 0, xp = 1;
            for (let j = 0; j <= degree; j++) { y += c[j] * xp; xp *= xi; }
            return y;
        });
    }

    function gaussElim(A, b) {
        const n = A.length;
        const M = A.map((r, i) => [...r, b[i]]);
        for (let c = 0; c < n; c++) {
            let mx = c;
            for (let r = c+1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[mx][c])) mx = r;
            [M[c], M[mx]] = [M[mx], M[c]];
            const piv = M[c][c];
            if (Math.abs(piv) < 1e-12) continue;
            for (let j = c; j <= n; j++) M[c][j] /= piv;
            for (let r = 0; r < n; r++) {
                if (r === c) continue;
                const f = M[r][c];
                for (let j = c; j <= n; j++) M[r][j] -= f * M[c][j];
            }
        }
        return M.map(r => r[n]);
    }

})();
