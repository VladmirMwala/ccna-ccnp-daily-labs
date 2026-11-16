# 002 — IPv4/IPv6 Subnetting: Addressing Plan + Python Subnet Calculator

| Date | Track | Exam Topics | Difficulty | Est. Time |
|------|-------|-------------|------------|-----------|
| 2026-11-16 | CCNA 200-301 | 1.6 IPv4 addressing & subnetting · 1.7 Private IPv4 · 1.8–1.9 IPv6 addressing & types | ⭐⭐☆☆☆ | 60–90 min |

## 🎯 Objective

Design a dual-stack (IPv4 + IPv6) addressing plan for a two-site company using VLSM, and
build a command-line subnet calculator in Python to check the work.

- [ ] Size every subnet from host requirements with VLSM (no overlaps, no gaps)
- [ ] Assign a /64 per VLAN from a /48 with a readable subnet-ID scheme
- [ ] Solve 8 practice problems by hand (IPv4, VLSM, IPv6 compression, EUI-64)
- [ ] Write a tested Python tool: `info`, `split`, `vlsm`, `eui64`, `quiz`

## 🗺️ Scenario

```
   HQ (VLAN 10, 20, 99)                     Branch (VLAN 110, 120, 99)
   ┌──────────┐    WAN 172.16.1.240/30      ┌──────────┐
   │  R-HQ    │──────────────────────────── │  R-BR    │
   └──────────┘   2001:db8:acad:ff01::/64   └──────────┘
   172.16.0.0/22  +  2001:db8:acad::/48 shared across both sites
```

The full plan, with tables, method and practice problems, is in **[`addressing-plan.md`](addressing-plan.md)**.

| Segment | IPv4 | IPv6 |
|---------|------|------|
| HQ-SALES (VLAN 10) | 172.16.0.0/24 | 2001:db8:acad:10::/64 |
| HQ-IT (VLAN 20) | 172.16.1.0/25 | 2001:db8:acad:20::/64 |
| BR-SALES (VLAN 110) | 172.16.1.128/26 | 2001:db8:acad:110::/64 |
| BR-IT (VLAN 120) | 172.16.1.192/27 | 2001:db8:acad:120::/64 |
| MGMT (VLAN 99) | 172.16.1.224/28 | 2001:db8:acad:99::/64 |
| WAN HQ–Branch | 172.16.1.240/30 | 2001:db8:acad:ff01::/64 |

## 🧰 Tools

- **Python 3.10+**, standard library only (`ipaddress`, `argparse`), nothing to `pip install`
- `unittest` for tests

## 📁 Files

| File | Description |
|------|-------------|
| [`LAB-GUIDE.md`](LAB-GUIDE.md) | **Start here.** Step-by-step: subnetting by hand, VLSM, IPv6, running the tool, code explained, 4 challenges |
| [`addressing-plan.md`](addressing-plan.md) | Requirements, VLSM worksheet, IPv6 plan, 8 practice problems with answers |
| [`scripts/subnet_calc.py`](scripts/subnet_calc.py) | CLI subnet calculator (IPv4 + IPv6) |
| [`scripts/test_subnet_calc.py`](scripts/test_subnet_calc.py) | 22 unit tests, including one that checks the plan's VLSM table |

## 🚀 How to Run

```bash
cd 002-ipv4-ipv6-subnetting/scripts

python subnet_calc.py info 192.168.10.77/26
python subnet_calc.py info 192.168.10.77 255.255.255.192
python subnet_calc.py info 2001:db8:acad:10::1/64
python subnet_calc.py split 192.168.10.0/24 --prefix 26
python subnet_calc.py vlsm 172.16.0.0/22 HQ-SALES=200 HQ-IT=100 BR-SALES=50 BR-IT=25 MGMT=10 WAN-HQ-BR=2
python subnet_calc.py eui64 2001:db8:acad:10::/64 00:1A:2B:3C:4D:5E
python subnet_calc.py quiz --count 10
```

<details>
<summary><b>Sample output: <code>info 192.168.10.77/26</code></b></summary>

