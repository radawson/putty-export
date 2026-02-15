"""Filter parsed registry keys to SSH sessions only.

Keeps only keys that represent PuTTY sessions (under ``\\Sessions\\<Name>``),
have ``Protocol`` equal to ``ssh`` (case-insensitive), and have a non-empty
``HostName``. The "Default Settings" template session can be excluded or included.
Duplicate session names: the later key in the input dict wins.
"""

import re
from urllib.parse import unquote

# PuTTY sessions live under \Software\SimonTatham\PuTTY\Sessions\<SessionName>
SESSIONS_PREFIX = r"\Software\SimonTatham\PuTTY\Sessions"
SESSIONS_PREFIX_NORMALIZED = SESSIONS_PREFIX.lower().replace("/", "\\")


def _normalize_key(key: str) -> str:
    """Normalize a registry key path for comparison (backslashes, lowercase, no leading/trailing \\.)."""
    return key.replace("/", "\\").strip("\\").lower()


def _session_name_from_key(full_key: str) -> str | None:
    """Extract the session name from a registry key path (last segment, URL-decoded).

    :param full_key: Full registry key path (e.g. ``\\Software\\...\\Sessions\\my-session``).
    :type full_key: str
    :returns: Session name, or None if the key is not under Sessions or has no segment.
    :rtype: str | None
    """
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
    """Return session_name -> session_values for keys that are SSH sessions.

    Included keys must be under ``...\\Sessions\\<Name>`` (not the bare Sessions key),
    have ``Protocol`` equal to ``ssh`` (case-insensitive), and have a non-empty
    ``HostName``. If ``skip_default_settings`` is True, the "Default Settings"
    session is excluded. When the same session name appears for multiple keys,
    the later key wins.

    :param keys: Parsed registry dict from :func:`parse_reg_file`.
    :type keys: dict[str, dict[str, object]]
    :param skip_default_settings: If True, exclude the "Default Settings" session.
    :type skip_default_settings: bool
    :returns: Dict mapping session name (URL-decoded) to that key's value dict.
    :rtype: dict[str, dict[str, object]]
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
