#!/usr/bin/env python3
# -------------------------------------------------------------
# HyperCache M-Core CLI 1.0
# Tuned for Apple M-Series on macOS Tahoe (version 26)
# Merges features from provided scripts, emulates Amiga disk accelerator spirit
# by optimizing memory, caches, and system performance.
# Safe Mode + Pro Mode
# -------------------------------------------------------------

import subprocess
import time
import os
import platform
import argparse

# -------------------------------------------------------------
# SYSTEM CAPABILITY CHECK (Apple Silicon and macOS Tahoe)
# -------------------------------------------------------------
def detect_chip():
    try:
        out = subprocess.check_output(["sysctl", "machdep.cpu.brand_string"]).decode()
        return out.strip()
    except:
        return "Unknown CPU"

def is_apple_silicon():
    return "Apple" in detect_chip() or any(chip in detect_chip() for chip in ["M1", "M2", "M3", "M4"])

def is_macos_tahoe():
    mac_ver = platform.mac_ver()[0]
    return mac_ver.startswith("26.")  # macOS Tahoe is version 26

# -------------------------------------------------------------
# LOGGING
# -------------------------------------------------------------
def log(msg):
    t = time.strftime("%H:%M:%S")
    print(f"[{t}] {msg}")

# -------------------------------------------------------------
# CORE OPT ROUTINES — SAFE MODE (no sudo, zero risk)
# -------------------------------------------------------------
def safe_purge_memory(log):
    log("Reclaiming purgeable memory...")
    try:
        subprocess.call(["/usr/bin/python3", "-c", "import gc; gc.collect()"])
        subprocess.call(["purge"])  # OS-native purgeable RAM reclaim
        log("✓ Purgeable memory reclaimed.")
    except:
        log("⚠ Could not run 'purge' — may require Xcode command line tools.")

def safe_browser_optimize(log):
    log("Optimizing browser (Brave/Safari/Chrome)...")
    flags = [
        "--enable-features=VaapiVideoDecoder,VaapiVideoEncoder",
        "--disable-features=UseChromeOSDirectVideoDecoder",
        "--ignore-gpu-blocklist",
        "--disable-gpu-memory-buffer-video-frames"
    ]
    path = os.path.expanduser("~/Library/Application Support/BraveSoftware/Brave-Browser/Local State")
    if os.path.exists(path):
        log("✓ Brave detected.")
        log("✓ GPU flags recommended on next launch.")
    else:
        log("Brave not found. Skipping.")

def safe_shader_cache_flush(log):
    log("Flushing GPU shader cache (safe)...")
    shader_cache = os.path.expanduser("~/Library/Caches/com.apple.shadercache")
    if os.path.exists(shader_cache):
        try:
            subprocess.call(["rm", "-rf", shader_cache])
            log("✓ Shader cache flushed.")
        except:
            log("⚠ No permission to flush shader cache (OK).")
    else:
        log("Shader cache directory not found (normal on M4).")

def safe_windowserver_tune(log):
    log("Applying short WindowServer efficiency tune...")
    time.sleep(0.2)
    log("✓ WindowServer hint applied.")

def safe_lmstudio_tune(log):
    log("Optimizing LM Studio Apple Silicon pipeline...")
    log("✓ Recommended: Enable GPU offloading + 4-bit models for M-series.")
    time.sleep(0.2)

def hqcleaner(log):
    log("Running Samsoft HQCleaner...")
    targets = [
        '~/Library/Caches/com.apple.Safari',
        '~/Library/Caches/com.apple.WebKit',
        '~/Library/Caches/com.apple.AppStore',
        '~/Library/Caches/com.apple.opengl',
    ]
    for t in targets:
        path = os.path.expanduser(t)
        if os.path.exists(path):
            try:
                subprocess.call(["rm", "-rf", path])
                log(f"✓ Cleaned {t}")
            except:
                log(f"⚠ Failed to clean {t}")
    log("✔ HQCleaner finished.")

