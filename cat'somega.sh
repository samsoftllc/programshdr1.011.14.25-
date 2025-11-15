#!/usr/bin/env bash
# ============================================================================
# [C SAMSOFT HDR 1999-2025] ULTIMATE COMPILER COLLECTION (macOS Apple Silicon)
# M4 PRO-OPTIMIZED, BREW-FIRST, FAULT-TOLERANT
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
  if [[ "$major_version" -lt 26 ]]; then
    error "This installer requires macOS Tahoe (26) or later."
    exit 1
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
  brew tap homebrew/cask-versions >/dev/null 2>&1 || true
  brew_cask_install temurin8 temurin11 temurin17 temurin21
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

  log "Starting SAMSOFT HDR Compiler Installation…"
  echo -e "${CYAN}Initializing compiler eras...${NC}"

  local total_steps=11 current_step=0

  # Progress updates after each major install
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
  install_wrappers; ((current_step++)); progress_bar $current_step $total_steps

  verify_installation
  echo -e "${CYAN}"
  cat << 'EOF'
╔════════════════════════════════════════════════════════════════════════════╗
║                         INSTALLATION COMPLETE!                             ║
║                                                                            ║
║   [C SAMSOFT HDR 1999-2025] – Apple Silicon / M4 optimized                 ║
║   See: ~/.samsoft_compiler_install.log                                     ║
║   Add to PATH (recommended):                                                ║
║     export PATH="$HOME/.local/bin:$PATH"                                   ║
╚════════════════════════════════════════════════════════════════════════════╝
EOF
  echo -e "${NC}"
  print_summary
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  main "$@"
fi
