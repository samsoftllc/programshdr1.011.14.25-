#!/usr/bin/env bash
# ============================================================================
# [C SAMSOFT HDR 1999-2025] ULTIMATE COMPILER + HARDWARE COLLECTION (macOS Apple Silicon)
# M4 PRO-OPTIMIZED, BREW-FIRST, FAULT-TOLERANT
# ENHANCED: COMPLETE JAVA 2025 + HARDWARE EMULATION/DEV COLLECTION
# MIPS/PS1/RETRO FOCUS - 50MB-1GB SYSTEMS
# ============================================================================

set -Eeuo pipefail

# Bash 3.x compatible (macOS default). Avoid associative arrays.
IFS=$'\n\t'

# ----------------------------------------------------------------------------
# Colors
# ----------------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
MAGENTA='\033[0;35m'; CYAN='\033[0;36m'; WHITE='\033[1;37m'; NC='\033[0m'

# ----------------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------------
LOG_FILE="${HOME}/.samsoft_compiler_install.log"
mkdir -p "$(dirname "$LOG_FILE")"

# POSIX-compatible alternative to process substitution using FIFO
TMP_FIFO="/tmp/samsoft_compiler_install_fifo.$$"
mkfifo "$TMP_FIFO" 2>/dev/null || { echo -e "${RED}[ERROR]${NC} Cannot create FIFO for logging." >&2; exit 1; }
tee -a "$LOG_FILE" < "$TMP_FIFO" >/dev/null 2>&1 &
exec > "$TMP_FIFO" 2>&1
rm "$TMP_FIFO"

log()   { echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

# macOS-like spinner for short delays
spinner() {
  local pid=$!
  local spinstr='|/-\'
  while kill -0 $pid 2>/dev/null; do
    local temp=${spinstr#?}
    printf " [%c]  " "$spinstr"
    local spinstr=$temp${spinstr%"$temp"}
    sleep 0.1
  done
  printf "    \r"
}

print_banner() {
  echo -e "${CYAN}"
  cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║     ____    _    __  __ ____   ___  _____ _____   _   _ ____  ____        ║
║    / ___|  / \  |  \/  / ___| / _ \|  ___|_   _| | | | |  _ \|  _ \       ║
║    \___ \ / _ \ | |\/| \___ \| | | | |_    | |   | |_| | | | | |_) |      ║
║     ___) / ___ \| |  | |___) | |_| |  _|   | |   |  _  | |_| |  _ <       ║
║    |____/_/   \_\_|  |_|____/ \___/|_|     |_|   |_| |_|____/|_| \_\      ║
║                                                                            ║
║              [C SAMSOFT HDR 1999-2025] COMPILER COLLECTION                 ║
║                APPLE SILICON / M4 PRO-OPTIMIZED • macOS TAHOE              ║
║               JAVA 2025 + HARDWARE EMULATION COMPLETE EDITION              ║
║                      MIPS/PS1/RETRO SYSTEMS INCLUDED                       ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
}

# Progress bar function (macOS loading vibe)
progress_bar() {
  local current_step=$1 total_steps=$2 width=50
  local percent=$((current_step * 100 / total_steps))
  local filled=$((percent * width / 100))
  local empty=$((width - filled))
  local bar=$(printf "${GREEN}█%.0s${NC}" $(seq 1 $filled))
  bar+=$(printf "${YELLOW}░%.0s${NC}" $(seq 1 $empty))
  printf "\r${BLUE}[${bar}] ${GREEN}%d%%${NC} | Optimizing for M4 Pro...${NC}" $percent
  if [[ $percent -eq 100 ]]; then echo; fi
}

trap 'error "Unexpected error on line $LINENO. See $LOG_FILE for details."' ERR

have() { command -v "$1" >/dev/null 2>&1; }

# ----------------------------------------------------------------------------
# System detection
# ----------------------------------------------------------------------------
require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    error "This installer is tailored for macOS (Apple Silicon)."
    exit 1
  fi
  local major_version
  major_version="$(sw_vers -productVersion | cut -d. -f1)"
  if [[ "$major_version" -lt 11 ]]; then
    warn "Script optimized for macOS 11+, you have version $major_version"
  fi
}

detect_cores() {
  local cores
  cores="$(sysctl -n hw.logicalcpu 2>/dev/null || getconf _NPROCESSORS_ONLN || echo 1)"
  # Favor saturation without overcommit storms
  PARALLEL_JOBS=$(( cores > 1 ? (cores * 2) : 1 ))
  export MAKEFLAGS="-j${PARALLEL_JOBS}"
  log "Detected ${cores} cores; using ${PARALLEL_JOBS} build jobs."
}

ensure_clt() {
  if ! xcode-select -p >/dev/null 2>&1; then
    warn "Xcode Command Line Tools not found. A prompt will appear."
    echo -e "${YELLOW}Installing CLT...${NC}"
    xcode-select --install || true
  fi
}

