"""Output schedule in samples. All levels are digital peak amplitudes."""
import random
import numpy as np
from scipy.signal import chirp

SCAN_SETTINGS = tuple((hz, peak) for hz in (1000, 2000, 4000) for peak in (.005, .010))


def build(rate, channels, mode, frequency, end, level, duration, side, seed, laptop=False,
          timing_warmup=False, extended_guard=False):
    if not 0 < frequency < rate * .48 or not 0 < end < rate * .48:
        raise ValueError("Frequencies must be below 48% of the selected sample rate.")
    if not 0 < level <= .05 or not .1 <= duration <= 10:
        raise ValueError("Use peak levels up to 0.05 and durations from 0.1 to 10 s.")
    if channels == 1 and side != "Both":
        raise ValueError("Mono output requires Both (the single available channel).")
    events, pieces = [], []
    cursor = 0

    def add(seconds, cue, kind="quiet", f0=frequency, f1=end, peak=level, **tags):
        nonlocal cursor
        count = round(seconds * rate)
        wave = np.zeros(count, dtype="float32")
        if kind != "quiet":
            t = np.arange(count) / rate
            signal = chirp(t, f0, seconds, f1) if kind == "chirp" else np.sin(2*np.pi*f0*t)
            wave[:] = peak * signal
            ramp = np.linspace(0, 1, min(round(rate * .015), count // 2)) ** 2
            wave[:len(ramp)] *= ramp
            wave[-len(ramp):] *= ramp[::-1]
        events.append(dict(start=cursor, stop=cursor+count, cue=cue, kind=kind, **tags))
        pieces.append(wave)
        cursor += count

    def marker():
        # Same modest audible marker at either end, separated from trial windows.
        add(.15, "Timing chirp", "chirp", 700, 2700, marker=True)
        add(.9, "Hold still")

    add(.6, "Get ready", extra_hold_s=.4 if extended_guard else 0)
    guided = mode in ("Guided pairs", "Head-turn control")
    head_control = mode == "Head-turn control"
    if guided or mode in ("Timing check","Quick Scan"):
        if timing_warmup:
            add(1, "Warm-up tone • hold still", "tone", f0=2000, warmup=True)
            add(.65, "Hold still")
        marker()
    if mode == "Continuous movement":
        if frequency not in (2000, 8000, 16000) or level > .01:
            raise ValueError("Continuous movement requires 2000, 8000 or 16000 Hz and peak at most 0.010.")
        conditions = ["mouth", "head", "off"] * 3
        random.Random(seed).shuffle(conditions)
        for trial, condition in enumerate(conditions, 1):
            start = cursor
            tags = dict(trial=trial, condition=condition)
            add(3, "Close mouth, face forward and hold still", stage="settle", **tags)
            add(3, "Keep mouth closed and still", stage="baseline", **tags)
            prompt = "Slowly turn head left and right, lips closed" if condition == "head" else "Slowly open and close mouth, head still"
            add(6, prompt + (" • probe OFF" if condition == "off" else ""), stage="movement", **tags)
            if condition != "off":
                # One continuous oscillator across all three prompts of this trial.
                count = cursor - start
                wave = (level * np.sin(2 * np.pi * frequency * np.arange(count) / rate)).astype("float32")
                ramp = np.linspace(0, 1, round(.015 * rate)) ** 2
                wave[:len(ramp)] *= ramp
                wave[-len(ramp):] *= ramp[::-1]
                offset = 0
                for piece, event in zip(pieces[-3:], events[-3:]):
                    piece[:] = wave[offset:offset + len(piece)]
                    offset += len(piece)
                    event['kind'] = 'tone'
    elif mode == "Reception check":
        if rate < 44100 or level > .01:
            raise ValueError("Reception check requires 44.1 or 48 kHz and peak at most 0.010.")
        for hz in (2000, 8000, 16000):
            for repeat in range(3):
                for state in ("off", "on"):
                    add(5, f"Keep mouth closed and still • {hz} Hz • probe {state}",
                        "tone" if state == "on" else "quiet", f0=hz,
                        reception_hz=hz, repeat=repeat, state=state)
    elif mode=="Quick Scan":
        if rate*.48<=4000 or not extended_guard or level>.01:
            raise ValueError("Quick Scan requires Setup E, a rate above 8.34 kHz and peak at most 0.010.")
        rng = random.Random(seed)
        # Balance opening first/second, including in the probe-off controls.
        pairs = [(condition,i%2) for condition,count in (("on",6),("off",4),("still",3))
                 for i in range(count)]
        rng.shuffle(pairs)
        for pair,(condition,reverse) in enumerate(pairs,1):
            if pair in (5,9):
                marker()
            poses = ["closed","closed" if condition=="still" else "open"]
            if reverse:
                poses.reverse()
            order = list(SCAN_SETTINGS)
            rng.shuffle(order)
            for slot,pose in enumerate(poses):
                tags = dict(pair=pair,slot=slot,pose=pose,condition=condition)
                add(.5,"Rest • lips gently closed")
                add(1.2,"Move to mouth "+pose,stage="transition",**tags)
                for hz,amp in order:
                    add(.42,"Hold mouth "+pose,"quiet" if condition=="off" else "tone",
                        f0=hz,peak=amp,scan_hz=hz,scan_peak=amp,stage="scan",**tags)
                add(.85,"Hold mouth "+pose,stage="settle_tail",**tags)
        marker()
    elif guided:
        rng = random.Random(seed)
        pairs = ["on", "off", "closed_repeat"] * 10
        rng.shuffle(pairs)
        for pair, condition in enumerate(pairs, 1):
            if extended_guard and pair>1 and (pair-1)%5==0:
                add(.8, "Rest before timing check")
                marker()
            poses = ["closed", "closed" if condition == "closed_repeat" else "open"]
            rng.shuffle(poses)
            for slot, pose in enumerate(poses):
                if head_control:
                    pose = "forward" if pose == "closed" else "turned"
                    action = "face forward" if pose == "forward" else "turn slightly right"
                    move = "Lips closed: " + action
                    hold = "Hold " + pose + " with lips closed"
                else:
                    move, hold = "Move to mouth " + pose, "Hold mouth " + pose
                tags = dict(pair=pair, condition=condition, slot=slot, pose=pose)
                add(1, "Rest with lips closed" if head_control else "Rest")
                add(1.5, move, stage="transition", **tags)
                add(1.6, hold, "quiet" if condition == "off" else "tone",
                    stage="hold", **tags)
                if extended_guard:
                    add(.4, hold, stage="settle_tail", **tags)
        add(.8, "Rest")
        marker()
    elif mode == "Band check":
        for repeat in range(3):
            add(1.5, "Still / probe off", repeat=repeat, state="off")
            add(1.5, "Still / probe on", "tone", repeat=repeat, state="on")
        add(1, "Rest")
    elif mode == "Timing check":
        add(5, "Hold still")
        marker()
    elif mode == "Mic check" and laptop:
        add(3, "Stay quiet")
        add(3, "Say 'testing, one, two' toward the laptop")
        add(3, "Stay quiet again")
    elif mode == "Mic check":
        add(3, "Make a quiet sound close to the boom")
        add(3, "Repeat close to the laptop mic")
        add(3, "Try the boom mute switch, if fitted")
    elif mode in ("Tone", "Sweep"):
        add(duration, "Probe playing", "tone" if mode == "Tone" else "chirp")
    else:
        raise ValueError("Unknown experiment")
    add(1, "Rest / recording tail")
    mono = np.concatenate(pieces)
    tx = np.zeros((len(mono), channels), np.float32)
    if side in ("Both", "Left"):
        tx[:, 0] = mono
    if channels == 2 and side in ("Both", "Right"):
        tx[:, 1] = mono
    return tx, events
