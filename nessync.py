import time, threading, math, array
from collections import deque
import sounddevice as sd  # pip install sounddevice

# -------------------------
# Config
# -------------------------
FPS = 60.0988                 # PPU master frame rate (NTSC)
CPU_HZ = 1789773              # NES CPU clock (NTSC)
APU_NATIVE_HZ = 1789773 / 2   # Conceptual APU tick rate (or your mixer’s internal rate)
OUT_RATE = 48000              # Device sample rate (44_100 or 48_000 are common)
BLOCK = 256                   # PortAudio callback block size (small -> low latency)
RING_CAP = OUT_RATE * 2       # ~2 seconds of ring buffer safety

# -------------------------
# Thread-safe ring buffer
# -------------------------
class Ring:
    def __init__(self, capacity):
        self.q = deque(maxlen=capacity)
        self.cv = threading.Condition()

    def push(self, samples_i16):
        with self.cv:
            self.q.extend(samples_i16)
            self.cv.notify_all()

    def pull(self, n):
        out = array.array('h')
        with self.cv:
            while len(self.q) < n:
                # If starving, wait a bit (or break and output silence)
                self.cv.wait(timeout=0.002)
                if len(self.q) == 0:
                    # return silence to avoid glitch
                    return array.array('h', [0]*n)
            for _ in range(n):
                out.append(self.q.popleft())
        return out

ring = Ring(RING_CAP)

# -------------------------
# Simple linear resampler
# (feed it at APU_NATIVE_HZ; it outputs OUT_RATE)
# -------------------------
class Resampler:
    def __init__(self, in_rate, out_rate):
        self.ratio = in_rate / out_rate
        self.pos = 0.0
        self.last = 0.0

    def process(self, in_f32):
        # in_f32: list/array of floats (-1..1) at in_rate
        out = array.array('h')
        if not in_f32:
            return out
        i = 0
        while True:
            src_idx = int(self.pos)
            frac = self.pos - src_idx
            if src_idx >= len(in_f32)-1:
                break
            a = in_f32[src_idx]
            b = in_f32[src_idx+1]
            samp = a + (b - a)*frac
            out.append(int(max(-1.0, min(1.0, samp)) * 32767))
            self.pos += self.ratio
        # keep last sample for continuity
        self.pos -= (len(in_f32)-1)
        if self.pos < 0: self.pos = 0.0
        return out

resamp = Resampler(APU_NATIVE_HZ, OUT_RATE)

# -------------------------
# PortAudio callback
# -------------------------
def audio_cb(outdata, frames, time_info, status):
    need = frames
    chunk = ring.pull(need)
    # Interleaved mono -> expand to frames
    outdata[:len(chunk)].view('i2')[:] = chunk
    if len(chunk) < need:
        # fill remainder with silence
        zeros = array.array('h', [0] * (need - len(chunk)))
        outdata[len(chunk):].view('i2')[:] = zeros

# -------------------------
# Emu frame loop (mastered by PPU FPS)
# -------------------------
def run_emu():
    target_frame_s = 1.0 / FPS
    next_t = time.perf_counter()
    apu_mix_f32 = []  # collect APU floats per frame at APU_NATIVE_HZ

    while True:
        frame_start = time.perf_counter()

        # 1) Compute how many CPU cycles fit this frame
        cpu_cycles_this_frame = int(round(CPU_HZ / FPS))

        # 2) Step CPU/PPU/APU in lockstep
        cycles_done = 0
        apu_mix_f32.clear()
        while cycles_done < cpu_cycles_this_frame:
            step = 1  # or run an instruction and return its cycle cost
            # cpu.step() -> returns cycles; ppu.step(step*3); apu.step(step)
            # apu.write_samples(...) append to apu_mix_f32 as floats [-1..1]
            cycles_done += step
            # For demo: synth a tiny beep at 440 Hz
            t = cycles_done / APU_NATIVE_HZ
            apu_mix_f32.append(math.sin(2*math.pi*440*t) * 0.2)

        # 3) Resample APU to device rate, push to ring
        out_i16 = resamp.process(apu_mix_f32)
        if len(out_i16):
            ring.push(out_i16)

        # 4) Frame pacing (PPU as master)
        next_t += target_frame_s
        sleep_s = next_t - time.perf_counter()
        if sleep_s > 0:
            time.sleep(sleep_s)
        else:
            # fell behind; reset schedule to now to avoid spiral of death
            next_t = time.perf_counter()

# -------------------------
# Boot audio + threads
# -------------------------
def main():
    stream = sd.OutputStream(
        samplerate=OUT_RATE,
        channels=1,
        dtype='int16',
        blocksize=BLOCK,
        callback=audio_cb,
        latency='low'   # or 'exclusive' on some setups
    )
    with stream:
        run_emu()

if __name__ == "__main__":
    main()
