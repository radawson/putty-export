"""Integration test: full pipeline on a minimal .reg file."""

import tempfile
import unittest
from pathlib import Path

from putty_export.reg_parser import parse_reg_file
from putty_export.session_filter import filter_ssh_sessions
from putty_export.ssh_config import build_ssh_config


class TestIntegration(unittest.TestCase):
    def test_full_pipeline_minimal_reg(self) -> None:
        # Minimal valid PuTTY session: SSH + HostName
        reg_content = """Windows Registry Editor Version 5.00

[\\Software\\SimonTatham\\PuTTY\\Sessions\\integration-test]
"HostName"=hex(1):31,00,30,00,2e,00,30,00,2e,00,30,00,2e,00,31,00,00,00
"Protocol"=hex(1):73,00,73,00,68,00,00,00
"PortNumber"=dword:00000016
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".reg", delete=False, encoding="utf-8") as f:
            f.write(reg_content)
            reg_path = Path(f.name)
        try:
            keys = parse_reg_file(reg_path)
            sessions = filter_ssh_sessions(keys)
            config = build_ssh_config(sessions)
            self.assertIn("Host integration-test", config)
            self.assertIn("HostName 10.0.0.1", config)
            self.assertIn("Port 22", config)
        finally:
            reg_path.unlink()
