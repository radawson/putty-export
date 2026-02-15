"""Unit tests for SSH config block generation."""

import unittest

from putty_export.ssh_config import build_host_block, build_ssh_config


class TestBuildHostBlock(unittest.TestCase):
    def test_minimal_host(self) -> None:
        data = {"HostName": "10.0.0.1", "PortNumber": 22}
        block = build_host_block("myhost", data)
        self.assertIn("Host myhost", block)
        self.assertIn("HostName 10.0.0.1", block)
        self.assertIn("Port 22", block)

    def test_user_and_identity(self) -> None:
        data = {
            "HostName": "git.example.com",
            "PortNumber": 22,
            "UserName": "git",
            "PublicKeyFile": "C:\\Users\\me\\.ssh\\id_rsa.ppk",
        }
        block = build_host_block("git", data)
        self.assertIn("User git", block)
        self.assertIn("IdentityFile", block)
        self.assertIn("C:/Users/me/.ssh/id_rsa.ppk", block)

    def test_proxy_jump(self) -> None:
        data = {
            "HostName": "internal",
            "PortNumber": 22,
            "ProxyMethod": 5,
            "ProxyHost": "jump.example.com",
            "ProxyUsername": "jumper",
        }
        block = build_host_block("internal", data)
        self.assertIn("ProxyJump jumper@jump.example.com", block)

    def test_socks_proxy(self) -> None:
        data = {
            "HostName": "target",
            "PortNumber": 22,
            "ProxyMethod": 1,
            "ProxyHost": "proxy.example.com",
            "ProxyPort": 1080,
        }
        block = build_host_block("target", data)
        self.assertIn("ProxyCommand nc -x proxy.example.com:1080 %h %p", block)

    def test_port_forwardings(self) -> None:
        data = {
            "HostName": "host",
            "PortNumber": 22,
            "PortForwardings": "L8080=localhost:80,R9022=localhost:22,D1080",
        }
        block = build_host_block("host", data)
        self.assertIn("LocalForward 8080 localhost:80", block)
        self.assertIn("RemoteForward 9022 localhost:22", block)
        self.assertIn("DynamicForward 1080", block)

    def test_forward_agent_and_compression(self) -> None:
        data = {
            "HostName": "host",
            "PortNumber": 22,
            "AgentFwd": 1,
            "Compression": 1,
            "X11Forward": 1,
        }
        block = build_host_block("host", data)
        self.assertIn("ForwardAgent yes", block)
        self.assertIn("Compression yes", block)
        self.assertIn("ForwardX11 yes", block)

    def test_host_alias_with_spaces_quoted(self) -> None:
        data = {"HostName": "host", "PortNumber": 22}
        block = build_host_block("my session", data)
        self.assertIn('Host "my session"', block)


class TestBuildSshConfig(unittest.TestCase):
    def test_sorted_hosts(self) -> None:
        sessions = {
            "z": {"HostName": "z.example.com", "PortNumber": 22},
            "a": {"HostName": "a.example.com", "PortNumber": 22},
        }
        config = build_ssh_config(sessions)
        self.assertTrue(config.index("Host a") < config.index("Host z"))

    def test_two_blocks_separated(self) -> None:
        sessions = {
            "one": {"HostName": "one.com", "PortNumber": 22},
            "two": {"HostName": "two.com", "PortNumber": 22},
        }
        config = build_ssh_config(sessions)
        self.assertIn("\n\n", config)
        self.assertEqual(config.count("Host "), 2)
