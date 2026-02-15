"""Unit tests for decoders (hex UTF-16LE and dword)."""

import unittest

from putty_export.decoders import decode_dword, decode_hex_string


class TestDecodeHexString(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(decode_hex_string(""), "")
        self.assertEqual(decode_hex_string("   "), "")

    def test_null_only(self) -> None:
        # UTF-16LE null: 00,00
        self.assertEqual(decode_hex_string("00,00"), "")

    def test_simple_ascii(self) -> None:
        # "ssh" in UTF-16LE: 73,00,73,00,68,00,00,00
        self.assertEqual(decode_hex_string("73,00,73,00,68,00,00,00"), "ssh")

    def test_hostname(self) -> None:
        # "10.10.10.49" - 31,00=1 30,00=0 2e,00=. etc
        raw = "31,00,30,00,2e,00,31,00,30,00,2e,00,31,00,30,00,2e,00,34,00,39,00,00,00"
        self.assertEqual(decode_hex_string(raw), "10.10.10.49")

    def test_whitespace_between_bytes(self) -> None:
        self.assertEqual(decode_hex_string("73, 00, 68, 00, 00, 00"), "sh")

    def test_invalid_hex_returns_empty(self) -> None:
        self.assertEqual(decode_hex_string("zz,00"), "")


class TestDecodeDword(unittest.TestCase):
    def test_empty(self) -> None:
        self.assertEqual(decode_dword(""), 0)
        self.assertEqual(decode_dword("   "), 0)

    def test_port_22(self) -> None:
        self.assertEqual(decode_dword("00000016"), 22)

    def test_port_80(self) -> None:
        self.assertEqual(decode_dword("00000050"), 80)

    def test_lowercase_hex(self) -> None:
        self.assertEqual(decode_dword("00000010"), 16)

    def test_invalid_returns_zero(self) -> None:
        self.assertEqual(decode_dword("xyz"), 0)
        self.assertEqual(decode_dword("0000000g"), 0)
