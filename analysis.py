import numpy as np
from scipy import signal
from protocol import SCAN_SETTINGS


def frames(x, rate, freq, size=2048):
    """One-sided PSD, integrated band power and quadrature envelope per window."""
    windows = np.lib.stride_tricks.sliding_window_view(x, size)[::size//2]
    w = signal.windows.hann(size, sym=False)
    f = np.fft.rfftfreq(size, 1/rate)
    psd = abs(np.fft.rfft(windows*w))**2 / (rate * np.sum(w*w))
    psd[:, 1:-1] *= 2
    band = abs(f-freq) <= max(75, 2*rate/size)
    power = psd[:, band].sum(axis=1)*rate/size
    oscillator = w * np.exp(-2j*np.pi*freq*np.arange(size)/rate)
    envelope = 2 * abs((windows @ oscillator)) / w.sum()
    return f, psd, power, envelope


def db(power):
    return 10*np.log10(np.maximum(power, 1e-20))


def tone_iq(x, rate, freq, size=2048):
    w = signal.windows.hann(size, sym=False)
    osc = w * np.exp(-2j*np.pi*freq*np.arange(size)/rate)
    return (np.lib.stride_tricks.sliding_window_view(x,size)[::size//2] @ osc) / w.sum()


def phase_reference(rx,tx,events,rate,freq):
    slopes, floors = [], []
    for e in events:
        if "state" not in e:
            continue
        a,b = e["start"]+round(.7*rate), e["stop"]-round(.15*rate)
        iq = tone_iq(rx[a:b],rate,freq)
        if e["state"]=="off":
            floors.append(float(np.max(abs(iq))))
            continue
        ref = tx[a:b]
        channel = np.argmax(np.max(abs(ref),axis=0))
        angle = np.unwrap(np.angle(iq*tone_iq(ref[:,channel],rate,freq).conj()))
        t = np.arange(len(angle))*1024/rate
        slope,offset = np.polyfit(t,angle,1)
        if np.max(abs(angle-offset-slope*t))>.10 or abs(slope)>.25:
            return None
        slopes.append(float(slope))
    if len(slopes)!=3 or np.ptp(slopes)>.15:
        return None
    return dict(drift_rad_s=float(np.median(slopes)), min_iq=max(1e-8,3*max(floors)))


def alignment(rx, tx, events, rate):
    points = []
    for e in events:
        if not e.get("marker"):
            continue
        a, b = e["start"], e["stop"]
        if b > len(tx):
            continue
        ref = tx[a:b, np.argmax(np.max(abs(tx[a:b]), axis=0))].astype(float)
        lo, hi = max(0, a-round(.45*rate)), min(len(rx), b+rate)
        if hi-lo < len(ref):
            continue
        # Normalize against energy in the emitted timing sweep's band. Apply
        # the same zero-phase filter to both sides to preserve relative delay.
        sos = signal.butter(4, [700,2700], fs=rate, btype="bandpass", output="sos")
        ref = signal.sosfiltfilt(sos, ref)
        x = signal.sosfiltfilt(sos, rx[lo:hi].astype(float))
        corr = abs(signal.correlate(x, ref, mode="valid", method="fft"))
        energy = np.r_[0., np.cumsum(x*x)]
        denom = np.sqrt(np.maximum(0, energy[len(ref):]-energy[:-len(ref)]) * np.dot(ref,ref))
        score = np.divide(corr,denom,out=np.zeros_like(corr),where=denom>1e-12)
        i = int(np.argmax(score))
        peak = float(score[i])
        score[max(0,i-rate//100):i+rate//100+1] = 0
        points.append(dict(at=a, lag=lo+i-a, correlation=peak,
                           valid=peak >= .30 and peak > 1.35*score.max().item()))
    return points


def score_scan(rx, rate, events, markers, out):
    out["scan_ranking"] = []
    out["selected_setting"] = None
    if out["issues"]:
        return
    marker_at = [p["at"] for p in markers]
    marker_lag = [p["lag"] for p in markers]
    # Matched short bursts are scored away from their fades and switching edges.
    measurements = {setting:{} for setting in SCAN_SETTINGS}
    for e in events:
        if e.get("stage")!="scan":
            continue
        hz,amp = e["scan_hz"],e["scan_peak"]
        lag = round(np.interp(e["start"],marker_at,marker_lag))
        a,b = e["start"]+lag+round(.08*rate), e["stop"]+lag-round(.08*rate)
        if a<0 or b>len(rx) or b-a<2048:
            out["issues"].append("Incomplete scan window")
            return
        power_db = float(db(np.median(frames(rx[a:b],rate,hz)[2])))
        group = measurements[hz,amp].setdefault((e["pair"],e["condition"]),[])
        group.append((e["pose"],e["slot"],power_db))

    ranking = []
    for (hz,amp),pairs in measurements.items():
        contrasts = {"on":[],"still":[],"off":[]}
        closed = {"on":[],"off":[]}
        for (_,condition),rows in sorted(pairs.items()):
            if len(rows)!=2:
                continue
            first,second = sorted(rows)  # closed then open, or by slot for still pairs
            contrasts[condition].append(second[2]-first[2])
            if condition in closed:
                closed[condition].append(first[2])
        if [len(contrasts[k]) for k in ("on","still","off")]!=[6,3,4]:
            out["issues"].append("Missing Quick Scan pairs")
            return
        effect = float(np.median(contrasts["on"]))
        still = max(abs(x) for x in contrasts["still"])
        off = float(np.median(contrasts["off"]))
        snr = float(np.median(closed["on"])-np.median(closed["off"]))
        agree = int(np.sum(np.sign(contrasts["on"])==np.sign(effect)))
        margin = abs(effect)-max(still,abs(off))
        ranking.append(dict(hz=hz,peak=amp,on_db=effect,off_db=off,still_max_db=still,
                            consistent_pairs=agree,probe_contrast_db=snr,margin_db=margin,
                            promising=agree>=5 and margin>0 and snr>=10,paired_db=contrasts))
    ranking.sort(key=lambda row:(not row["promising"],-row["margin_db"],row["peak"],row["hz"]))
    out["scan_ranking"] = ranking
    if ranking[0]["promising"]:
        out["selected_setting"] = {k:ranking[0][k] for k in ("hz","peak")}


def report(rx, tx, m):
    if m['mode'] == 'Continuous movement':
        from reception import measure
        rows = []
        for event in m['events']:
            if event.get('stage') not in ('baseline', 'movement') or event['stop'] > len(rx):
                continue
            x = rx[event['start'] + m['rate']:event['stop']]
            rows.append(dict(trial=event['trial'], condition=event['condition'],
                             stage=event['stage'], **measure(x, m['rate'], m.get('frequency', 2000))))
        issues = list(m['audio_flags'])
        if m['status'] != 'complete':
            issues.append('Capture ended early')
        if np.any(abs(rx) >= .999):
            issues.append('Input reached digital full scale')
        return dict(issues=issues, movement_measurements=rows,
                    interpretation='Exploratory trial measurements. Review mouth, head and off controls before inferring mouth specificity. Timing uses a 1 s guard and requires checking device latency.')
    if m['mode'] == 'Reception check':
        from reception import reception_report
        issues = []
        if m['status'] != 'complete':
            issues.append('Capture ended early')
        if m['audio_flags']:
            issues.append('Audio stream faults occurred')
        if np.any(abs(rx) >= .999):
            issues.append('Input reached digital full scale')
        return dict(issues=issues, reception=reception_report(rx, m, issues),
                    method='Welch PSD, 75 Hz half-band, 2 s settling guard',
                    limitations='Screening thresholds are experimental. Delays beyond 2 s can contaminate windows. Harmonics above Nyquist are unmeasurable. Physical acoustic routing requires verification.')
    rate, freq, events = m["rate"], m["frequency"], m["events"]
    markers = alignment(rx, tx, events, rate)
    issues = []
    if m["status"] != "complete":
        issues.append("Capture ended early: " + m["status"])
    if m["audio_flags"]:
        issues.append("Audio stream fault: " + ", ".join(m["audio_flags"]))
    if np.any(abs(rx) >= .999):
        issues.append("Input reached digital full scale")
    out = dict(issues=issues, timing_markers=markers)
    if markers:
        out["timing_method"] = "chirp-band normalized correlation v2 (700-2700 Hz)"
    extra_hold = events[0].get("extra_hold_s",0) if events else 0
    expected = 7 if extra_hold and m["mode"] in ("Head-turn control","Guided pairs") else 2
    if m["mode"]=="Quick Scan":
        expected = 4
    aligned = len(markers)==expected and all(p["valid"] for p in markers)
    if aligned:
        a,b = markers[0],markers[-1]
        out["lag_change_samples"] = b["lag"]-a["lag"]
        out["apparent_drift_ppm"] = 1e6*(b["lag"]-a["lag"])/(b["at"]-a["at"])
    if m["mode"] == "Band check":
        powers = {}
        for e in events:
            if "repeat" in e and e["stop"] <= len(rx):
                x = rx[e["start"]+round(.7*rate):e["stop"]-round(.15*rate)]
                powers[e["repeat"], e["state"]] = np.median(frames(x,rate,freq)[2])
        contrast = [float(db(powers[i,"on"])-db(powers[i,"off"])) for i in range(3)
                    if (i,"on") in powers and (i,"off") in powers]
        out.update(on_minus_off_db=contrast, band_gate=len(contrast)==3 and min(contrast)>=10 and not issues)
        if out["band_gate"] and m["stream_mode"]=="duplex" and m["setup"].startswith("A"):
            out["phase_reference"] = phase_reference(rx,tx,events,rate,freq)
    if m["mode"] not in ("Guided pairs", "Head-turn control", "Timing check","Quick Scan"):
        return out
    if not aligned:
        issues.append("Missing or ambiguous timing chirp")
    elif any(not (-.45 <= p["lag"]/rate <= .45+extra_hold) for p in markers):
        issues.append("Timing offset exceeds pose guard interval")
    elif extra_hold and np.ptp([p["lag"] for p in markers])/rate > .05:
        issues.append("Measured delay varied by more than 50 ms between timing checkpoints")
    if m["mode"]=="Timing check":
        out["timing_gate"] = not issues
        return out
    if m.get("missed_cues"):
        issues.append("Late or skipped pose prompts")
    if m["mode"]=="Quick Scan":
        score_scan(rx,rate,events,markers,out)
        return out
    rows = []
    for e in events:
        if e.get("stage") != "hold":
            continue
        lag = round(np.interp(e["start"], [p["at"] for p in markers], [p["lag"] for p in markers])) if aligned else 0
        lo, hi = e["start"]+lag+round(.55*rate), e["stop"]+lag-round(.55*rate)
        if lo < 0 or hi > len(rx):
            continue
        power = float(np.median(frames(rx[lo:hi],rate,freq)[2]))
        rows.append(dict(pair=e["pair"], condition=e["condition"], slot=e["slot"],
                         pose=e["pose"], rx_start=lo, rx_stop=hi, power=power, db=float(db(power))))
    out["holds"] = rows
    differences = {k:[] for k in ("on","off","closed_repeat")}
    for pair in sorted({r["pair"] for r in rows}):
        group = sorted([r for r in rows if r["pair"]==pair], key=lambda r:(r["pose"],r["slot"]))
        if len(group)==2:
            differences[group[0]["condition"]].append(group[1]["db"]-group[0]["db"])
    out["paired_differences_db"] = differences
    if not all(len(v)==10 for v in differences.values()):
        issues.append("Missing trial pairs")
    if not issues:
        on, off, null = (np.asarray(differences[k]) for k in ("on","off","closed_repeat"))
        med = float(np.median(on))
        threshold = float(np.percentile(abs(null),95))
        consistent = int(np.sum(np.sign(on)==np.sign(med)))
        out.update(on_median_db=med, off_median_db=float(np.median(off)),
                   still_repeat_p95_db=threshold, consistent_pairs=consistent,
                   position_gate=consistent>=8 and abs(med)>threshold)
        if m["mode"]=="Guided pairs":
            out["mouth_checks"] = {
                "At least 8 of 10 pairs agree": consistent>=8,
                "Above closed/closed variation": abs(med)>threshold,
                "Smaller contrast with probe off": abs(out["off_median_db"])<abs(med),
            }
            out["mouth_gate"] = all(out["mouth_checks"].values())
    return out
