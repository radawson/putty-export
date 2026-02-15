"""Build OpenSSH config text from filtered PuTTY session data.

Maps PuTTY session key names (e.g. HostName, PortNumber, ProxyMethod) to
OpenSSH config directives. Produces Host blocks with HostName, Port, User,
IdentityFile, ProxyCommand/ProxyJump, LocalForward/RemoteForward/DynamicForward,
ForwardAgent, Compression, and ForwardX11 as applicable.
"""

import re
from typing import Any


def _get_str(data: dict[str, Any], key: str, default: str = "") -> str:
    """Return a string value from the session dict, or default if missing/non-string."""
    v = data.get(key)
    if isinstance(v, str):
        return v.strip()
    return default


def _get_int(data: dict[str, Any], key: str, default: int = 0) -> int:
    """Return an integer value from the session dict, or default if missing/non-integer."""
    v = data.get(key)
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return default


def _quote_value(s: str) -> str:
    """Quote a value for SSH config if it contains spaces or special characters.

    :param s: The value string (e.g. Host alias or path).
    :type s: str
    :returns: The value, optionally wrapped in double quotes with escapes.
    :rtype: str
    """
    if not s:
        return '""'
    if re.search(r'[\s#"\\]', s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _build_proxy_directive(data: dict[str, Any]) -> str | None:
    """Build a single ProxyCommand or ProxyJump line from session proxy settings.

    ProxyMethod: 0 = none (returns None), 1 = SOCKS, 2 = HTTP CONNECT, 3 = Telnet,
    4 = Local command, 5 = SSH (jump host). Uses ProxyHost, ProxyPort, ProxyUsername,
    and ProxyTelnetCommand as needed.

    :param data: Session values dict.
    :type data: dict[str, Any]
    :returns: One indented line (e.g. ``  ProxyJump user@host``), or None if no proxy.
    :rtype: str | None
    """
    method = _get_int(data, "ProxyMethod", 0)
    host = _get_str(data, "ProxyHost")
    if method == 0 or not host:
        return None
    port = _get_int(data, "ProxyPort", 80)
    username = _get_str(data, "ProxyUsername")

    if method == 5:
        # SSH proxy (jump host)
        if username:
            return f"  ProxyJump {username}@{host}"
        return f"  ProxyJump {host}"

    if method == 1:
        # SOCKS 4/5
        return f"  ProxyCommand nc -x {host}:{port} %h %p"
    if method == 2:
        # HTTP CONNECT
        return f"  ProxyCommand connect -H {host}:{port} %h %p"
    if method in (3, 4):
        # Telnet or Local: use ProxyTelnetCommand (custom command)
        cmd = _get_str(data, "ProxyTelnetCommand")
        if cmd:
            cmd = cmd.replace("%host", "%h").replace("%port", "%p")
            return f"  ProxyCommand {cmd}"
        return None
    return None


def _parse_port_forwardings(raw: str) -> list[tuple[str, str]]:
    """Parse PuTTY PortForwardings string into (directive_name, value) pairs.

    Format is comma-separated: ``Lport=host:port`` (LocalForward), ``Rport=host:port``
    (RemoteForward), ``Dport`` (DynamicForward). Optional bind address: ``Lbind:port=host:port``.

    :param raw: Comma-separated PortForwardings string from session data.
    :type raw: str
    :returns: List of (directive_name, value) e.g. ``("LocalForward", "8080 localhost:80")``.
    :rtype: list[tuple[str, str]]
    """
    if not raw or not raw.strip():
        return []
    result = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if part.startswith("L"):
            rest = part[1:]
            if "=" in rest:
                left, right = rest.split("=", 1)
                # left can be "port" or "bind:port"
                result.append(("LocalForward", f"{left.strip()} {right.strip()}"))
            else:
                result.append(("LocalForward", rest))
        elif part.startswith("R"):
            rest = part[1:]
            if "=" in rest:
                left, right = rest.split("=", 1)
                result.append(("RemoteForward", f"{left.strip()} {right.strip()}"))
            else:
                result.append(("RemoteForward", rest))
        elif part.startswith("D"):
            port = part[1:].strip()
            if port:
                result.append(("DynamicForward", port))
    return result


def _identity_file_path(path: str) -> str:
    """Normalize a path by converting backslashes to forward slashes.

    :param path: Typically a Windows path from PuTTY (e.g. ``C:\\Users\\.ssh\\key.ppk``).
    :type path: str
    :returns: Same path with backslashes replaced by forward slashes; empty input returned as-is.
    :rtype: str
    """
    if not path:
        return path
    return path.replace("\\", "/")


def build_host_block(session_name: str, data: dict[str, Any]) -> str:
    """Build one OpenSSH Host block for a single session.

    :param session_name: Used as the Host alias (may contain spaces; will be quoted if needed).
    :type session_name: str
    :param data: Session values dict (e.g. from :func:`filter_ssh_sessions`).
    :type data: dict[str, Any]
    :returns: A single Host block as a multi-line string, with directives indented by two spaces.
    :rtype: str
    """
    lines = [f"Host {_quote_value(session_name)}"]

    hostname = _get_str(data, "HostName")
    if hostname:
        lines.append(f"  HostName {hostname}")

    port = _get_int(data, "PortNumber", 22)
    if port != 22:
        lines.append(f"  Port {port}")
    else:
        lines.append("  Port 22")

    user = _get_str(data, "UserName")
    if user:
        lines.append(f"  User {user}")

    identity = _get_str(data, "PublicKeyFile")
    if identity:
        lines.append(f"  IdentityFile {_quote_value(_identity_file_path(identity))}")

    proxy = _build_proxy_directive(data)
    if proxy:
        lines.append(proxy)

    port_fwd = _get_str(data, "PortForwardings")
    for directive, value in _parse_port_forwardings(port_fwd):
        lines.append(f"  {directive} {value}")

    agent_fwd = _get_int(data, "AgentFwd", 0)
    if agent_fwd:
        lines.append("  ForwardAgent yes")

    compression = _get_int(data, "Compression", 0)
    if compression:
        lines.append("  Compression yes")

    x11 = _get_int(data, "X11Forward", 0)
    if x11:
        lines.append("  ForwardX11 yes")

    return "\n".join(lines)


def build_ssh_config(sessions: dict[str, dict[str, Any]]) -> str:
    """Build full OpenSSH config text from a dict of sessions.

    Host blocks are emitted in sorted order by session name, separated by blank lines.

    :param sessions: Dict mapping session name to session values (e.g. from :func:`filter_ssh_sessions`).
    :type sessions: dict[str, dict[str, Any]]
    :returns: Complete SSH config file content as a single string.
    :rtype: str
    """
    blocks = []
    for name in sorted(sessions.keys()):
        blocks.append(build_host_block(name, sessions[name]))
    return "\n\n".join(blocks)
