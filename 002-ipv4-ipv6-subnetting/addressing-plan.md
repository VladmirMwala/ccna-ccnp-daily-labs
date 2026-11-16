# 002 — Dual-Stack Addressing Plan: "LabCorp" HQ + Branch

This plan grows the [Project 001](../001-vlan-trunking-router-on-a-stick/) network into a
two-site company and addresses it for both IPv4 and IPv6.

## 1. Requirements

| Segment | Site | VLAN | Hosts needed (incl. 20% growth) |
|---------|------|------|---------------------------------|
| HQ-SALES | HQ | 10 | 200 |
| HQ-IT | HQ | 20 | 100 |
| BR-SALES | Branch | 110 | 50 |
| BR-IT | Branch | 120 | 25 |
| MGMT | Both | 99 | 10 |
| WAN-HQ-BR | Point-to-point | — | 2 |

**Address space assigned:**
- IPv4: `172.16.0.0/22` (1,024 addresses, private RFC 1918)
- IPv6: `2001:db8:acad::/48` (documentation prefix, RFC 3849, standing in for an ISP-assigned /48)

---

## 2. IPv4 Plan (VLSM)

**Method:** sort by size, largest first, and allocate each block on its own boundary.
Allocating largest first means no block ever straddles a boundary, so there are no gaps or overlaps.

| Hosts | Smallest fit | Why |
|-------|--------------|-----|
| 200 | /24 (254) | /25 gives only 126 |
| 100 | /25 (126) | /26 gives only 62 |
| 50 | /26 (62) | /27 gives only 30 |
| 25 | /27 (30) | /28 gives only 14 |
| 10 | /28 (14) | /29 gives only 6 |
| 2 | /30 (2) | point-to-point link |

| Segment | VLAN | Subnet | Mask | Gateway | Usable range | Broadcast |
|---------|------|--------|------|---------|--------------|-----------|
| HQ-SALES | 10 | 172.16.0.0/24 | 255.255.255.0 | 172.16.0.1 | .0.1 – .0.254 | 172.16.0.255 |
| HQ-IT | 20 | 172.16.1.0/25 | 255.255.255.128 | 172.16.1.1 | .1.1 – .1.126 | 172.16.1.127 |
| BR-SALES | 110 | 172.16.1.128/26 | 255.255.255.192 | 172.16.1.129 | .1.129 – .1.190 | 172.16.1.191 |
| BR-IT | 120 | 172.16.1.192/27 | 255.255.255.224 | 172.16.1.193 | .1.193 – .1.222 | 172.16.1.223 |
| MGMT | 99 | 172.16.1.224/28 | 255.255.255.240 | 172.16.1.225 | .1.225 – .1.238 | 172.16.1.239 |
| WAN-HQ-BR | — | 172.16.1.240/30 | 255.255.255.252 | HQ .241 / BR .242 | .1.241 – .1.242 | 172.16.1.243 |

**Free for growth:** `172.16.1.244/30`, `172.16.1.248/29`, `172.16.2.0/23` (half the space is still free).

**Host conventions inside every user subnet:**

| Range | Use |
|-------|-----|
| First usable | Router / gateway |
| Next 9 | Switches, printers, servers (static) |
| Rest | DHCP pool |

> Reproduce this table: `python scripts/subnet_calc.py vlsm 172.16.0.0/22 HQ-SALES=200 HQ-IT=100 BR-SALES=50 BR-IT=25 MGMT=10 WAN-HQ-BR=2`

---

## 3. IPv6 Plan

**Method:** every LAN gets a **/64** (required for SLAAC). The 16-bit subnet ID (4th hextet)
reuses the VLAN number, so `VLAN 20` → `2001:db8:acad:20::/64`. The digits are hex, so
"20" really means 0x20 (decimal 32). The point is readability, not math.

```
2001:0db8:acad : 0020 : 0000:0000:0000:0001
└─ /48 global ─┘ └ID┘   └──── 64-bit interface ID ────┘
  routing prefix  subnet
```

