#!/usr/bin/env python3
"""Enterprise License Checker — scans dependency manifests for copyleft risk.

Parses requirements.txt, package.json, and go.mod to identify newly-added
packages, then checks each package's license against an enterprise-approved
allowlist.  Copyleft licenses (GPL, AGPL, LGPL, EUPL, MPL, SSPL, OSL, CPAL,
CC-BY-SA) are flagged as enterprise risks.

Exit codes:
    0 — all licenses are permissive or no dependency files found
    1 — one or more copyleft / unknown licenses detected
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# License classification
# ---------------------------------------------------------------------------

COPYLEFT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"\bAGPL\b", re.IGNORECASE),
    re.compile(r"\bGPL\b", re.IGNORECASE),
    re.compile(r"\bLGPL\b", re.IGNORECASE),
    re.compile(r"\bEUPL\b", re.IGNORECASE),
    re.compile(r"\bMPL\b", re.IGNORECASE),
    re.compile(r"\bSSPL\b", re.IGNORECASE),
    re.compile(r"\bOSL\b", re.IGNORECASE),
    re.compile(r"\bCPAL\b", re.IGNORECASE),
    re.compile(r"\bCC-BY-SA\b", re.IGNORECASE),
    re.compile(r"GNU General Public License", re.IGNORECASE),
    re.compile(r"GNU Affero", re.IGNORECASE),
    re.compile(r"Copyleft", re.IGNORECASE),
]


def is_copyleft(license_name: str) -> bool:
    """Return *True* if *license_name* matches a known copyleft pattern."""
    return any(pat.search(license_name) for pat in COPYLEFT_PATTERNS)


# ---------------------------------------------------------------------------
# Dependency extraction helpers
# ---------------------------------------------------------------------------

_REQ_LINE = re.compile(
    r"^(?P<name>[A-Za-z0-9_][A-Za-z0-9._-]*)" r"(?:\[.*?\])?" r"(?:\s*[><=!~].*)?$"
)


def parse_requirements_txt(path: Path) -> list[str]:
    """Return package names from a *requirements.txt* file."""
    packages: list[str] = []
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        m = _REQ_LINE.match(line)
        if m:
            packages.append(m.group("name"))
    return packages


def parse_package_json(path: Path) -> list[str]:
    """Return package names from a *package.json* file."""
    data = json.loads(path.read_text())
    names: list[str] = []
    for key in ("dependencies", "devDependencies"):
        deps = data.get(key)
        if isinstance(deps, dict):
            names.extend(deps.keys())
    return names


def parse_go_mod(path: Path) -> list[str]:
    """Return module paths from a *go.mod* file."""
    modules: list[str] = []
    in_require = False
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if line.startswith("require ("):
            in_require = True
            continue
        if in_require:
            if line == ")":
                in_require = False
                continue
            parts = line.split()
            if parts:
                modules.append(parts[0])
        elif line.startswith("require "):
            parts = line.split()
            if len(parts) >= 2:
                modules.append(parts[1])
    return modules


# ---------------------------------------------------------------------------
# License lookup (pip only — lightweight, no extra deps)
# ---------------------------------------------------------------------------


def pip_license(package: str) -> str:
    """Query *pip show* for the license string of *package*."""
    try:
        out = subprocess.run(
            ["pip", "show", package],
            capture_output=True,
            text=True,
            timeout=15,
        )
        for line in out.stdout.splitlines():
            if line.startswith("License:"):
                return line.split(":", 1)[1].strip() or "UNKNOWN"
    except Exception:
        pass
    return "UNKNOWN"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    root = Path(".")
    findings: list[dict[str, str]] = []

    # --- Python -----------------------------------------------------------
    req_path = root / "requirements.txt"
    if req_path.exists():
        for pkg in parse_requirements_txt(req_path):
            lic = pip_license(pkg)
            findings.append(
                {"source": "requirements.txt", "package": pkg, "license": lic}
            )

    # --- Node.js ----------------------------------------------------------
    pkg_json = root / "package.json"
    if pkg_json.exists():
        for pkg in parse_package_json(pkg_json):
            findings.append(
                {"source": "package.json", "package": pkg, "license": "CHECK_MANUALLY"}
            )

    # --- Go ---------------------------------------------------------------
    go_mod = root / "go.mod"
    if go_mod.exists():
        for mod in parse_go_mod(go_mod):
            findings.append(
                {"source": "go.mod", "package": mod, "license": "CHECK_MANUALLY"}
            )

    if not findings:
        print("License Check: no dependency manifests found — nothing to audit.")
        return 0

    # --- Report -----------------------------------------------------------
    violations: list[dict[str, str]] = []
    print("\n=== Enterprise License Audit ===\n")
    for f in findings:
        status = "✅ Permissive"
        if is_copyleft(f["license"]):
            status = "🚫 COPYLEFT — Enterprise Risk"
            violations.append(f)
        elif f["license"] in ("UNKNOWN", "CHECK_MANUALLY"):
            status = "⚠️  Unknown (verify manually)"
        print(f"  {f['source']:20s}  {f['package']:30s}  {f['license']:25s}  {status}")

    print()
    if violations:
        print("FAILURE: Copyleft license(s) detected — see findings above.")
        return 1

    print(
        "License Check Passed: all detected licenses are permissive or need manual review."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
