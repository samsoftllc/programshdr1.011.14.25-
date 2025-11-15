#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# cats_ultimate_compiler_agi_1930_2025.sh
# Historical Compiler Installer (1930 → 2025)
# Clean rebuild as requested — shell ONLY, no GUI, no Python, no extras.
# -----------------------------------------------------------------------------
set -euo pipefail

log() { printf "
[INFO] %s
" "$*"; }
warn() { printf "
[WARN] %s
" "$*" >&2; }
err() { printf "
[ERROR] %s
" "$*" >&2; }

# ----- REQUIREMENTS -----------------------------------------------------------
# macOS + Homebrew
if [[ "$(uname -s)" != "Darwin" ]]; then err "macOS only"; exit 1; fi

ensure_homebrew() {
  if command -v /opt/homebrew/bin/brew >/dev/null 2>&1; then
    BREW=/opt/homebrew/bin/brew
  elif command -v brew >/dev/null 2>&1; then
    BREW=$(command -v brew)
  else
    log "Installing Homebrew..."
    NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    BREW=/opt/homebrew/bin/brew
  fi
  eval "$($BREW shellenv)"
}

brew_install() {
  local pkg="$1"
  if $BREW list --versions "$pkg" >/dev/null 2>&1; then
    log "Already installed: $pkg"
  else
    log "brew install $pkg"; $BREW install "$pkg"
  fi
}

brew_install_any() {
  for n in "$@"; do
    if $BREW info "$n" >/dev/null 2>&1; then brew_install "$n"; return 0; fi
  done
  warn "none found: $*"
}

# -----------------------------------------------------------------------------
# HISTORICAL COMPILER TIMELINE (1930 → 2025)
# -----------------------------------------------------------------------------
install_1930_2025() {
  log "Installing historical + modern compilers (1930–2025)..."

  # 1930s–1940s (proto-languages → mathematical / assembler simulation)
  brew_install maxima        # symbolic mathematics
  brew_install binutils      # assembler roots

  # 1950s
  brew_install gfortran      # FORTRAN (1957)
  brew_install_any algol68g algol68
  brew_install sbcl
  brew_install clisp

  # 1960s
  brew_install freebasic     # BASIC (1964)
  brew_install pcc           # pre-ANSI C roots
  brew_install guile
  brew_install chezscheme
  brew_install chicken
  brew_install bc

  # 1970s
  brew_install fpc
  brew_install gnu-smalltalk
  brew_install swi-prolog
  brew_install gforth
  brew_install gawk

  # 1980s
  brew_install ocaml
  brew_install smlnj
  brew_install polyml
  brew_install mlton
  brew_install io

  # 1990s
  brew_install ghc
  brew_install cabal-install
  brew_install haskell-stack
  brew_install cc65
  brew_install llvm
  brew_install erlang
  brew_install elixir

  # 2000s
  brew_install julia
  brew_install nim
  brew_install crystal
  brew_install go
  brew_install rustup-init
  yes 1 | rustup-init -y --no-modify-path --default-toolchain stable || true
  brew_install dart-sdk
  brew_install deno
  brew_install ldc
  brew_install dmd

  # 2010s
  brew_install wasm-pack
  brew_install binaryen
  brew_install wabt
  brew_install zig
  brew_install_any vlang v

  # 2020–2025
  brew_install nuitka
  brew_install wasmer
  brew_install wasmtime

  log "All compilers (1930–2025) installed."
}

# -----------------------------------------------------------------------------
main() {
  log "=== Historical Compiler Installer 1930–2025 ==="
  ensure_homebrew
  install_1930_2025
  log "Done."
}

main "$@"