| Segment | VLAN | Prefix | Gateway (GUA) | Gateway link-local |
|---------|------|--------|---------------|--------------------|
| HQ-SALES | 10 | 2001:db8:acad:10::/64 | 2001:db8:acad:10::1 | fe80::1 |
| HQ-IT | 20 | 2001:db8:acad:20::/64 | 2001:db8:acad:20::1 | fe80::1 |
| MGMT | 99 | 2001:db8:acad:99::/64 | 2001:db8:acad:99::1 | fe80::1 |
| BR-SALES | 110 | 2001:db8:acad:110::/64 | 2001:db8:acad:110::1 | fe80::2 |
| BR-IT | 120 | 2001:db8:acad:120::/64 | 2001:db8:acad:120::1 | fe80::2 |
| WAN-HQ-BR | — | 2001:db8:acad:ff01::/64 | HQ `::1` / BR `::2` | fe80::1 / fe80::2 |

- A /48 holds **65,536** /64s, so this plan uses 6 of them.
- Static link-local addresses (`fe80::1` on HQ, `fe80::2` on Branch) make `show ipv6 route` next hops easy to read.
- Point-to-point links may use **/127** (RFC 6164). /64 is used here to keep the CCNA design simple.

**Sample router config (HQ, VLAN 10 subinterface):**
```
ipv6 unicast-routing
interface GigabitEthernet0/0/0.10
 encapsulation dot1Q 10
 ip address 172.16.0.1 255.255.255.0
 ipv6 address 2001:db8:acad:10::1/64
 ipv6 address fe80::1 link-local
```

---

## 4. Practice Problems

Solve on paper first, then check with the calculator or open the answer.

### IPv4

**1.** Host `192.168.45.130/27`: network, broadcast, usable range, number of hosts?
<details><summary>Answer</summary>

Block size 32 in octet 4 → subnets at .0, .32, .64, .96, **.128**, .160 …
Network `192.168.45.128`, broadcast `192.168.45.159`, usable `.129 – .158`, **30 hosts**.
</details>

**2.** Host `10.20.37.200/21`: network and broadcast?
<details><summary>Answer</summary>

/21 = 255.255.**248**.0 → block size 8 in octet 3 → 0, 8, 16, 24, **32**, 40 …
Network `10.20.32.0`, broadcast `10.20.39.255`, **2,046 hosts**.
</details>

**3.** Host `172.16.100.5/19`: network and broadcast?
<details><summary>Answer</summary>

/19 = 255.255.**224**.0 → block size 32 in octet 3 → 64, **96**, 128 …
Network `172.16.96.0`, broadcast `172.16.127.255`, **8,190 hosts**.
</details>

**4.** Smallest subnet for **500** hosts?
<details><summary>Answer</summary>

2⁹ − 2 = 510 ≥ 500 → 9 host bits → **/23** (`255.255.254.0`). A /24 holds only 254.
</details>

**5.** VLSM: split `192.168.50.0/24` for A = 60, B = 28, C = 12, WAN = 2 hosts.
<details><summary>Answer</summary>

| Segment | Subnet | Usable range |
|---------|--------|--------------|
| A | 192.168.50.0/26 | .1 – .62 |
| B | 192.168.50.64/27 | .65 – .94 |
| C | 192.168.50.96/28 | .97 – .110 |
| WAN | 192.168.50.112/30 | .113 – .114 |

Free: `.116/30`, `.120/29`, `.128/25`
</details>

### IPv6

**6.** Compress `2001:0db8:0000:0000:00a0:0000:0000:0001`
<details><summary>Answer</summary>

`2001:db8::a0:0:0:1`. There are two runs of two zero hextets. When runs tie, the
**leftmost** becomes `::` (RFC 5952), and `::` can only appear once.
</details>

**7.** Expand `2001:db8:acad::10:1`
<details><summary>Answer</summary>

`2001:0db8:acad:0000:0000:0000:0010:0001`. The `::` stands for three zero hextets (8 − 5 shown).
</details>

**8.** EUI-64 address for MAC `0C9A.3E12.3456` on prefix `2001:db8:acad:20::/64`?
<details><summary>Answer</summary>

1. Split: `0C9A3E | 123456` → insert `FFFE` → `0C9A:3EFF:FE12:3456`
2. Flip the 7th bit of `0C`: `00001100` → `00001110` = `0E`
3. Result: **`2001:db8:acad:20:e9a:3eff:fe12:3456`**
</details>
