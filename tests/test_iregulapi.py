"""Tests for aioiregul.iregulapi utilities."""

import pytest

from aioiregul.iregulapi import split_host_port


class TestSplitHostPort:
    """Tests for split_host_port."""

    def test_host_with_port(self) -> None:
        """Host string containing a port should be split correctly."""
        host, port = split_host_port("example.com:2000")
        assert host == "example.com"
        assert port == 2000

    def test_host_without_port_no_fallback(self) -> None:
        """Host string without a port and no fallback should return None port."""
        host, port = split_host_port("example.com")
        assert host == "example.com"
        assert port is None

    def test_host_without_port_with_fallback(self) -> None:
        """Fallback port should be used when host has no embedded port."""
        host, port = split_host_port("example.com", 443)
        assert host == "example.com"
        assert port == 443

    def test_embedded_port_overrides_fallback(self) -> None:
        """Embedded port in host should take precedence over fallback port."""
        host, port = split_host_port("example.com:8080", 443)
        assert host == "example.com"
        assert port == 8080

    def test_ipv4_with_port(self) -> None:
        """IPv4 address with port should be split correctly."""
        host, port = split_host_port("192.168.1.100:9000")
        assert host == "192.168.1.100"
        assert port == 9000

    def test_ipv4_without_port(self) -> None:
        """IPv4 address without port should return None port."""
        host, port = split_host_port("192.168.1.100")
        assert host == "192.168.1.100"
        assert port is None

    def test_ipv6_with_port(self) -> None:
        """IPv6 address in brackets with port should be split correctly."""
        host, port = split_host_port("[::1]:8080")
        assert host == "::1"
        assert port == 8080

    def test_ipv6_without_port(self) -> None:
        """IPv6 address in brackets without port should return None port."""
        host, port = split_host_port("[::1]")
        assert host == "::1"
        assert port is None

    def test_port_boundary_low(self) -> None:
        """Port 1 should be accepted as valid."""
        host, port = split_host_port("example.com:1")
        assert port == 1

    def test_port_boundary_high(self) -> None:
        """Port 65535 should be accepted as valid."""
        host, port = split_host_port("example.com:65535")
        assert port == 65535

    def test_port_out_of_range_raises(self) -> None:
        """Port 0 should raise ValueError."""
        with pytest.raises(ValueError, match="out of the valid range"):
            split_host_port("example.com:0")

    def test_port_above_max_raises(self) -> None:
        """Port above 65535 should raise ValueError."""
        with pytest.raises(ValueError, match="out .* range"):
            split_host_port("example.com:65536")

    def test_subdomain_host_with_port(self) -> None:
        """Subdomain hostname with port should be handled correctly."""
        host, port = split_host_port("vpn.i-regul.com:2000")
        assert host == "vpn.i-regul.com"
        assert port == 2000