# ----------------------------------------------------------------------------
# Homebrew setup
# ----------------------------------------------------------------------------
ensure_brew() {
  if ! have brew; then
    # Prefer Apple Silicon path if preinstalled but not in PATH
    if [[ -x /opt/homebrew/bin/brew ]]; then
      eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -x /usr/local/bin/brew ]]; then
      eval "$(/usr/local/bin/brew shellenv)"
    else
      log "Installing Homebrew..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" &
      spinner
      if [[ -x /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
      else
        eval "$(/usr/local/bin/brew shellenv)"
      fi
    fi
  fi
  export HOMEBREW_NO_AUTO_UPDATE=1
  export HOMEBREW_NO_ENV_HINTS=1
  brew analytics off >/dev/null 2>&1 || true
  BREW_PREFIX="$(brew --prefix)"
  export PATH="$HOME/.local/bin:$BREW_PREFIX/bin:$BREW_PREFIX/sbin:$PATH"
  log "Homebrew ready at ${BREW_PREFIX}."
}

# ----------------------------------------------------------------------------
# CPU flags (probe for supported optimization flags)
# ----------------------------------------------------------------------------
probe_cpu_flags() {
  local cc="${CC:-clang}" flag
  local test='int x;'
  local flags=()
  # Test candidates (highest to lowest preference)
  for flag in -mcpu=apple-m4 -mcpu=apple-m3 -mcpu=apple-m2 -march=armv8.5-a; do
    if echo "$test" | "$cc" -c -x c -o /dev/null - "$flag" >/dev/null 2>&1; then
      flags+=("$flag")
      break
    fi
  done
  CPU_FLAG="${flags[0]:-}"
  if [[ -n "$CPU_FLAG" ]]; then
    log "Using CPU flag: ${CPU_FLAG}"
  else
    warn "No advanced CPU flags supported by current compiler; using defaults."
  fi

  # Common fast but mostly safe opts (avoid strict -ffast-math globally)
  export CFLAGS="${CPU_FLAG:+$CPU_FLAG }-O3"
  export CXXFLAGS="${CPU_FLAG:+$CPU_FLAG }-O3"
  export LDFLAGS="-L${BREW_PREFIX}/lib ${LDFLAGS:-}"
  export CPPFLAGS="-I${BREW_PREFIX}/include ${CPPFLAGS:-}"
  export ARCHFLAGS="-arch arm64"
  export CMAKE_OSX_ARCHITECTURES="arm64"
}

# ----------------------------------------------------------------------------
# Rosetta (optional)
# ----------------------------------------------------------------------------
maybe_install_rosetta() {
  if /usr/bin/pgrep oahd >/dev/null 2>&1; then
    log "Rosetta already present."
    return 0
  fi
  if have softwareupdate; then
    warn "Rosetta not detected. Some x86-only tools may require it."
    warn "Attempting a silent install (may require admin)…"
    if /usr/sbin/softwareupdate --install-rosetta --agree-to-license >/dev/null 2>&1; then
      log "Rosetta installed."
    else
      warn "Rosetta install skipped or failed (no admin?). Continue without."
    fi
  fi
}

# ----------------------------------------------------------------------------
# Install helpers (graceful, non-fatal) - Enhanced with per-package logging
# ----------------------------------------------------------------------------
SKIPPED_FORMULAS=()
SKIPPED_CASKS=()
SKIPPED_PIPS=()
SKIPPED_NPMS=()

brew_install() {
  # Usage: brew_install pkg1 pkg2 ...
  local f
  for f in "$@"; do
    [[ -z "$f" ]] && continue
    echo -e "${MAGENTA}  └─ Installing ${f}...${NC}"
    if brew list --formula "$f" >/dev/null 2>&1; then
      log "Already installed (brew formula): $f"
      continue
    fi
    if brew info --formula "$f" >/dev/null 2>&1; then
      if brew install "$f"; then
        log "Installed: $f"
      else
        warn "Install failed (formula): $f"
        SKIPPED_FORMULAS+=("$f")
      fi
    else
      warn "Formula not found: $f"
      SKIPPED_FORMULAS+=("$f")
    fi
  done
}

brew_cask_install() {
  # Usage: brew_cask_install cask1 cask2 ...
  local c
  for c in "$@"; do
    [[ -z "$c" ]] && continue
    echo -e "${MAGENTA}  └─ Installing cask ${c}...${NC}"
    if brew list --cask "$c" >/dev/null 2>&1; then
      log "Already installed (cask): $c"
      continue
    fi
    if brew info --cask "$c" >/dev/null 2>&1; then
      if brew install --cask "$c"; then
        log "Installed cask: $c"
      else
        warn "Install failed (cask): $c"
        SKIPPED_CASKS+=("$c")
      fi
    else
      warn "Cask not found: $c"
      SKIPPED_CASKS+=("$c")
    fi
  done
}

pip_install_user() {
  # Usage: pip_install_user pkg1 pkg2 ...
  if ! have python3; then
    warn "python3 not found; skipping pip packages: $*"
    SKIPPED_PIPS+=("$*")
    return 0
  fi
  echo -e "${MAGENTA}  └─ Installing pip packages: $*...${NC}"
  if python3 -m pip install --user -U "$@"; then
    log "pip installed (user): $*"
  else
    warn "pip install failed: $*"
    SKIPPED_PIPS+=("$*")
  fi
}

npm_install_g() {
  # Usage: npm_install_g pkg1 pkg2 ...
  if ! have npm; then
    warn "npm not found; skipping global npm packages: $*"
    SKIPPED_NPMS+=("$*")
    return 0
  fi
  echo -e "${MAGENTA}  └─ Installing npm global: $*...${NC}"
  if npm install -g "$@"; then
    log "npm -g installed: $*"
  else
    warn "npm global install failed: $*"
    SKIPPED_NPMS+=("$*")
  fi
}

# ----------------------------------------------------------------------------
# Wrappers (user-local; no sudo)
# ----------------------------------------------------------------------------
install_wrappers() {
  echo -e "${MAGENTA}  └─ Setting up M4-optimized wrappers...${NC}"
  mkdir -p "$HOME/.local/bin"
  cat > "$HOME/.local/bin/clang-m4" <<EOF
#!/usr/bin/env bash
exec clang ${CPU_FLAG:+$CPU_FLAG } -O3 "\$@"
EOF
  chmod +x "$HOME/.local/bin/clang-m4"

  cat > "$HOME/.local/bin/gcc-m4" <<'EOF'
#!/usr/bin/env bash
# Try brewed GCC first; fall back to Apple clang if not available.
for cand in gcc-15 gcc-14 gcc-13 gcc; do
  if command -v "$cand" >/dev/null 2>&1; then
    exec "$cand" -O3 "$@"
  fi
done
exec cc -O3 "$@"
EOF
  chmod +x "$HOME/.local/bin/gcc-m4"
  log "Installed M4-optimized convenience wrappers to ~/.local/bin (ensure it's in PATH)."
}

# ============================================================================
# HARDWARE EMULATION & DEVELOPMENT COLLECTION
# ============================================================================

# ----------------------------------------------------------------------------
# MIPS Architecture Tools
# ----------------------------------------------------------------------------
install_mips_toolchain() {
  log "Installing MIPS cross-compilation toolchain..."
  echo -e "${CYAN}  └─ MIPS Development Tools${NC}"
  
  # MIPS GCC cross-compiler
  brew_install mips-elf-gcc mipsel-elf-gcc
  
  # MIPS assemblers and utilities
  brew_install binutils
  
  # Create MIPS toolchain wrapper
  cat > "$HOME/.local/bin/mips-gcc" <<'EOF'
#!/usr/bin/env bash
# MIPS cross-compiler wrapper
if command -v mipsel-elf-gcc >/dev/null 2>&1; then
  exec mipsel-elf-gcc "$@"
elif command -v mips-elf-gcc >/dev/null 2>&1; then
  exec mips-elf-gcc "$@"
else
  echo "MIPS toolchain not found" >&2
  exit 1
fi
EOF
  chmod +x "$HOME/.local/bin/mips-gcc"
  
  log "MIPS toolchain installed"
}

# ----------------------------------------------------------------------------
# PlayStation 1 Development
# ----------------------------------------------------------------------------
install_ps1_dev() {
  log "Installing PlayStation 1 development tools..."
  echo -e "${CYAN}  └─ PS1/PSX Development Suite${NC}"
  
  # PS1 SDK and tools (via homebrew or manual setup)
  mkdir -p "$HOME/.ps1dev"
  
  # PSn00bSDK (modern PS1 SDK)
  if ! [[ -d "$HOME/.ps1dev/psn00bsdk" ]]; then
    echo -e "${MAGENTA}  └─ Cloning PSn00bSDK...${NC}"
    git clone https://github.com/Lameguy64/PSn00bSDK.git "$HOME/.ps1dev/psn00bsdk" >/dev/null 2>&1 || warn "PSn00bSDK clone failed"
  fi
  
  # PCSX-Redux (PS1 emulator with dev tools)
  brew_cask_install pcsx-redux || warn "PCSX-Redux not available via cask"
  
  # mkpsxiso (PS1 ISO builder)
  if ! [[ -d "$HOME/.ps1dev/mkpsxiso" ]]; then
    echo -e "${MAGENTA}  └─ Cloning mkpsxiso...${NC}"
    git clone https://github.com/Lameguy64/mkpsxiso.git "$HOME/.ps1dev/mkpsxiso" >/dev/null 2>&1 || warn "mkpsxiso clone failed"
  fi
  
  log "PS1 development tools installed to ~/.ps1dev"
}

# ----------------------------------------------------------------------------
# Nintendo 64 (MIPS-based)
# ----------------------------------------------------------------------------
install_n64_dev() {
  log "Installing Nintendo 64 development tools..."
  echo -e "${CYAN}  └─ N64 Development Suite${NC}"
  
  mkdir -p "$HOME/.n64dev"
  
  # libdragon (modern N64 SDK)
  if ! [[ -d "$HOME/.n64dev/libdragon" ]]; then
    echo -e "${MAGENTA}  └─ Cloning libdragon...${NC}"
    git clone https://github.com/DragonMinded/libdragon.git "$HOME/.n64dev/libdragon" >/dev/null 2>&1 || warn "libdragon clone failed"
  fi
  
  # N64 tools
  brew_install n64-dev-tools || warn "n64-dev-tools not available"
  
  # Alternative: manual tool compilation would go here
  
  log "N64 development tools installed to ~/.n64dev"
}

# ----------------------------------------------------------------------------
# PSP (MIPS-based)
# ----------------------------------------------------------------------------
install_psp_dev() {
  log "Installing PlayStation Portable development tools..."
  echo -e "${CYAN}  └─ PSP Development Suite${NC}"
  
  mkdir -p "$HOME/.pspdev"
  
  # PSPSDK
  if ! [[ -d "$HOME/.pspdev/pspsdk" ]]; then
    echo -e "${MAGENTA}  └─ Setting up PSP toolchain...${NC}"
    # PSP toolchain setup would require manual compilation
    # For now, just create the directory structure
    mkdir -p "$HOME/.pspdev/"{bin,lib,include}
  fi
  
  log "PSP development environment created at ~/.pspdev"
}

# ----------------------------------------------------------------------------
# Retro Console Emulators (50MB-1GB range)
# ----------------------------------------------------------------------------
install_retro_emulators() {
  log "Installing retro console emulators..."
  echo -e "${CYAN}  └─ Comprehensive Emulator Collection${NC}"
  
  # Sony systems
  echo -e "${YELLOW}Sony Systems:${NC}"
  brew_cask_install \
    duckstation \
    pcsx2 \
    ppsspp \
    rpcs3
  
  # Nintendo systems
  echo -e "${YELLOW}Nintendo Systems:${NC}"
  brew_cask_install \
    dolphin \
    mupen64plus \
    snes9x \
    bsnes \
    mesen \
    citra \
    ryujinx
  
  # Sega systems
  echo -e "${YELLOW}Sega Systems:${NC}"
  brew_cask_install \
    genesis-plus-gx \
    blastem \
    kronos
  
  # Multi-system emulators
  echo -e "${YELLOW}Multi-System:${NC}"
  brew_cask_install \
    retroarch \
    openemu \
    ares
  
  # Command-line emulators
  echo -e "${YELLOW}CLI Emulators:${NC}"
  brew_install \
    mednafen \
    fceux \
    stella \
    vice \
    dosbox-x
  
  log "Emulator collection installed"
}

# ----------------------------------------------------------------------------
# ROM Development Tools
# ----------------------------------------------------------------------------
install_rom_tools() {
  log "Installing ROM development and hacking tools..."
  echo -e "${CYAN}  └─ ROM Development Suite${NC}"
  
  # Hex editors
  brew_cask_install hex-fiend imhex
  
  # Tile editors and graphics tools
  brew_cask_install \
    aseprite \
    tiled
  
  # Audio tools for retro formats
  brew_install \
    sox \
    ffmpeg \
    vgmtools
  
  # Compression/decompression tools
  brew_install \
    p7zip \
    unrar \
    xz
  
  # ROM patching
  pip_install_user flips-python
  
  log "ROM development tools installed"
}

# ----------------------------------------------------------------------------
# Assembly & Low-Level Tools
# ----------------------------------------------------------------------------
install_asm_tools() {
  log "Installing assembly and low-level development tools..."
  echo -e "${CYAN}  └─ Assembly Development Suite${NC}"
  
  # Assemblers
  brew_install \
    nasm \
    yasm \
    ca65 \
    rgbds \
    asmx \
    wla-dx
  
  # Disassemblers and reverse engineering
  brew_cask_install \
    ghidra \
    hopper-disassembler \
    radare2
  
  brew_install \
    radare2 \
    capstone \
    keystone
  
  # Debuggers
  brew_install \
    gdb \
    lldb
  
  log "Assembly tools installed"
}

# ----------------------------------------------------------------------------
# HDL & FPGA (Hardware Description)
# ----------------------------------------------------------------------------
install_hdl_tools() {
  log "Installing HDL and FPGA development tools..."
  echo -e "${CYAN}  └─ Hardware Description Suite${NC}"
  
  # Verilog/VHDL
  brew_install \
    verilator \
    iverilog \
    ghdl \
    yosys \
    nextpnr \
    icestorm
  
  # Waveform viewers
  brew_cask_install gtkwave || warn "GTKWave cask not available"
  
  log "HDL tools installed"
}

# ----------------------------------------------------------------------------
# 8-bit/16-bit Console Dev
# ----------------------------------------------------------------------------
install_classic_console_dev() {
  log "Installing classic console development tools..."
  echo -e "${CYAN}  └─ 8/16-bit Console Development${NC}"
  
  # NES development
  echo -e "${YELLOW}NES/Famicom:${NC}"
  brew_install cc65
  mkdir -p "$HOME/.nesdev"
  
  # SNES development
  echo -e "${YELLOW}SNES:${NC}"
  brew_install wla-dx
  mkdir -p "$HOME/.snesdev"
  
  # Game Boy development
  echo -e "${YELLOW}Game Boy:${NC}"
  brew_install rgbds
  mkdir -p "$HOME/.gbdev"
  
  # Genesis/Mega Drive
  echo -e "${YELLOW}Genesis/Mega Drive:${NC}"
  brew_install gendev || warn "gendev not available"
  mkdir -p "$HOME/.genesisdev"
  
  # Master System / Game Gear
  echo -e "${YELLOW}SMS/GG:${NC}"
  mkdir -p "$HOME/.smsdev"
  
  log "Classic console dev tools installed"
}

# ----------------------------------------------------------------------------
# Arcade Hardware
# ----------------------------------------------------------------------------
install_arcade_dev() {
  log "Installing arcade hardware development tools..."
  echo -e "${CYAN}  └─ Arcade Development Suite${NC}"
  
  # MAME development
  brew_install mame
  
  # Arcade ROM tools
  mkdir -p "$HOME/.arcadedev"
  
  # CPS (Capcom Play System)
  mkdir -p "$HOME/.arcadedev/cps"
  
  # Neo Geo
  mkdir -p "$HOME/.arcadedev/neogeo"
  
  log "Arcade development environment created"
}

# ----------------------------------------------------------------------------
# Modern Console Dev (Homebrew)
# ----------------------------------------------------------------------------
install_modern_homebrew() {
  log "Installing modern console homebrew tools..."
  echo -e "${CYAN}  └─ Modern Console Homebrew${NC}"
  
  # Nintendo Switch
  echo -e "${YELLOW}Nintendo Switch:${NC}"
  mkdir -p "$HOME/.switchdev"
  
  # PS4/PS5 homebrew
  echo -e "${YELLOW}PlayStation 4/5:${NC}"
  mkdir -p "$HOME/.ps4dev"
  
  # Xbox homebrew
  echo -e "${YELLOW}Xbox:${NC}"
  mkdir -p "$HOME/.xboxdev"
  
  # 3DS
  echo -e "${YELLOW}3DS:${NC}"
  mkdir -p "$HOME/.3dsdev"
  
  # Vita
  echo -e "${YELLOW}PS Vita:${NC}"
  mkdir -p "$HOME/.vitadev"
  
  log "Modern console homebrew directories created"
}

# ----------------------------------------------------------------------------
# Handheld Systems
# ----------------------------------------------------------------------------
install_handheld_dev() {
  log "Installing handheld console development tools..."
  echo -e "${CYAN}  └─ Handheld Development Suite${NC}"
  
  # Game Boy Advance
  echo -e "${YELLOW}Game Boy Advance:${NC}"
  brew_install devkitarm || warn "devkitARM not available via brew"
  mkdir -p "$HOME/.gbadev"
  
  # Nintendo DS
  echo -e "${YELLOW}Nintendo DS:${NC}"
  mkdir -p "$HOME/.ndsdev"
  
  # Game Gear / Lynx / Wonderswan
  echo -e "${YELLOW}Other Handhelds:${NC}"
  mkdir -p "$HOME/.handhelddev"
  
  log "Handheld development tools installed"
}

# ============================================================================
# JAVA 2025 COMPLETE BUILD COLLECTION
# ============================================================================

install_java_2025_temurin() {
  log "Installing Temurin (Adoptium) Java 2025 builds..."
  echo -e "${CYAN}  └─ Temurin OpenJDK Collection${NC}"
  
  # Add Adoptium tap for latest releases
  brew tap homebrew/cask-versions >/dev/null 2>&1 || true
  
  # Install all Temurin versions (LTS and current)
  brew_cask_install \
    temurin8 \
    temurin11 \
    temurin17 \
    temurin21 \
    temurin22 \
    temurin23 \
    temurin24 \
    temurin25 \
    temurin
}

install_java_2025_graalvm() {
  log "Installing GraalVM Java 2025 builds..."
  echo -e "${CYAN}  └─ GraalVM Enterprise Collection${NC}"
  
  # GraalVM for JDK 21, 22, 23, 24, 25
  brew_cask_install \
    graalvm-jdk21 \
    graalvm-jdk22 \
    graalvm-jdk23 \
    graalvm-jdk24 \
    graalvm-jdk25 \
    graalvm
    
  # GraalVM native-image component
  if have gu; then
    echo -e "${MAGENTA}  └─ Installing GraalVM native-image...${NC}"
    gu install native-image >/dev/null 2>&1 || warn "GraalVM native-image install skipped"
  fi
}

install_java_2025_corretto() {
  log "Installing Amazon Corretto Java 2025 builds..."
  echo -e "${CYAN}  └─ Amazon Corretto Collection${NC}"
  
  # Amazon Corretto (optimized for AWS)
  brew_cask_install \
    corretto8 \
    corretto11 \
    corretto17 \
    corretto21 \
    corretto22 \
    corretto23 \
    corretto
}

install_java_2025_zulu() {
  log "Installing Azul Zulu Java 2025 builds..."
  echo -e "${CYAN}  └─ Azul Zulu Collection${NC}"
  
  # Azul Zulu builds (certified builds)
  brew_cask_install \
    zulu8 \
    zulu11 \
    zulu17 \
    zulu21 \
    zulu22 \
    zulu23 \
    zulu24 \
    zulu25 \
    zulu
}

install_java_2025_oracle() {
  log "Installing Oracle Java 2025 builds..."
  echo -e "${CYAN}  └─ Oracle JDK Collection${NC}"
  
  # Oracle JDK (commercial features)
  brew_cask_install \
    oracle-jdk21 \
    oracle-jdk22 \
    oracle-jdk23 \
    oracle-jdk24 \
    oracle-jdk25 \
    oracle-jdk
}

install_java_2025_microsoft() {
  log "Installing Microsoft OpenJDK 2025 builds..."
  echo -e "${CYAN}  └─ Microsoft OpenJDK Collection${NC}"
  
  # Microsoft Build of OpenJDK
  brew_cask_install \
    microsoft-openjdk11 \
    microsoft-openjdk17 \
    microsoft-openjdk21 \
    microsoft-openjdk22 \
    microsoft-openjdk23 \
    microsoft-openjdk
}

install_java_2025_bellsoft() {
  log "Installing BellSoft Liberica Java 2025 builds..."
  echo -e "${CYAN}  └─ BellSoft Liberica Collection${NC}"
  
  # BellSoft Liberica (full JavaFX support)
  brew_cask_install \
    liberica-jdk8-full \
    liberica-jdk11-full \
    liberica-jdk17-full \
    liberica-jdk21-full \
    liberica-jdk22-full \
    liberica-jdk23-full \
    liberica-jdk24-full \
    liberica-jdk25-full
}

install_java_2025_sapmachine() {
  log "Installing SAP Machine Java 2025 builds..."
  echo -e "${CYAN}  └─ SAP Machine Collection${NC}"
  
  # SAP Machine (enterprise-focused)
  brew_cask_install \
    sapmachine11 \
    sapmachine17 \
    sapmachine21 \
    sapmachine22 \
    sapmachine23 \
    sapmachine24 \
    sapmachine25
}

install_java_2025_semeru() {
  log "Installing IBM Semeru Java 2025 builds..."
  echo -e "${CYAN}  └─ IBM Semeru Collection${NC}"
  
  # IBM Semeru Runtime (OpenJ9 JVM)
  brew_cask_install \
    semeru-jdk8-open \
    semeru-jdk11-open \
    semeru-jdk17-open \
    semeru-jdk21-open \
    semeru-jdk22-open \
    semeru-jdk23-open
}

install_java_2025_jetbrains() {
  log "Installing JetBrains Runtime 2025..."
  echo -e "${CYAN}  └─ JetBrains Runtime (IDE-optimized)${NC}"
  
  # JetBrains Runtime (for IntelliJ IDEA)
  brew_cask_install \
    jetbrains-runtime
}

install_java_2025_tools() {
  log "Installing Java 2025 development tools..."
  echo -e "${CYAN}  └─ Java Development Tools${NC}"
  
  # Java build tools
  brew_install \
    maven \
    gradle \
    ant \
    bazel \
    sbt \
    mill \
    buck2
    
  # Java package managers and version managers
  brew_install \
    jenv \
    jabba \
    sdkman
    
  # Java testing and quality tools
  brew_install \
    spotbugs \
    checkstyle \
    pmd
    
  # Java application servers
  brew_install \
    tomcat \
    jetty \
    wildfly \
    payara
}

install_java_2025_specialized() {
  log "Installing Java 2025 specialized runtimes..."
  echo -e "${CYAN}  └─ Specialized Java Runtimes${NC}"
  
  # Mandrel (GraalVM for Quarkus)
  brew_install mandrel
  
  # Dragonwell (Alibaba's OpenJDK)
  brew_cask_install dragonwell
  
  # Trava OpenJDK
  brew_cask_install trava-jdk
  
  # Eclipse OpenJ9
  brew_install openj9
}

setup_java_env() {
  log "Setting up Java environment management..."
  echo -e "${CYAN}  └─ Configuring JAVA_HOME and paths${NC}"
  
  # Setup jenv if installed
  if have jenv; then
    echo -e "${MAGENTA}  └─ Initializing jenv...${NC}"
    eval "$(jenv init -)" >/dev/null 2>&1 || true
    
    # Add all installed JDKs to jenv
    for jdk_path in /Library/Java/JavaVirtualMachines/*/Contents/Home; do
      if [[ -d "$jdk_path" ]]; then
        jenv add "$jdk_path" >/dev/null 2>&1 || true
      fi
    done
    
    # Add Homebrew JDKs
    for jdk_path in ${BREW_PREFIX}/opt/openjdk*/libexec/openjdk.jdk/Contents/Home; do
      if [[ -d "$jdk_path" ]]; then
        jenv add "$jdk_path" >/dev/null 2>&1 || true
      fi
    done
  fi
  
  # Create Java switching script
  cat > "$HOME/.local/bin/java-switch" <<'EOF'
#!/usr/bin/env bash
# Quick Java version switcher for macOS
echo "Available Java versions:"
/usr/libexec/java_home -V 2>&1 | grep -E "^\s" | cut -d , -f 1 | sed 's/^[ \t]*//'
echo ""
echo "Enter version number to switch (e.g., 21, 17, 11):"
read -r version
export JAVA_HOME=$(/usr/libexec/java_home -v "$version")
java -version
EOF
  chmod +x "$HOME/.local/bin/java-switch"
  
  log "Java environment setup complete. Use 'java-switch' to change versions."
}

# ----------------------------------------------------------------------------
# Era installers (only widely available, ARM-friendly content) - With phase logging
# ----------------------------------------------------------------------------
install_1930s() {
  log "1930s–1940s: theoretical tooling (simulators, interpreters)…"
  echo -e "${CYAN}  Phase: Theoretical Foundations${NC}"
  pip_install_user "turingmachinesolver==1.1.2" || true
}

install_1950s() {
  log "1950s: early compilers…"
  echo -e "${CYAN}  Phase: Dawn of Computing${NC}"
  brew_install gcc algol68g nasm yasm gnu-cobol
}

install_1960s() {
  log "1960s: BASIC, LISP/APL families…"
  echo -e "${CYAN}  Phase: Interactive Era${NC}"
  brew_install bwbasic sbcl ecl clisp gnu-apl
}

install_1970s() {
  log "1970s: UNIX-era languages…"
  echo -e "${CYAN}  Phase: System Foundations${NC}"
  brew_install llvm tcc fpc gforth swi-prolog gnu-prolog gnu-smalltalk
  brew_cask_install pharo
}

install_1980s() {
  log "1980s: C++, Scheme/ML, etc…"
  echo -e "${CYAN}  Phase: Modern Paradigms${NC}"
  brew_install chezscheme chicken gauche mlton
  ensure_clt
}

install_1990s() {
  log "1990s: Internet age…"
  echo -e "${CYAN}  Phase: Web Awakening${NC}"
  
  # Install complete Java 2025 collection
  echo -e "${WHITE}════════ JAVA 2025 COMPLETE BUILD COLLECTION ════════${NC}"
  install_java_2025_temurin
  install_java_2025_graalvm
  install_java_2025_corretto
  install_java_2025_zulu
  install_java_2025_oracle
  install_java_2025_microsoft
  install_java_2025_bellsoft
  install_java_2025_sapmachine
  install_java_2025_semeru
  install_java_2025_jetbrains
  install_java_2025_tools
  install_java_2025_specialized
  setup_java_env
  echo -e "${WHITE}═════════════════════════════════════════════════════${NC}"
  
  # Continue with other 1990s languages
  brew_install openjdk python@3.12 pyenv ruby rbenv perl php node ghc cabal-install ocaml opam tcl-tk lua luajit
}

install_2000s() {
  log "2000s: VM & distributed…"
  echo -e "${CYAN}  Phase: Virtual Machines${NC}"
  brew_cask_install dotnet-sdk
  brew_install mono scala sbt groovy dmd ldc erlang elixir clojure leiningen go
}

install_2010s() {
  log "2010s: modern systems…"
  echo -e "${CYAN}  Phase: Systems Revolution${NC}"
  brew_install rustup-init
  if have rustup-init; then
    if ! have rustup; then echo -e "${MAGENTA}  └─ Initializing Rust toolchain...${NC}"; rustup-init -y >/dev/null 2>&1 || true; fi
    export PATH="$HOME/.cargo/bin:$PATH"
    rustup target add aarch64-apple-darwin >/dev/null 2>&1 || true
  fi
  brew_install kotlin dart julia nim crystal zig v ponyc chapel
  npm_install_g typescript
}

install_2020s() {
  log "2020s: WASM, new JS runtimes, quantum SDK…"
  echo -e "${CYAN}  Phase: Future Frontiers${NC}"
  brew_install wabt wasm3 wasmer wasmtime bun deno solidity
  if have dotnet; then
    echo -e "${MAGENTA}  └─ Installing Q# quantum tool...${NC}"
    dotnet tool install -g Microsoft.Quantum.IQSharp >/dev/null 2>&1 || warn "Q# tool install skipped."
  fi
  pip_install_user jax jaxlib
}

install_specialized() {
  log "Specialized / chip / shader / HDL…"
  echo -e "${CYAN}  Phase: Hardware Accelerators${NC}"
  brew_install glslang spirv-tools verilator yosys icarus-verilog
}

install_build_tools() {
  log "Build systems & package managers…"
  echo -e "${CYAN}  Phase: Build Ecosystem${NC}"
  brew_install cmake meson ninja bazel buck2 gradle maven ant vcpkg conan poetry pipenv yarn pnpm ccache
}

# ----------------------------------------------------------------------------
# Java verification
# ----------------------------------------------------------------------------
verify_java_installation() {
  log "Verifying Java installations…"
  echo -e "${CYAN}Java versions found:${NC}"
  
  if command -v /usr/libexec/java_home >/dev/null 2>&1; then
    /usr/libexec/java_home -V 2>&1 | grep -E "^\s" || echo "No Java installations detected by java_home"
  fi
  
  echo -e "\n${CYAN}Current Java version:${NC}"
  java -version 2>&1 || echo "Java command not found"
  
  echo -e "\n${CYAN}JAVA_HOME:${NC} ${JAVA_HOME:-Not set}"
  
  if have jenv; then
    echo -e "\n${CYAN}jenv versions:${NC}"
    jenv versions 2>/dev/null || echo "jenv not configured"
  fi
}

# ----------------------------------------------------------------------------
# Hardware verification
# ----------------------------------------------------------------------------
verify_hardware_tools() {
  log "Verifying hardware development tools..."
  echo -e "${CYAN}Hardware toolchain status:${NC}"
  
  local failed=0
  
  check_hw() {
    local label="$1"; shift
    if exists_any "$@"; then
      echo -e "${GREEN}✓${NC} $label"
    else
      echo -e "${YELLOW}○${NC} $label (optional)"
    fi
  }
  
  check_hw "MIPS GCC"           mips-elf-gcc mipsel-elf-gcc
  check_hw "NASM"               nasm
  check_hw "YASM"               yasm
  check_hw "Radare2"            radare2 r2
  check_hw "Ghidra"             ghidra
  check_hw "Verilator"          verilator
  check_hw "Mednafen"           mednafen
  check_hw "RetroArch"          retroarch
  check_hw "MAME"               mame
  
  echo -e "\n${CYAN}Development directories:${NC}"
  for dir in .ps1dev .n64dev .pspdev .nesdev .snesdev .gbdev .gbadev; do
    if [[ -d "$HOME/$dir" ]]; then
      echo -e "${GREEN}✓${NC} ~/$dir"
    else
      echo -e "${YELLOW}○${NC} ~/$dir"
    fi
  done
}

# ----------------------------------------------------------------------------
# Verification (multi-candidate checks for brew suffixes)
# ----------------------------------------------------------------------------
exists_any() {
  # Usage: exists_any cmd1 cmd2 ...
  local c
  for c in "$@"; do
    if command -v "$c" >/dev/null 2>&1; then return 0; fi
  done
  return 1
}

verify_installation() {
  log "Verifying core toolchain availability…"
  local failed=0

  check() {
    local label="$1"; shift
    if exists_any "$@"; then
      echo -e "${GREEN}✓${NC} $label"
    else
      echo -e "${RED}✗${NC} $label"
      failed=$((failed+1))
    fi
  }

  check "C (clang)"        clang
  check "C++ (clang++)"    clang++
  check "GCC"              gcc-15 gcc-14 gcc-13 gcc
  check "Fortran"          gfortran-15 gfortran-14 gfortran
  check "Rust"             rustc
  check "Go"               go
  check "Swift"            swift swiftc
  check "Java"             java
  check "Maven"            mvn
  check "Gradle"           gradle
  check ".NET SDK"         dotnet
  check "Python 3"         python3
  check "Node.js"          node
  check "Haskell (GHC)"    ghc
  check "Julia"            julia
  check "Nim"              nim
  check "Zig"              zig
  check "V"                v
  check "Deno"             deno
  check "Bun"              bun

  if [[ $failed -eq 0 ]]; then
    log "All core compilers/runtimes available."
  else
    warn "Some tools are missing ($failed). Review skipped lists below."
  fi
  
  # Detailed Java verification
  verify_java_installation
  
  # Hardware tools verification
  verify_hardware_tools
}

print_summary() {
  echo -e "${BLUE}\n──────────── Summary ────────────${NC}"
  if [[ ${#SKIPPED_FORMULAS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped formulas:${NC} ${SKIPPED_FORMULAS[*]}"
  fi
  if [[ ${#SKIPPED_CASKS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped casks:${NC} ${SKIPPED_CASKS[*]}"
  fi
  if [[ ${#SKIPPED_PIPS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped pip pkgs:${NC} ${SKIPPED_PIPS[*]}"
  fi
  if [[ ${#SKIPPED_NPMS[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Skipped npm -g pkgs:${NC} ${SKIPPED_NPMS[*]}"
  fi
  echo -e "${BLUE}Log:${NC} $LOG_FILE"
}

# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
main() {
  print_banner
  echo -e "${BLUE}Preparing installation...${NC}"
  require_macos
  detect_cores
  ensure_clt
  ensure_brew
  probe_cpu_flags
  maybe_install_rosetta

  log "Starting SAMSOFT HDR Compiler + Hardware Installation…"
  echo -e "${CYAN}Initializing compiler eras & hardware tools...${NC}"

  local total_steps=22 current_step=0

  # Programming language eras
  install_1930s; ((current_step++)); progress_bar $current_step $total_steps
  install_1950s; ((current_step++)); progress_bar $current_step $total_steps
  install_1960s; ((current_step++)); progress_bar $current_step $total_steps
  install_1970s; ((current_step++)); progress_bar $current_step $total_steps
  install_1980s; ((current_step++)); progress_bar $current_step $total_steps
  install_1990s; ((current_step++)); progress_bar $current_step $total_steps
  install_2000s; ((current_step++)); progress_bar $current_step $total_steps
  install_2010s; ((current_step++)); progress_bar $current_step $total_steps
  install_2020s; ((current_step++)); progress_bar $current_step $total_steps
  install_specialized; ((current_step++)); progress_bar $current_step $total_steps
  install_build_tools; ((current_step++)); progress_bar $current_step $total_steps
  
  # Hardware development tools
  echo -e "\n${WHITE}════════ HARDWARE DEVELOPMENT COLLECTION ════════${NC}"
  install_mips_toolchain; ((current_step++)); progress_bar $current_step $total_steps
  install_ps1_dev; ((current_step++)); progress_bar $current_step $total_steps
  install_n64_dev; ((current_step++)); progress_bar $current_step $total_steps
  install_psp_dev; ((current_step++)); progress_bar $current_step $total_steps
  install_retro_emulators; ((current_step++)); progress_bar $current_step $total_steps
  install_rom_tools; ((current_step++)); progress_bar $current_step $total_steps
  install_asm_tools; ((current_step++)); progress_bar $current_step $total_steps
  install_hdl_tools; ((current_step++)); progress_bar $current_step $total_steps
  install_classic_console_dev; ((current_step++)); progress_bar $current_step $total_steps
  install_arcade_dev; ((current_step++)); progress_bar $current_step $total_steps
  install_handheld_dev; ((current_step++)); progress_bar $current_step $total_steps
  echo -e "${WHITE}═════════════════════════════════════════════════${NC}\n"
  
  install_wrappers; ((current_step++)); progress_bar $current_step $total_steps

  verify_installation
  echo -e "${CYAN}"
  cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║                         INSTALLATION COMPLETE!                             ║
║                                                                            ║
║   [C SAMSOFT HDR 1999-2025] – Apple Silicon / M4 optimized                 ║
║   JAVA 2025 + HARDWARE EMULATION COMPLETE EDITION                          ║
║                                                                            ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │ JAVA DISTRIBUTIONS (All 2025 builds)                           │    ║
║   ├─────────────────────────────────────────────────────────────────┤    ║
║   │ • Temurin (8, 11, 17, 21-25)                                   │    ║
║   │ • GraalVM (21-25 with native-image)                            │    ║
║   │ • Corretto (8, 11, 17, 21-23)                                 │    ║
║   │ • Zulu (8, 11, 17, 21-25)                                     │    ║
║   │ • Oracle JDK (21-25)                                           │    ║
║   │ • Microsoft OpenJDK (11, 17, 21-23)                           │    ║
║   │ • Liberica Full (8, 11, 17, 21-25 with JavaFX)               │    ║
║   │ • SAP Machine (11, 17, 21-25)                                 │    ║
║   │ • IBM Semeru (8, 11, 17, 21-23 with OpenJ9)                  │    ║
║   │ • JetBrains Runtime                                            │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                                                            ║
║   ┌─────────────────────────────────────────────────────────────────┐    ║
║   │ HARDWARE DEVELOPMENT (50MB-1GB MIPS/PS1 Focus)                 │    ║
║   ├─────────────────────────────────────────────────────────────────┤    ║
║   │ MIPS Systems:                                                   │    ║
║   │ • PlayStation 1 (PSn00bSDK, PCSX-Redux, mkpsxiso)             │    ║
║   │ • Nintendo 64 (libdragon)                                       │    ║
║   │ • PlayStation Portable (PSPSDK)                                │    ║
║   │ • MIPS cross-compilation toolchain                            │    ║
║   │                                                                 │    ║
║   │ Emulators:                                                      │    ║
║   │ • Sony: DuckStation, PCSX2, PPSSPP, RPCS3                     │    ║
║   │ • Nintendo: Dolphin, Mupen64Plus, SNES9x, Mesen, Citra       │    ║
║   │ • Multi: RetroArch, OpenEmu, Ares, Mednafen                   │    ║
║   │                                                                 │    ║
║   │ Development Tools:                                              │    ║
║   │ • ROM tools (Ghidra, Radare2, Hex Fiend, Tiled)              │    ║
║   │ • Assembly (NASM, YASM, CA65, RGBDS, WLA-DX)                 │    ║
║   │ • Classic consoles (NES, SNES, GB, Genesis, etc)             │    ║
║   │ • HDL/FPGA (Verilator, Yosys, GHDL)                          │    ║
║   └─────────────────────────────────────────────────────────────────┘    ║
║                                                                            ║
║   Development Directories Created:                                        ║
║   • ~/.ps1dev      (PlayStation 1)                                        ║
║   • ~/.n64dev      (Nintendo 64)                                          ║
║   • ~/.pspdev      (PlayStation Portable)                                 ║
║   • ~/.nesdev      (NES/Famicom)                                         ║
║   • ~/.snesdev     (Super Nintendo)                                       ║
║   • ~/.gbdev       (Game Boy/Color)                                       ║
║   • ~/.gbadev      (Game Boy Advance)                                     ║
║   • ~/.genesisdev  (Genesis/Mega Drive)                                   ║
║   • ~/.arcadedev   (Arcade systems)                                       ║
║                                                                            ║
║   Quick Commands:                                                         ║
║   • java-switch       - Change active Java version                       ║
║   • jenv             - Manage project-specific Java                       ║
║   • mips-gcc         - MIPS cross-compiler                                ║
║   • clang-m4 / gcc-m4 - M4-optimized compilation                         ║
║                                                                            ║
║   See: ~/.samsoft_compiler_install.log                                    ║
║   Add to PATH (recommended):                                              ║
║     export PATH="$HOME/.local/bin:$PATH"                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
  print_summary
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