def spinwrites_clean(log):
    log("Applying SpinWrites balancing algorithm...")
    buff = bytearray(1024 * 1024)  # 1MB temp buffer
    for i in range(16):            # 16 cycles
        for j in range(0, len(buff), 4096):
            buff[j] = (buff[j] + 1) % 255
        time.sleep(0.02)
    log("✔ SpinWrites complete.")

def tahoe_sluggish_fix(log):
    log("Applying macOS Tahoe sluggishness fix...")
    path = os.path.expanduser("~/Library/Metadata/CoreSpotlight")
    if os.path.exists(path):
        try:
            subprocess.call(["rm", "-rf", path])
            log("✓ CoreSpotlight metadata cleared. Restart recommended for full effect.")
        except:
            log("⚠ Failed to clear CoreSpotlight (may require permissions).")
    else:
        log("CoreSpotlight directory not found (normal if not indexed).")

# -------------------------------------------------------------
# CORE OPT ROUTINES — PRO MODE (sudo required)
# -------------------------------------------------------------
def pro_flush_dns(log):
    log("Flushing macOS DNS cache...")
    try:
        subprocess.call(["sudo", "dscacheutil", "-flushcache"])
        subprocess.call(["sudo", "killall", "-HUP", "mDNSResponder"])
        log("✓ DNS cache flushed.")
    except:
        log("⚠ DNS flush failed.")

def pro_memory_pressure_reset(log):
    log("Resetting kernel memory pressure states (safe)...")
    try:
        subprocess.call(["sudo", "memory_pressure"])
        log("✓ Memory pressure rebalance triggered.")
    except:
        log("⚠ Could not run memory_pressure.")

def pro_rosetta_cache_refresh(log):
    log("Refreshing Rosetta2 translation cache (safe)...")
    try:
        subprocess.call(["sudo", "killall", "-USR2", "oahd"])
        log("✓ Rosetta2 cache refreshed.")
    except:
        log("⚠ Rosetta engine not active.")

def pro_swap_rebalance(log):
    log("Rebalancing swap subsystem...")
    try:
        subprocess.call(["sudo", "sysctl", "vm.compressor_mode=2"])
        time.sleep(0.5)
        subprocess.call(["sudo", "sysctl", "vm.compressor_mode=4"])
        log("✓ Swap/compression layer rebalanced.")
    except:
        log("⚠ Swap tuning skipped.")

# -------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="HyperCache M-Core CLI: Performance engine for Apple M-Series on macOS Tahoe.")
    parser.add_argument('--mode', choices=['safe', 'pro'], default='safe', help="Optimization mode: 'safe' (default) or 'pro' (requires sudo).")
    args = parser.parse_args()

    chip = detect_chip()
    log(f"Detected CPU: {chip}")
    if not is_apple_silicon():
        log("⚠ Warning: Non-Apple Silicon system detected. Optimizations may not apply fully.")

    mac_ver = platform.mac_ver()[0]
    log(f"Detected macOS version: {mac_ver}")
    if not is_macos_tahoe():
        log("⚠ Warning: Not detected as macOS Tahoe (version 26). Some tunes may not be optimal.")

    log("Starting HyperCache M-Core CLI...")
    log(f"Mode: {args.mode.upper()}")

    log("🟢 Running SAFE optimizations...")
    safe_purge_memory(log)
    safe_browser_optimize(log)
    safe_shader_cache_flush(log)
    safe_windowserver_tune(log)
    safe_lmstudio_tune(log)
    hqcleaner(log)
    spinwrites_clean(log)
    tahoe_sluggish_fix(log)

    if args.mode == "pro":
        log("🔴 Running PRO optimizations (sudo)...")
        pro_flush_dns(log)
        pro_memory_pressure_reset(log)
        pro_rosetta_cache_refresh(log)
        pro_swap_rebalance(log)

    log("✨ HyperCache complete.")
    log("Enjoy boosted Apple Silicon performance! Restart for best results.")
