"""Unit tests for .reg file parser."""

import tempfile
import unittest
from pathlib import Path

from putty_export.reg_parser import parse_reg_file


def _make_reg(content: str) -> Path:
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8")
    f.write(content)
    f.close()
    return Path(f.name)


class TestRegParser(unittest.TestCase):
    def tearDown(self) -> None:
        pass

    def test_parses_key_and_dword(self) -> None:
        reg = _make_reg(
            "Windows Registry Editor Version 5.00\n\n"
            "[\\Software\\SimonTatham\\PuTTY\\Sessions\\test]\n"
            '"PortNumber"=dword:00000016\n'
        )
        try:
            result = parse_reg_file(reg)
            self.assertIn("\\Software\\SimonTatham\\PuTTY\\Sessions\\test", result)
            self.assertEqual(result["\\Software\\SimonTatham\\PuTTY\\Sessions\\test"]["PortNumber"], 22)
        finally:
            reg.unlink()

    def test_parses_hex_string(self) -> None:
        # "ssh" in UTF-16LE
        reg = _make_reg(
            "Windows Registry Editor Version 5.00\n\n"
            "[\\Software\\SimonTatham\\PuTTY\\Sessions\\mysession]\n"
            '"Protocol"=hex(1):73,00,73,00,68,00,00,00\n'
            '"HostName"=hex(1):31,00,30,00,2e,00,30,00,2e,00,30,00,2e,00,31,00,00,00\n'
        )
        try:
            result = parse_reg_file(reg)
            sess = result["\\Software\\SimonTatham\\PuTTY\\Sessions\\mysession"]
            self.assertEqual(sess["Protocol"], "ssh")
            self.assertEqual(sess["HostName"], "10.0.0.1")
        finally:
            reg.unlink()

    def test_multiple_keys(self) -> None:
        reg = _make_reg(
            "Windows Registry Editor Version 5.00\n\n"
            "[\\Software\\SimonTatham\\PuTTY\\Sessions\\first]\n"
            '"HostName"=hex(1):61,00,00,00\n'
            "[\\Software\\SimonTatham\\PuTTY\\Sessions\\second]\n"
            '"HostName"=hex(1):62,00,00,00\n'
        )
        try:
            result = parse_reg_file(reg)
            self.assertEqual(len(result), 2)
            self.assertEqual(result["\\Software\\SimonTatham\\PuTTY\\Sessions\\first"]["HostName"], "a")
            self.assertEqual(result["\\Software\\SimonTatham\\PuTTY\\Sessions\\second"]["HostName"], "b")
        finally:
            reg.unlink()

    def test_ignores_non_matching_lines(self) -> None:
        reg = _make_reg(
            "Windows Registry Editor Version 5.00\n\n"
            "[\\Software\\SimonTatham\\PuTTY\\Sessions\\x]\n"
            "some junk\n"
            '"Valid"=dword:00000001\n'
        )
        try:
            result = parse_reg_file(reg)
            self.assertEqual(result["\\Software\\SimonTatham\\PuTTY\\Sessions\\x"]["Valid"], 1)
        finally:
            reg.unlink()
