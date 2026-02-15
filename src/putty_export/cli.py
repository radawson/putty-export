"""CLI entrypoint: read .reg file, emit SSH config to stdout or file."""

import argparse
import sys
from pathlib import Path

from putty_export.reg_parser import parse_reg_file
from putty_export.session_filter import filter_ssh_sessions
from putty_export.ssh_config import build_ssh_config


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export PuTTY session settings from a Windows registry (.reg) file to OpenSSH config format.",
    )
    parser.add_argument(
        "reg_file",
        type=Path,
        help="Path to the exported PuTTY Sessions .reg file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Write config to this file instead of stdout",
    )
    parser.add_argument(
        "--include-default-settings",
        action="store_true",
        help="Include the 'Default Settings' template session if it has a hostname",
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
