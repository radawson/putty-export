"""CLI entrypoint: read a PuTTY .reg file and emit OpenSSH config to stdout or a file.

Parses the given .reg file, filters to SSH sessions with a hostname, builds
OpenSSH config text, and either prints it or writes it to the specified file.
Uses only the standard library (argparse, pathlib, etc.).
"""

import argparse
import sys
from pathlib import Path

from putty_export.reg_parser import parse_reg_file
from putty_export.session_filter import filter_ssh_sessions
from putty_export.ssh_config import build_ssh_config

EPILOG = """
Examples:
  putty-export putty_sessions.reg
  putty-export putty_sessions.reg -o ~/.ssh/config
  putty-export putty_sessions.reg --include-default-settings -o config
"""


def main() -> None:
    """Parse arguments, run the export pipeline, and write output.

    Reads the .reg file, filters to SSH sessions (Protocol=ssh, non-empty HostName),
    builds SSH config, and writes to --output or stdout. Exits 0 on success, 1 if
    the file is missing or cannot be read.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Export PuTTY session settings from a Windows registry (.reg) file to "
            "OpenSSH config format. Only SSH sessions with a hostname are included; "
            "the 'Default Settings' template is skipped unless requested."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "reg_file",
        type=Path,
        help=(
            "Path to the exported PuTTY Sessions .reg file (from "
            "HKEY_CURRENT_USER\\Software\\SimonTatham\\PuTTY\\Sessions)."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help=(
            "Write the generated OpenSSH config to this file (overwrites if it exists). "
            "If omitted, print to stdout."
        ),
    )
    parser.add_argument(
        "--include-default-settings",
        action="store_true",
        help=(
            "Include the 'Default Settings' template session in the output if it "
            "has a hostname. By default it is skipped."
        ),
    )
    args = parser.parse_args()

    if not args.reg_file.exists():
        print(f"Error: file not found: {args.reg_file}", file=sys.stderr)
        sys.exit(1)

    try:
        keys = parse_reg_file(args.reg_file)
    except OSError as e:
        print(f"Error reading {args.reg_file}: {e}", file=sys.stderr)
        sys.exit(1)

    sessions = filter_ssh_sessions(keys, skip_default_settings=not args.include_default_settings)
    config = build_ssh_config(sessions)

    if args.output is not None:
        args.output.write_text(config, encoding="utf-8")
    else:
        print(config)


if __name__ == "__main__":
    main()
