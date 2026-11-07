"""Welch reception measurements. Thresholds are experimental screening criteria."""
import numpy as np
from scipy.signal import welch


def measure(x, rate, hz):
    f, p = welch(x, rate, nperseg=8192)
    band = abs(f - hz) <= 75
    nearby = (abs(f - hz) >= 200) & (abs(f - hz) <= 1000)
    power = float(p[band].sum())
    floor = max(float(np.median(p[nearby])), 1e-30)
    peak = float(p[band].max())
    peak_hz = float(f[band][np.argmax(p[band])])
    harmonics = {}
    for multiple in range(2, 6):
        if multiple * hz + 75 >= rate / 2:
            break
        harmonic = float(p[abs(f - multiple * hz) <= 75].sum())
        harmonics[str(multiple)] = float(10 * np.log10(max(harmonic, 1e-30) / max(power, 1e-30)))
    windows = np.array_split(x, 6)
    powers = []
    for window in windows:
        wf, wp = welch(window, rate, nperseg=min(8192, len(window)))
        powers.append(float(wp[abs(wf - hz) <= 75].sum()))
    variation = float(np.ptp(10 * np.log10(np.maximum(powers, 1e-30))))
    return dict(power=power, peak_hz=peak_hz,
                peak_floor_db=float(10 * np.log10(max(peak, 1e-30) / floor)),
                variation_db=variation, harmonics_dbc=harmonics)


def reception_report(rx, metadata, issues):
    rate = metadata['rate']
    rows = []
    for hz in (2000, 8000, 16000):
        measurements = {}
        for event in metadata['events']:
            if event.get('reception_hz') != hz or event['stop'] > len(rx):
                continue
            # Discard two seconds after each switch for buffering and settling.
            x = rx[event['start'] + 2 * rate:event['stop'] - round(.5 * rate)]
            measurements[event['repeat'], event['state']] = measure(x, rate, hz)
        trials = []
        for repeat in range(3):
            if (repeat, 'on') in measurements and (repeat, 'off') in measurements:
                on, off = measurements[repeat, 'on'], measurements[repeat, 'off']
                contrast = float(10 * np.log10(max(on['power'], 1e-30) / max(off['power'], 1e-30)))
                trials.append(dict(on=on, off=off, on_off_db=contrast))
        row = dict(hz=hz, trials=trials, result='incomplete')
        if len(trials) == 3:
            contrast = min(t['on_off_db'] for t in trials)
            peak = min(t['on']['peak_floor_db'] for t in trials)
            variation = max(t['on']['variation_db'] for t in trials)
            harmonic_warning = any(v > -20 for t in trials for v in t['on']['harmonics_dbc'].values())
            usable = contrast >= 10 and peak >= 10 and variation <= 3 and not issues and not harmonic_warning
            row.update(on_off_db=contrast, peak_floor_db=peak, variation_db=variation,
                       harmonic_warning=harmonic_warning,
                       result='usable for next experiment' if usable else 'inconclusive / check details')
        rows.append(row)
    return rows
