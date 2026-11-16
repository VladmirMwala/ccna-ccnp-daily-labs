#!/usr/bin/env python3
"""
subnet_calc.py - IPv4 / IPv6 subnet calculator for CCNA practice.

Standard library only (ipaddress, argparse, random), so there is nothing to install.

Commands
--------
  info   ADDRESS/PREFIX                    Everything about one subnet (IPv4 or IPv6)
  split  NETWORK/PREFIX --prefix N         Divide a network into equal-size subnets
  vlsm   NETWORK/PREFIX NAME=HOSTS ...     Variable-length allocation, largest first
  eui64  IPV6-PREFIX/64 MAC                Build an EUI-64 address step by step
  quiz   [--count N]                       Practice: network, broadcast, usable hosts

Examples
--------
  python subnet_calc.py info 192.168.10.77/26
  python subnet_calc.py info 192.168.10.77 255.255.255.192
  python subnet_calc.py info 2001:db8:acad:10::1/64
  python subnet_calc.py split 192.168.10.0/24 --prefix 26
  python subnet_calc.py vlsm 172.16.0.0/22 HQ-SALES=200 HQ-IT=100 WAN=2
  python subnet_calc.py eui64 2001:db8:acad:10::/64 00:1A:2B:3C:4D:5E
  python subnet_calc.py quiz --count 5
"""
from __future__ import annotations

import argparse
import ipaddress
import random
import re
import sys
from typing import Callable

Network = ipaddress.IPv4Network | ipaddress.IPv6Network
Address = ipaddress.IPv4Address | ipaddress.IPv6Address

# ---------------------------------------------------------------------------
# Address classification
# Order matters: the first matching range wins.
# ---------------------------------------------------------------------------
_SPECIAL_RANGES: list[tuple[str, Network]] = [
    (label, ipaddress.ip_network(cidr))
    for label, cidr in [
        ("This network (RFC 791)", "0.0.0.0/8"),
        ("Loopback", "127.0.0.0/8"),
        ("Link-local / APIPA (RFC 3927)", "169.254.0.0/16"),
        ("Documentation TEST-NET-1 (RFC 5737)", "192.0.2.0/24"),
        ("Documentation TEST-NET-2 (RFC 5737)", "198.51.100.0/24"),
        ("Documentation TEST-NET-3 (RFC 5737)", "203.0.113.0/24"),
        ("Private (RFC 1918)", "10.0.0.0/8"),
        ("Private (RFC 1918)", "172.16.0.0/12"),
        ("Private (RFC 1918)", "192.168.0.0/16"),
        ("Shared / CGNAT (RFC 6598)", "100.64.0.0/10"),
        ("Multicast (Class D)", "224.0.0.0/4"),
        ("Reserved (Class E)", "240.0.0.0/4"),
        ("Unspecified", "::/128"),
        ("Loopback", "::1/128"),
        ("Link-local", "fe80::/10"),
        ("Unique local / ULA (RFC 4193)", "fc00::/7"),
        ("Multicast", "ff00::/8"),
        ("Documentation (RFC 3849)", "2001:db8::/32"),
        ("Global unicast", "2000::/3"),
    ]
]


def address_type(addr: Address) -> str:
    """Return a human-readable category such as 'Private (RFC 1918)'."""
    for label, net in _SPECIAL_RANGES:
        if addr in net:  # always False when IP versions differ
            return label
    return "Public" if addr.version == 4 else "Reserved / unassigned"


def ipv4_class(addr: ipaddress.IPv4Address) -> str:
    """Classful category from the first octet (historical, still tested on the CCNA)."""
    first = int(str(addr).split(".")[0])
    if first == 0:
        return "Reserved"
    if first <= 126:
        return "A (default /8)"
    if first == 127:
        return "Loopback"
    if first <= 191:
        return "B (default /16)"
    if first <= 223:
        return "C (default /24)"
    if first <= 239:
        return "D (multicast)"
    return "E (experimental)"


# ---------------------------------------------------------------------------
# Core subnet math
# ---------------------------------------------------------------------------
def usable_hosts(net: Network) -> int:
    """
    Number of assignable host addresses.

    IPv4 reserves the network and broadcast addresses, except:
      /31 -> 2 (point-to-point links, RFC 3021)
      /32 -> 1 (a single host route, e.g. a loopback)
    IPv6 has no broadcast address, so every address counts.
    """
    if net.version == 6:
        return net.num_addresses
    if net.prefixlen == 32:
        return 1
    if net.prefixlen == 31:
        return 2
    return net.num_addresses - 2


