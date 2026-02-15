"""Unit tests for session filter (SSH only, non-empty HostName)."""

import unittest

from putty_export.session_filter import filter_ssh_sessions


class TestSessionFilter(unittest.TestCase):
    def test_excludes_bare_sessions_key(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions": {"HostName": "x", "Protocol": "ssh"},
        }
        self.assertEqual(filter_ssh_sessions(keys), {})

    def test_includes_ssh_session_with_hostname(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions\\mysession": {
                "Protocol": "ssh",
                "HostName": "host.example.com",
            },
        }
        result = filter_ssh_sessions(keys)
        self.assertEqual(len(result), 1)
        self.assertIn("mysession", result)
        self.assertEqual(result["mysession"]["HostName"], "host.example.com")

    def test_excludes_non_ssh_protocol(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions\\telnet": {
                "Protocol": "telnet",
                "HostName": "host",
            },
        }
        self.assertEqual(filter_ssh_sessions(keys), {})

    def test_excludes_empty_hostname(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions\\empty": {
                "Protocol": "ssh",
                "HostName": "",
            },
        }
        self.assertEqual(filter_ssh_sessions(keys), {})

    def test_skips_default_settings_by_default(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions\\Default%20Settings": {
                "Protocol": "ssh",
                "HostName": "some",
            },
        }
        self.assertEqual(filter_ssh_sessions(keys), {})

    def test_includes_default_settings_when_asked(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions\\Default%20Settings": {
                "Protocol": "ssh",
                "HostName": "some",
            },
        }
        result = filter_ssh_sessions(keys, skip_default_settings=False)
        self.assertEqual(len(result), 1)
        self.assertIn("Default Settings", result)

    def test_session_name_url_decoded(self) -> None:
        keys = {
            "\\Software\\SimonTatham\\PuTTY\\Sessions\\my%20session": {
                "Protocol": "ssh",
                "HostName": "host",
            },
        }
        result = filter_ssh_sessions(keys)
        self.assertIn("my session", result)
        self.assertEqual(result["my session"]["HostName"], "host")
