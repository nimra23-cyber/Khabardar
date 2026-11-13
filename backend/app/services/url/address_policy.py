"""SSRF address block policy (Req 11.2/11.3, 19.8).

Classifies an IP address (or a resolved hostname) as BLOCKED when it falls in a
loopback / private / link-local / metadata / reserved range. This is the core
of the SSRF guard: any outbound request on behalf of user input must be refused
when the target resolves to a blocked address. The demo analyzer does not fetch
URLs, but it uses this policy to (a) flag a submitted private/metadata host and
(b) guarantee that if fetching is ever enabled it cannot reach these ranges.

Pure, deterministic, no network calls in the classification itself. A separate
helper resolves a hostname (DNS) only when explicitly requested.
"""

from __future__ import annotations

import ipaddress
import socket

# Extra metadata addresses to block beyond what ``is_private`` covers.
_METADATA_ADDRESSES = {
    "169.254.169.254",  # AWS/GCP/Azure IMDS
    "fd00:ec2::254",    # AWS IPv6 IMDS
    "100.100.100.200",  # Alibaba metadata
}


def is_blocked_ip(ip: str) -> bool:
    """True if the IP is in a range we must never connect to (SSRF defense)."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        # Not a literal IP; cannot classify here (caller resolves first).
        return False
    if str(addr) in _METADATA_ADDRESSES:
        return True
    return (
        addr.is_loopback
        or addr.is_private
        or addr.is_link_local
        or addr.is_reserved
        or addr.is_multicast
        or addr.is_unspecified
    )


def resolve_all(host: str) -> list[str]:
    """Resolve a hostname to all A/AAAA addresses. Returns [] on failure.

    DNS resolution is the only network action here; it is used to evaluate the
    block policy against every resolved address (resolve-then-check). No
    connection is opened.
    """
    try:
        infos = socket.getaddrinfo(host, None)
    except (socket.gaierror, UnicodeError, OSError):
        return []
    addrs: list[str] = []
    for info in infos:
        sockaddr = info[4]
        if sockaddr and sockaddr[0] not in addrs:
            addrs.append(sockaddr[0])
    return addrs


def host_is_blocked(host: str) -> bool:
    """True if ``host`` is a literal blocked IP, or resolves to any blocked IP.

    A hostname that fails to resolve is NOT classified as blocked here (the
    analyzer reports network checks as unavailable in that case); it is only
    blocked when a resolved address is in a reserved range (fail-safe: if we
    cannot resolve, we also never fetch).
    """
    # Literal IP?
    try:
        ipaddress.ip_address(host)
        return is_blocked_ip(host)
    except ValueError:
        pass
    # Hostname: resolve and check every address.
    for ip in resolve_all(host):
        if is_blocked_ip(ip):
            return True
    return False