def host_range(net: Network) -> tuple[Address, Address]:
    """First and last usable addresses."""
    last = net.broadcast_address  # for IPv6 this is simply the last address
    if net.max_prefixlen - net.prefixlen <= 1:  # /31, /32, /127, /128
        return net.network_address, last
    if net.version == 6:
        # ::0 is the subnet-router anycast address, so hosts conventionally start at ::1
        return net.network_address + 1, last
    return net.network_address + 1, last - 1


def block_size(net: ipaddress.IPv4Network) -> tuple[int, int]:
    """
    The 'magic number' shortcut: (block size, interesting octet 1-4).
    /26 -> (64, 4): subnets start every 64 in the 4th octet.
    /21 -> (8, 3):  subnets start every 8 in the 3rd octet.
    """
    p = net.prefixlen
    if p == 0:
        return 256, 1
    octet = (p - 1) // 8  # 0-based octet holding the last network bit
    bits_in_octet = p - 8 * octet
    return 2 ** (8 - bits_in_octet), octet + 1


def mask_to_binary(mask: ipaddress.IPv4Address) -> str:
    return ".".join(f"{int(o):08b}" for o in str(mask).split("."))


def parse_interface(text: str) -> ipaddress.IPv4Interface | ipaddress.IPv6Interface:
    """
    Accept '192.168.10.77/26', '192.168.10.77/255.255.255.192',
    '192.168.10.77 255.255.255.192' or an IPv6 'addr/prefix'.
    A bare address is treated as a host (/32 or /128).
    """
    text = text.strip()
    if " " in text:
        text = "/".join(text.split())
    return ipaddress.ip_interface(text)


def prefix_for_hosts(hosts: int) -> int:
    """Smallest IPv4 subnet (longest prefix) that fits `hosts` usable addresses."""
    if hosts < 1:
        raise ValueError("host count must be at least 1")
    for prefix in range(30, -1, -1):
        if 2 ** (32 - prefix) - 2 >= hosts:
            return prefix
    raise ValueError(f"{hosts} hosts does not fit in any IPv4 subnet")


# ---------------------------------------------------------------------------
# Commands (each returns data, so it can be unit tested without printing)
# ---------------------------------------------------------------------------
def describe(text: str) -> dict[str, str]:
    """Build an ordered label -> value report for one address/prefix."""
    iface = parse_interface(text)
    net, addr = iface.network, iface.ip
    first, last = host_range(net)
    info: dict[str, str] = {}

    if net.version == 4:
        if net.prefixlen <= 30 and addr == net.network_address:
            role = "network address (not assignable)"
        elif net.prefixlen <= 30 and addr == net.broadcast_address:
            role = "broadcast address (not assignable)"
        else:
            role = "host address"
        block, octet = block_size(net)
        info["Address"] = f"{addr}  <- {role}"
        info["Network"] = str(net)
        info["Subnet mask"] = str(net.netmask)
        info["Wildcard mask"] = str(net.hostmask)
        info["Mask (binary)"] = mask_to_binary(net.netmask)
        info["Broadcast"] = str(net.broadcast_address)
        info["First usable"] = str(first)
        info["Last usable"] = str(last)
        info["Total addresses"] = f"{net.num_addresses:,}"
        info["Usable hosts"] = f"{usable_hosts(net):,}"
        info["Block size"] = f"{block} (octet {octet})"
        info["Class"] = ipv4_class(addr)
        info["Type"] = address_type(addr)
    else:
        info["Address"] = addr.compressed
        info["Expanded"] = addr.exploded
        info["Network"] = net.compressed
        info["Prefix length"] = f"/{net.prefixlen}"
        info["First address"] = str(first)
        info["Last address"] = str(last)
        host_bits = net.max_prefixlen - net.prefixlen
        info["Total addresses"] = f"2^{host_bits} = {net.num_addresses:,}"
        if net.prefixlen < 64:
            info["/64 subnets inside"] = f"2^{64 - net.prefixlen} = {2 ** (64 - net.prefixlen):,}"
        info["Type"] = address_type(addr)
    return info


