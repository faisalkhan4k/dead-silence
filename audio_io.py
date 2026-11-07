"""Capture only. No plotting, filesystem access, gain control or DSP in callbacks."""
import time
import numpy as np
import sounddevice as sd


def devices():
    hosts = sd.query_hostapis()
    return [dict(id=i, name=d["name"], host=hosts[d["hostapi"]]["name"],
                 host_id=d["hostapi"], inputs=d["max_input_channels"],
                 outputs=d["max_output_channels"], default_rate=d["default_samplerate"])
            for i, d in enumerate(sd.query_devices())]


def rates_for(mic, speaker, channels):
    candidates = dict.fromkeys([48000, 44100, int(mic["default_rate"]),
                                int(speaker["default_rate"]), 32000, 24000, 16000])
    result = {}
    for rate in candidates:
        try:
            sd.check_input_settings(device=mic["id"], channels=1, dtype="float32", samplerate=rate)
            sd.check_output_settings(device=speaker["id"], channels=channels, dtype="float32", samplerate=rate)
            result[rate] = "formats accepted separately"
        except (sd.PortAudioError, ValueError) as exc:
            result[rate] = str(exc)
    return result


class Capture:
    def __init__(self, tx, rate, latency="low"):
        self.tx, self.rate = tx, rate
        self.latency = latency
        self.rx = np.empty(len(tx), np.float32)
        self.nin = self.nout = 0
        self.timing, self.errors, self.streams = [], [], []
        self.mode = ""
        self.details = []

    def block(self, incoming, outgoing, frames, times, status):
        ni, no = self.nin, self.nout
        if incoming is not None:
            n = min(frames, len(self.rx) - ni)
            self.rx[ni:ni+n] = incoming[:n, 0]
            self.nin += n
        if outgoing is not None:
            n = min(frames, len(self.tx) - no)
            outgoing.fill(0)
            outgoing[:n] = self.tx[no:no+n]
            self.nout += n
        self.timing.append((time.perf_counter(), ni if incoming is not None else -1,
                            no if outgoing is not None else -1, frames, times.inputBufferAdcTime,
                            times.outputBufferDacTime, times.currentTime, str(status)))
        if status:
            self.errors.append(str(status))

    def open(self, mic, speaker):
        args = dict(samplerate=self.rate, dtype="float32", blocksize=0, latency=self.latency)
        channels = self.tx.shape[1]
        try:
            stream = sd.Stream(device=(mic, speaker), channels=(1, channels),
                               callback=self.block, **args)
            self.streams = [stream]
            self.mode = "duplex"
            stream.start()
        except sd.PortAudioError as exc:
            self.close()
            if self.nin or self.nout:
                raise
            self.details.append("Duplex unavailable: " + str(exc))
            self.mode = "separate streams"
            try:
                self.streams.append(sd.InputStream(device=mic, channels=1,
                    callback=lambda data, n, t, s: self.block(data, None, n, t, s), **args))
                self.streams.append(sd.OutputStream(device=speaker, channels=channels,
                    callback=lambda data, n, t, s: self.block(None, data, n, t, s), **args))
                for stream in self.streams:
                    stream.start()
            except Exception:
                self.close()
                raise
        self.details.extend(dict(rate=s.samplerate, latency=s.latency) for s in self.streams)

    def close(self):
        for stream in self.streams[::-1]:
            try:
                stream.abort()
            finally:
                stream.close()
        self.streams.clear()
