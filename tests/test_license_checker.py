"""Tests for the enterprise license checker."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from scripts.governance.license_checker import (
    is_copyleft,
    parse_go_mod,
    parse_package_json,
    parse_requirements_txt,
)

# --------------------------------------------------------------------------- #
# is_copyleft
# --------------------------------------------------------------------------- #


class TestIsCopyleft:
    def test_gpl_detected(self):
        assert is_copyleft("GPL-3.0") is True

    def test_agpl_detected(self):
        assert is_copyleft("AGPL-3.0-only") is True

    def test_lgpl_detected(self):
        assert is_copyleft("LGPL-2.1") is True

    def test_gnu_general(self):
        assert is_copyleft("GNU General Public License v3") is True

    def test_mit_is_permissive(self):
        assert is_copyleft("MIT") is False

    def test_apache_is_permissive(self):
        assert is_copyleft("Apache-2.0") is False

    def test_bsd_is_permissive(self):
        assert is_copyleft("BSD-3-Clause") is False

    def test_unknown_is_not_copyleft(self):
        assert is_copyleft("UNKNOWN") is False


# --------------------------------------------------------------------------- #
# parse_requirements_txt
# --------------------------------------------------------------------------- #


class TestParseRequirementsTxt:
    def test_basic(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("flask==2.3.0\nrequests>=2.28\n")
        assert parse_requirements_txt(req) == ["flask", "requests"]

    def test_comments_and_blanks(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("# comment\n\nflask\n  \n")
        assert parse_requirements_txt(req) == ["flask"]

    def test_extras(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("uvicorn[standard]>=0.20\n")
        assert parse_requirements_txt(req) == ["uvicorn"]

    def test_flags_skipped(self, tmp_path: Path):
        req = tmp_path / "requirements.txt"
        req.write_text("-r base.txt\nflask\n")
        assert parse_requirements_txt(req) == ["flask"]


# --------------------------------------------------------------------------- #
# parse_package_json
# --------------------------------------------------------------------------- #


class TestParsePackageJson:
    def test_dependencies_and_dev(self, tmp_path: Path):
        pkg = tmp_path / "package.json"
        pkg.write_text(
            json.dumps(
                {
                    "name": "app",
                    "dependencies": {"express": "^4.18.0", "cors": "^2.8.5"},
                    "devDependencies": {"jest": "^29.0.0"},
                }
            )
        )
        result = parse_package_json(pkg)
        assert "express" in result
        assert "cors" in result
        assert "jest" in result

    def test_no_deps(self, tmp_path: Path):
        pkg = tmp_path / "package.json"
        pkg.write_text(json.dumps({"name": "empty"}))
        assert parse_package_json(pkg) == []


# --------------------------------------------------------------------------- #
# parse_go_mod
# --------------------------------------------------------------------------- #


class TestParseGoMod:
    def test_multi_line_require(self, tmp_path: Path):
        mod = tmp_path / "go.mod"
        mod.write_text(textwrap.dedent("""\
                module example.com/myapp

                go 1.21

                require (
                    github.com/gin-gonic/gin v1.9.1
                    golang.org/x/crypto v0.14.0
                )
                """))
        result = parse_go_mod(mod)
        assert "github.com/gin-gonic/gin" in result
        assert "golang.org/x/crypto" in result

    def test_single_line_require(self, tmp_path: Path):
        mod = tmp_path / "go.mod"
        mod.write_text(textwrap.dedent("""\
                module example.com/myapp

                go 1.21

                require github.com/stretchr/testify v1.8.4
                """))
        result = parse_go_mod(mod)
        assert result == ["github.com/stretchr/testify"]

    def test_empty_mod(self, tmp_path: Path):
        mod = tmp_path / "go.mod"
        mod.write_text("module example.com/myapp\n\ngo 1.21\n")
        assert parse_go_mod(mod) == []