def split(network: str, new_prefix: int) -> list[Network]:
    """Divide `network` into equal subnets of length /new_prefix."""
    net = ipaddress.ip_network(network, strict=False)
    if not net.prefixlen < new_prefix <= net.max_prefixlen:
        raise ValueError(f"--prefix must be between /{net.prefixlen + 1} and /{net.max_prefixlen}")
    return list(net.subnets(new_prefix=new_prefix))


def parse_requirement(item: str) -> tuple[str, int]:
    """'HQ-SALES=200' -> ('HQ-SALES', 200)"""
    name, sep, hosts = item.partition("=")
    if not sep or not name or not hosts.isdigit():
        raise ValueError(f"bad requirement '{item}', expected NAME=HOSTS (e.g. SALES=50)")
    return name, int(hosts)


def vlsm(network: str, requirements: list[tuple[str, int]]) -> tuple[list[tuple[str, int, Network]], list[Network]]:
    """
    Allocate subnets largest-first so every block stays aligned on its boundary.
    Returns (allocations, free_blocks).
    """
    base = ipaddress.ip_network(network, strict=False)
    if base.version != 4:
        raise ValueError("VLSM by host count is IPv4 only (IPv6 uses /64 per LAN)")

    ordered = sorted(requirements, key=lambda r: r[1], reverse=True)  # stable sort
    cursor = int(base.network_address)
    end = int(base.broadcast_address)
    allocations: list[tuple[str, int, Network]] = []

    for name, hosts in ordered:
        prefix = prefix_for_hosts(hosts)
        subnet = ipaddress.ip_network(f"{ipaddress.IPv4Address(cursor)}/{prefix}")
        if int(subnet.broadcast_address) > end:
            raise ValueError(f"'{name}' needs a /{prefix} but {base} is out of space")
        allocations.append((name, hosts, subnet))
        cursor = int(subnet.broadcast_address) + 1

    free = (
        list(ipaddress.summarize_address_range(ipaddress.IPv4Address(cursor), base.broadcast_address))
        if cursor <= end
        else []
    )
    return allocations, free


def eui64(prefix: str, mac: str) -> tuple[ipaddress.IPv6Address, list[tuple[str, str]]]:
    """Return the EUI-64 address plus the worked steps, for learning."""
    net = ipaddress.IPv6Network(prefix, strict=False)
    if net.prefixlen != 64:
        raise ValueError("EUI-64 needs a /64 prefix")
    digits = re.sub(r"[^0-9a-fA-F]", "", mac)
    if len(digits) != 12:
        raise ValueError(f"'{mac}' is not a 48-bit MAC address")

    digits = digits.lower()
    mac_bytes = bytearray.fromhex(digits)
    original_first = mac_bytes[0]
    mac_bytes[0] ^= 0x02  # flip the Universal/Local bit (7th bit of the first byte)
    iid = bytes(mac_bytes[:3]) + b"\xff\xfe" + bytes(mac_bytes[3:])
    address = ipaddress.IPv6Address(int(net.network_address) | int.from_bytes(iid, "big"))

    iid_hex = iid.hex()
    steps = [
        ("1. MAC address", ":".join(digits[i:i + 2] for i in range(0, 12, 2))),
        ("2. Split in half", f"{digits[:6]} | {digits[6:]}"),
        ("3. Insert FFFE", f"{digits[:6]} fffe {digits[6:]}"),
        ("4. Flip 7th bit", f"{original_first:08b} -> {mac_bytes[0]:08b}  ({original_first:02x} -> {mac_bytes[0]:02x})"),
        ("5. Interface ID", ":".join(iid_hex[i:i + 4] for i in range(0, 16, 4))),
        ("6. Prefix + ID", address.compressed),
    ]
    return address, steps


