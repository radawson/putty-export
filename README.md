# putty-export

Export PuTTY session settings from a Windows registry (.reg) file to OpenSSH `~/.ssh/config` format.

## Usage

```bash
# Print SSH config to stdout
putty-export putty_sessions.reg

# Write to a file
putty-export putty_sessions.reg -o ~/.ssh/config

# Include the "Default Settings" template session (normally skipped)
putty-export putty_sessions.reg --include-default-settings -o config
```

## Exporting PuTTY sessions from Windows

1. Open **Registry Editor** (`regedit.exe`).
2. Navigate to `HKEY_CURRENT_USER\Software\SimonTatham\PuTTY\Sessions`.
3. Right-click **Sessions** and choose **Export**.
4. Save as a `.reg` file (e.g. `putty_sessions.reg`) and transfer it to the machine where you run `putty-export`.

## PuTTY → OpenSSH mapping

| PuTTY (registry)              | OpenSSH config                | Notes |
|--------------------------------|-------------------------------|-------|
| Session name (from key path)   | `Host`                        | URL-decoded (e.g. `%20` → space). |
| HostName                       | `HostName`                    | Decoded from UTF-16LE. |
| PortNumber                     | `Port`                        | Default 22 if missing. |
| UserName                       | `User`                        | Omitted if empty. |
| PublicKeyFile                  | `IdentityFile`                | Path normalized to forward slashes. See [Keys](#keys) below. |
| ProxyMethod + ProxyHost/Port/Username | `ProxyCommand` or `ProxyJump` | See [Proxy](#proxy) below. |
| PortForwardings                | `LocalForward` / `RemoteForward` / `DynamicForward` | Comma-separated: `Lport=host:port`, `Rport=host:port`, `Dport`. |
| AgentFwd                       | `ForwardAgent`                 | 1 → yes (omitted when 0). |
| Compression                    | `Compression`                 | 1 → yes (omitted when 0). |
| X11Forward                     | `ForwardX11`                  | 1 → yes (omitted when 0). |

### Keys

- **IdentityFile** is written with the path from PuTTY (backslashes converted to forward slashes). PuTTY uses `.ppk` keys; OpenSSH uses PEM/OpenSSH format. Convert keys with:
  ```bash
  puttygen key.ppk -O private-openssh -o ~/.ssh/key_openssh
  ```
  Then point `IdentityFile` at the converted file, or replace the path in the generated config.

### Proxy

- **ProxyMethod** 0 = none (no directive). 1 = SOCKS → `ProxyCommand nc -x host:port %h %p`. 2 = HTTP CONNECT → `ProxyCommand connect -H host:port %h %p`. 3/4 = Telnet/Local → `ProxyCommand` from ProxyTelnetCommand. 5 = SSH proxy → `ProxyJump user@host`.
- **ProxyPassword** is not stored in SSH config. Use key-based auth or other means for proxy/jump host authentication.

## Requirements

- Python 3.8+
- No external dependencies (stdlib only).

## Installation

```bash
pip install -e .
```

## Development

Run tests:

```bash
python -m unittest discover -s tests -v
```

