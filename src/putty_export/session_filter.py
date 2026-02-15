"""Filter parsed registry keys to SSH sessions only (Protocol=ssh, non-empty HostName)."""

import re
from urllib.parse import unquote

# PuTTY sessions live under \Software\SimonTatham\PuTTY\Sessions\<SessionName>
SESSIONS_PREFIX = r"\Software\SimonTatham\PuTTY\Sessions"
SESSIONS_PREFIX_NORMALIZED = SESSIONS_PREFIX.lower().replace("/", "\\")


def _normalize_key(key: str) -> str:
    return key.replace("/", "\\").strip("\\").lower()


def _session_name_from_key(full_key: str) -> str | None:
    """Extract session name from key path. Returns None if not a session key."""
    norm = _normalize_key(full_key)
    prefix = SESSIONS_PREFIX_NORMALIZED.strip("\\")
    if not norm.startswith(prefix):
        return None
    suffix = norm[len(prefix) :].strip("\\")
    if not suffix:
        return None
    # Session name is the last segment in the original key
    parts = full_key.replace("/", "\\").strip("\\").split("\\")
    if len(parts) < 2:
        return None
    name = parts[-1]
    return unquote(name)


def filter_ssh_sessions(
    keys: dict[str, dict[str, object]],
    *,
    skip_default_settings: bool = True,
) -> dict[str, dict[str, object]]:
    """
    Return a dict of session_name -> session_values for keys that are SSH sessions:
    - Key path is ...\\Sessions\\<Name> (not the bare Sessions key).
    - Protocol (decoded string) equals "ssh" (case-insensitive).
    - HostName (decoded string) is non-empty after strip.
    - Optionally skip session name "Default Settings".
    Duplicate session names: later key wins.
    """
    result: dict[str, dict[str, object]] = {}
    norm_prefix = _normalize_key(SESSIONS_PREFIX).rstrip("\\")

    for full_key, values in keys.items():
        session_name = _session_name_from_key(full_key)
        if session_name is None:
            continue
        if skip_default_settings and session_name == "Default Settings":
            continue

        protocol_val = values.get("Protocol")
        if isinstance(protocol_val, str):
            protocol = protocol_val.strip().lower()
        else:
            protocol = ""
        if protocol != "ssh":
            continue

        hostname_val = values.get("HostName")
        if isinstance(hostname_val, str):
            hostname = hostname_val.strip()
        else:
            hostname = ""
        if not hostname:
            continue

        result[session_name] = dict(values)
    return result