```
  Address         : 192.168.10.77  <- host address
  Network         : 192.168.10.64/26
  Subnet mask     : 255.255.255.192
  Wildcard mask   : 0.0.0.63
  Mask (binary)   : 11111111.11111111.11111111.11000000
  Broadcast       : 192.168.10.127
  First usable    : 192.168.10.65
  Last usable     : 192.168.10.126
  Total addresses : 64
  Usable hosts    : 62
  Block size      : 64 (octet 4)
  Class           : C (default /24)
  Type            : Private (RFC 1918)
```
</details>

<details>
<summary><b>Sample output: <code>vlsm 172.16.0.0/22 ...</code></b></summary>

```
Name       Need  Usable  Subnet           Mask             Usable range                 Broadcast
----------------------------------------------------------------------------------------------------
HQ-SALES   200   254     172.16.0.0/24    255.255.255.0    172.16.0.1 - 172.16.0.254    172.16.0.255
HQ-IT      100   126     172.16.1.0/25    255.255.255.128  172.16.1.1 - 172.16.1.126    172.16.1.127
BR-SALES   50    62      172.16.1.128/26  255.255.255.192  172.16.1.129 - 172.16.1.190  172.16.1.191
BR-IT      25    30      172.16.1.192/27  255.255.255.224  172.16.1.193 - 172.16.1.222  172.16.1.223
MGMT       10    14      172.16.1.224/28  255.255.255.240  172.16.1.225 - 172.16.1.238  172.16.1.239
WAN-HQ-BR  2     2       172.16.1.240/30  255.255.255.252  172.16.1.241 - 172.16.1.242  172.16.1.243

Free for growth: 172.16.1.244/30, 172.16.1.248/29, 172.16.2.0/23
```
</details>

<details>
<summary><b>Sample output: <code>eui64 2001:db8:acad:10::/64 00:1A:2B:3C:4D:5E</code></b></summary>

```
  1. MAC address   : 00:1a:2b:3c:4d:5e
  2. Split in half : 001a2b | 3c4d5e
  3. Insert FFFE   : 001a2b fffe 3c4d5e
  4. Flip 7th bit  : 00000000 -> 00000010  (00 -> 02)
  5. Interface ID  : 021a:2bff:fe3c:4d5e
  6. Prefix + ID   : 2001:db8:acad:10:21a:2bff:fe3c:4d5e
```
</details>

## ✅ Verification

```bash
cd 002-ipv4-ipv6-subnetting
python -m unittest discover -s scripts -v
```
Expected: `Ran 22 tests ... OK`. One test rebuilds the VLSM table from `addressing-plan.md`,
so if the plan and the code ever disagree, the test fails.

## 🧠 Key Concepts

- **Block size ("magic number") = 256 − interesting mask octet.** /26 → 256 − 192 = 64, so subnets start at .0, .64, .128, .192.
- **Usable hosts = 2ʰ − 2** (network + broadcast reserved). Exceptions: /31 point-to-point = 2 (RFC 3021), /32 = 1.
- **VLSM, largest first.** Allocating big blocks first keeps every subnet aligned on its boundary.
- **Wildcard mask = 255.255.255.255 − subnet mask.** Used in ACLs and OSPF `network` statements.
- **IPv6 LANs are always /64.** SLAAC and EUI-64 need a 64-bit interface ID. A /48 gives 65,536 LANs.
- **IPv6 compression:** drop leading zeros in each hextet, and replace the longest run of all-zero hextets with `::` once (leftmost on a tie).
- **EUI-64:** split the MAC, insert `FFFE`, flip the 7th (U/L) bit.

## 📝 My Notes

<!-- Which problems did you get wrong on the first try? What shortcut stuck? -->
-

## 🔗 References

- [RFC 1918](https://www.rfc-editor.org/rfc/rfc1918): Private IPv4 address space
- [RFC 4291](https://www.rfc-editor.org/rfc/rfc4291): IPv6 addressing architecture (EUI-64, Appendix A)
- [RFC 5952](https://www.rfc-editor.org/rfc/rfc5952): IPv6 text representation (compression rules)
- [RFC 3849](https://www.rfc-editor.org/rfc/rfc3849): IPv6 documentation prefix `2001:db8::/32`
- Python [`ipaddress`](https://docs.python.org/3/library/ipaddress.html) module docs
