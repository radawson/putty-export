"""Build OpenSSH config text from filtered PuTTY session data."""

import re
from typing import Any


def _get_str(data: dict[str, Any], key: str, default: str = "") -> str:
    v = data.get(key)
    if isinstance(v, str):
        return v.strip()
    return default


def _get_int(data: dict[str, Any], key: str, default: int = 0) -> int:
    v = data.get(key)
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return default


def _quote_value(s: str) -> str:
    """Quote value if it contains spaces or special characters."""
    if not s:
        return '""'
    if re.search(r'[\s#"\\]', s):
        return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return s


def _build_proxy_directive(data: dict[str, Any]) -> str | None:
    """Build ProxyCommand or ProxyJump line. Returns None if no proxy."""
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
    """
    Parse PortForwardings string. Returns list of (directive_name, value).
    Format: Lport=host:port, Rport=host:port, Dport. Optional bind: Lbind:port=host:port.
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
    """Normalize path: backslashes to forward slashes for cross-platform hint."""
    if not path:
        return path
    return path.replace("\\", "/")


def build_host_block(session_name: str, data: dict[str, Any]) -> str:
    """Build one Host block for a single session. session_name becomes the Host alias."""
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
    """Build full SSH config from sessions dict (session_name -> values)."""
    blocks = []
    for name in sorted(sessions.keys()):
        blocks.append(build_host_block(name, sessions[name]))
    return "\n\n".join(blocks)