def quiz(count: int, rng: random.Random | None = None, ask: Callable[[str], str] = input) -> int:
    """Interactive practice. Returns the number of fully correct questions."""
    rng = rng or random.Random()
    pools = [ipaddress.ip_network(n) for n in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")]
    score = 0

    for n in range(1, count + 1):
        pool = rng.choice(pools)
        addr = pool.network_address + rng.randrange(pool.num_addresses)
        net = ipaddress.ip_interface(f"{addr}/{rng.randint(17, 30)}").network
        print(f"\nQ{n}. Host {addr}/{net.prefixlen}  (mask {net.netmask})")

        checks = [
            ("Network address", str(net.network_address)),
            ("Broadcast address", str(net.broadcast_address)),
            ("Usable hosts", str(usable_hosts(net))),
        ]
        correct = 0
        for label, answer in checks:
            reply = ask(f"   {label}: ").strip().replace(",", "")
            if reply == answer:
                correct += 1
                print("     correct")
            else:
                print(f"     answer: {answer}")
        if correct == len(checks):
            score += 1
        block, octet = block_size(net)
        print(f"   Tip: block size {block} in octet {octet}")

    print(f"\nScore: {score}/{count}")
    return score


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------
def print_pairs(pairs: list[tuple[str, str]] | dict[str, str]) -> None:
    items = list(pairs.items()) if isinstance(pairs, dict) else pairs
    width = max(len(k) for k, _ in items)
    for key, value in items:
        print(f"  {key:<{width}} : {value}")


def print_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max(len(str(c)) for c in col) for col in zip(headers, *rows)]
    line = "  ".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for row in rows:
        print("  ".join(f"{str(c):<{w}}" for c, w in zip(row, widths)))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="IPv4/IPv6 subnet calculator for CCNA practice.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Examples", 1)[1] if __doc__ else None,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("info", help="details for one address/prefix")
    p.add_argument("address", nargs="+", help="e.g. 10.1.1.9/27, '10.1.1.9 255.255.255.224' or 2001:db8::1/64")

    p = sub.add_parser("split", help="divide a network into equal subnets")
    p.add_argument("network")
    p.add_argument("--prefix", type=int, required=True, help="new prefix length, e.g. 26")
    p.add_argument("--limit", type=int, default=64, help="max rows to print (default 64)")

    p = sub.add_parser("vlsm", help="allocate subnets by host count (IPv4)")
    p.add_argument("network")
    p.add_argument("requirements", nargs="+", metavar="NAME=HOSTS")

    p = sub.add_parser("eui64", help="build an EUI-64 IPv6 address from a MAC")
    p.add_argument("prefix", help="a /64, e.g. 2001:db8:acad:10::/64")
    p.add_argument("mac", help="any format: 001A.2B3C.4D5E, 00-1A-2B-3C-4D-5E ...")

    p = sub.add_parser("quiz", help="practice subnetting questions")
    p.add_argument("--count", type=int, default=5)
    p.add_argument("--seed", type=int, help="repeat the same questions")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "info":
            print_pairs(describe(" ".join(args.address)))

        elif args.command == "split":
            subnets = split(args.network, args.prefix)
            print(f"{args.network} -> {len(subnets):,} subnets of /{args.prefix} "
                  f"({usable_hosts(subnets[0]):,} usable hosts each)\n")
            rows = []
            for i, s in enumerate(subnets[: args.limit]):
                first, last = host_range(s)
                rows.append([str(i), s.compressed, f"{first} - {last}",
                             str(s.broadcast_address) if s.version == 4 else "n/a"])
            print_table(["#", "Subnet", "Usable range", "Broadcast"], rows)
            if len(subnets) > args.limit:
                print(f"... {len(subnets) - args.limit:,} more (use --limit)")

        elif args.command == "vlsm":
            reqs = [parse_requirement(r) for r in args.requirements]
            allocations, free = vlsm(args.network, reqs)
            rows = []
            for name, hosts, s in allocations:
                first, last = host_range(s)
                rows.append([name, str(hosts), str(usable_hosts(s)), str(s), str(s.netmask),
                             f"{first} - {last}", str(s.broadcast_address)])
            print_table(["Name", "Need", "Usable", "Subnet", "Mask", "Usable range", "Broadcast"], rows)
            print("\nFree for growth: " + (", ".join(str(f) for f in free) or "none"))

        elif args.command == "eui64":
            _, steps = eui64(args.prefix, args.mac)
            print_pairs(steps)

        elif args.command == "quiz":
            try:
                quiz(args.count, random.Random(args.seed))
            except (EOFError, KeyboardInterrupt):
                print("\nQuiz stopped.")

    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
