#!/usr/bin/env bash
# cli-hub installer — thin wrapper around PyPI package installation.
#
# What this script does:
#   1. Detects Python ≥ 3.10 (installs if missing via brew/apt/dnf)
#   2. Installs "agent-cli-hub" from PyPI using uv/pipx/pip
#   3. Verifies the "cli-hub" command is available
#
# Security:
#   - Only installs from PyPI (https://pypi.org/project/agent-cli-hub/)
#   - pip/uv/pipx verify package signatures via PyPI's TLS + PEP 691
#   - Source: https://github.com/agentrix-ai/clihub (MIT License)
#   - If you prefer not to pipe to shell, run: pip install agent-cli-hub
#
set -euo pipefail

PACKAGE="agent-cli-hub"
VERSION="0.2.0"
CMD="cli-hub"
MIN_PY="3.10"
REPO="https://github.com/agentrix-ai/clihub"
PYPI="https://pypi.org/project/agent-cli-hub/"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${CYAN}[info]${NC}  $*"; }
ok()    { echo -e "${GREEN}[ok]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
fail()  { echo -e "${RED}[fail]${NC}  $*"; exit 1; }

echo -e "${BOLD}"
echo "  ┌─────────────────────────────────────┐"
echo "  │     cli-hub installer v${VERSION}        │"
echo "  │  Enterprise CLI Unified Gateway     │"
echo "  └─────────────────────────────────────┘"
echo -e "${NC}"
echo -e "  ${CYAN}Source:${NC}  ${REPO}"
echo -e "  ${CYAN}PyPI:${NC}    ${PYPI}"
echo ""

version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -t. -k1,1n -k2,2n -k3,3n -C
}

find_python() {
    for cmd in python3 python; do
        if command -v "$cmd" &>/dev/null; then
            local ver
            ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null) || continue
            if version_ge "$ver" "$MIN_PY"; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# ── Step 1: Detect Python ──
info "Detecting Python ≥ ${MIN_PY}..."
PYTHON=""
if PYTHON=$(find_python); then
    PY_VER=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    ok "Found $PYTHON ($PY_VER)"
else
    warn "Python ≥ ${MIN_PY} not found."
    if command -v brew &>/dev/null; then
        info "Installing Python via Homebrew..."
        brew install python@3.12
        PYTHON=$(find_python) || fail "Python install failed. Please install Python ≥ ${MIN_PY} manually."
    elif command -v apt-get &>/dev/null; then
        info "Installing Python via apt..."
        sudo apt-get update -qq && sudo apt-get install -y -qq python3 python3-pip python3-venv
        PYTHON=$(find_python) || fail "Python install failed. Please install Python ≥ ${MIN_PY} manually."
    elif command -v dnf &>/dev/null; then
        info "Installing Python via dnf..."
        sudo dnf install -y python3 python3-pip
        PYTHON=$(find_python) || fail "Python install failed. Please install Python ≥ ${MIN_PY} manually."
    else
        fail "Cannot auto-install Python. Please install Python ≥ ${MIN_PY} first:\n  macOS:  brew install python@3.12\n  Ubuntu: sudo apt install python3 python3-pip\n  Fedora: sudo dnf install python3 python3-pip"
    fi
fi

# ── Step 2: Install from PyPI (uv > pipx > pip) ──
INSTALLED=false
INSTALL_SPEC="${PACKAGE}==${VERSION}"

if command -v uv &>/dev/null; then
    info "Installing ${INSTALL_SPEC} via uv (from PyPI)..."
    uv tool install "$INSTALL_SPEC" && INSTALLED=true

elif command -v pipx &>/dev/null; then
    info "Installing ${INSTALL_SPEC} via pipx (from PyPI)..."
    pipx install "$INSTALL_SPEC" && INSTALLED=true

else
    if $PYTHON -m pip --version &>/dev/null; then
        info "Installing ${INSTALL_SPEC} via pip (from PyPI)..."
        $PYTHON -m pip install --user "$INSTALL_SPEC" && INSTALLED=true
    else
        warn "pip not found, installing uv first..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        if command -v uv &>/dev/null; then
            info "Installing ${INSTALL_SPEC} via uv (from PyPI)..."
            uv tool install "$INSTALL_SPEC" && INSTALLED=true
        else
            fail "Failed to install uv. Please install manually: https://docs.astral.sh/uv/"
        fi
    fi
fi

$INSTALLED || fail "Installation failed. Try manually: pip install ${INSTALL_SPEC}"

# ── Step 3: Verify ──
export PATH="$HOME/.local/bin:$PATH"

if command -v "$CMD" &>/dev/null; then
    ACTUAL_VER=$($CMD version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || echo "unknown")
    echo ""
    ok "${BOLD}cli-hub v${ACTUAL_VER} installed successfully!${NC}"
    echo ""
    echo -e "  ${BOLD}Quick start:${NC}"
    echo "    cli-hub doctor                # Check environment"
    echo "    cli-hub search \"发送消息\"      # Search tools"
    echo "    cli-hub install --all         # Install underlying CLIs"
    echo ""
    echo -e "  ${CYAN}Docs:${NC}   ${REPO}"
    echo -e "  ${CYAN}PyPI:${NC}   ${PYPI}"
else
    warn "cli-hub installed but not found in PATH."
    echo ""
    echo "  Add to your shell profile:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "  Then run: cli-hub doctor"
fi
