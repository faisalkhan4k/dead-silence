import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import numpy as np
from analysis import report


ROOT = Path(__file__).resolve().parent / "sessions"


def session_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]


def save(cap, metadata):
    path = ROOT / metadata["id"]
    path.mkdir(parents=True, exist_ok=False)
    # A partial directory remains identifiable if a write is interrupted.
    rx, tx = cap.rx[:cap.nin], cap.tx[:cap.nout]
    np.save(path/"mic.npy", rx)
    np.save(path/"output.npy", tx)
    if metadata['mode'] in ('Reception check', 'Continuous movement'):
        from scipy.io.wavfile import write
        write(path/'mic.wav', metadata['rate'], rx)
        write(path/'output.wav', metadata['rate'], tx)
    with (path/"timing.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["monotonic_s","input_frame","output_frame","frames","adc_s","dac_s","stream_s","flags"])
        writer.writerows(cap.timing)
    metadata.update(stream_mode=cap.mode, stream_details=cap.details, audio_flags=sorted(set(cap.errors)),
                    input_frames=cap.nin, output_frames=cap.nout)
    (path/"session.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    result = report(rx,tx,metadata)
    (path/"report.json").write_text(json.dumps(result,indent=2), encoding="utf-8")
    return path, result
