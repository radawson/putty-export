"""Export PuTTY session settings from Windows registry to OpenSSH config format.

This package parses a Windows .reg file exported from the PuTTY Sessions key,
filters to SSH sessions (Protocol=ssh, non-empty HostName), and produces
OpenSSH client config text suitable for ``~/.ssh/config``.

Public API
----------
- :func:`parse_reg_file` -- Parse a .reg file into a nested dict of key paths and values.
- :func:`filter_ssh_sessions` -- Keep only SSH sessions with a hostname from the parsed keys.
- :func:`build_ssh_config` -- Build full OpenSSH config text from a sessions dict.
"""

from putty_export.reg_parser import parse_reg_file
from putty_export.session_filter import filter_ssh_sessions
from putty_export.ssh_config import build_ssh_config

__all__ = ["parse_reg_file", "filter_ssh_sessions", "build_ssh_config"]
