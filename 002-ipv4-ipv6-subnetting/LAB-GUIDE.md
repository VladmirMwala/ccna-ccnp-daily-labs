# 002 — Step-by-Step Lab Guide: Subnetting by Hand + the Python Calculator Explained

Work through this in order. Parts 1–3 teach the math with pen and paper. Part 4 checks
your answers with the tool. Parts 5–7 explain the code line by line and give you
challenges to extend it yourself.

| Part | What you'll do | Time |
|------|----------------|------|
| 0 | Set up Python and open a terminal | 5 min |
| 1 | IPv4 subnetting by hand (the 6-step method) | 20 min |
| 2 | VLSM by hand | 15 min |
| 3 | IPv6: compress, expand, plan, EUI-64 | 15 min |
| 4 | Run the calculator and check your answers | 10 min |
| 5 | Code walkthrough | 30 min |
| 6 | Run and read the tests | 10 min |
| 7 | Extend it: 4 coding challenges | your pace |
| 8 | Push to GitHub | 5 min |

---

## Part 0 — Setup

1. Check Python (3.10 or newer) in PowerShell:
   ```bash
   python --version
   ```
   If it isn't installed, get it from [python.org](https://www.python.org/downloads/) and tick
   **"Add python.exe to PATH"** during setup.
2. Go to the scripts folder:
   ```bash
   cd "M:\LEARNING CENTER\VLADMIR_CCNA_CCNP PROJECTS\002-ipv4-ipv6-subnetting\scripts"
   ```
3. Smoke test:
   ```bash
   python subnet_calc.py --help
   ```
   You should see the five commands: `info`, `split`, `vlsm`, `eui64` and `quiz`.

> Get a sheet of paper. Parts 1–3 only stick if you write them out.

---

## Part 1 — IPv4 Subnetting by Hand

### Memorize these two rows

| Bits on in the octet | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|----------------------|---|---|---|---|---|---|---|---|
| **Mask octet value** | 128 | 192 | 224 | 240 | 248 | 252 | 254 | 255 |
| **Block size** (256 − value) | 128 | 64 | 32 | 16 | 8 | 4 | 2 | 1 |

Every subnetting question is these two rows plus the six steps below.

### The 6-step method

**Worked example: `192.168.10.77/26`**

| Step | Do this | Result |
|------|---------|--------|
| 1. **Mask** | 26 bits = 8+8+8+**2**. Two bits on in octet 4 → 192 | `255.255.255.192` |
| 2. **Interesting octet** | The octet where the mask isn't 255 or 0 | Octet **4** |
| 3. **Block size** | 256 − 192 | **64** |
| 4. **Network** | Count in blocks: 0, 64, 128, 192. The host's 77 falls in 64–127 | `192.168.10.64` |
| 5. **Broadcast** | Next network − 1 = 128 − 1 | `192.168.10.127` |
| 6. **Usable range / hosts** | Network+1 → broadcast−1. Hosts = 2^(32−26) − 2 = 2⁶ − 2 | `.65 – .126`, **62 hosts** |

**Worked example 2, interesting octet = 3: `10.20.37.200/21`**

| Step | Result |
|------|--------|
| 1. Mask | 21 = 8+8+**5** → 248 in octet 3 → `255.255.248.0` |
| 2–3. Block | 256 − 248 = **8** in octet 3 |
| 4. Network | 0, 8, 16, 24, **32**, 40… 37 falls in 32–39 → `10.20.32.0` |
| 5. Broadcast | Next network is 10.20.40.0, so subtract 1 → `10.20.39.255` |
| 6. Hosts | 2^(32−21) − 2 = 2¹¹ − 2 = **2,046** · usable `10.20.32.1 – 10.20.39.254` |

> When the interesting octet is 3, octet 4 is **0 in the network** and **255 in the broadcast**.

### Cheat sheet

| Prefix | Mask | Block | Usable hosts | | Prefix | Mask | Block (octet 3) | Usable hosts |
|--------|------|-------|--------------|-|--------|------|-----------------|--------------|
| /24 | .0 | 256 | 254 | | /17 | 255.255.128.0 | 128 | 32,766 |
| /25 | .128 | 128 | 126 | | /18 | 255.255.192.0 | 64 | 16,382 |
| /26 | .192 | 64 | 62 | | /19 | 255.255.224.0 | 32 | 8,190 |
| /27 | .224 | 32 | 30 | | /20 | 255.255.240.0 | 16 | 4,094 |
| /28 | .240 | 16 | 14 | | /21 | 255.255.248.0 | 8 | 2,046 |
| /29 | .248 | 8 | 6 | | /22 | 255.255.252.0 | 4 | 1,022 |
| /30 | .252 | 4 | 2 | | /23 | 255.255.254.0 | 2 | 510 |
| /31 | .254 | 2 | 2 (point-to-point) | | | | | |

**Wildcard mask** = 255.255.255.255 − mask. /26 → `0.0.0.63`. It's used in ACLs and OSPF.

### ✍️ Your turn

Solve problems **1–4** in [`addressing-plan.md`](addressing-plan.md#4-practice-problems)
on paper. Don't open the answers yet. You'll check them with the tool in Part 4.

---

## Part 2 — VLSM by Hand

**VLSM** (variable-length subnet masking) gives each segment a subnet sized to its needs,
instead of making every subnet the same size.

### Method

1. **List** the segments and the hosts each needs.
2. **Sort** them largest first.
3. **Size** each one: the smallest block where 2^h − 2 ≥ hosts.
4. **Allocate** from the start of the space. Each new subnet starts right after the previous broadcast.
5. **Record** what's left as free space.

### Worked example: LabCorp in `172.16.0.0/22`

| Order | Segment | Hosts | Fits in | Starts at (cursor) | Subnet | Next cursor |
|-------|---------|-------|---------|--------------------|--------|-------------|
| 1 | HQ-SALES | 200 | /24 (254) | 172.16.0.0 | 172.16.0.0/24 | 172.16.1.0 |
| 2 | HQ-IT | 100 | /25 (126) | 172.16.1.0 | 172.16.1.0/25 | 172.16.1.128 |
| 3 | BR-SALES | 50 | /26 (62) | 172.16.1.128 | 172.16.1.128/26 | 172.16.1.192 |
| 4 | BR-IT | 25 | /27 (30) | 172.16.1.192 | 172.16.1.192/27 | 172.16.1.224 |
| 5 | MGMT | 10 | /28 (14) | 172.16.1.224 | 172.16.1.224/28 | 172.16.1.240 |
| 6 | WAN | 2 | /30 (2) | 172.16.1.240 | 172.16.1.240/30 | 172.16.1.244 |

Free: `172.16.1.244` up to `172.16.3.255` → `172.16.1.244/30`, `172.16.1.248/29`, `172.16.2.0/23`.

**Why largest first?** A subnet must start on a multiple of its own block size. If you
placed the /30 first at `172.16.0.0`, the /24 couldn't start at `172.16.0.4`. It would
have to jump to `172.16.1.0`, wasting space. Going largest first keeps every block aligned
automatically.

### ✍️ Your turn

Solve problem **5** in `addressing-plan.md` on paper.

---

## Part 3 — IPv6

### Compression rules (RFC 5952)

1. Drop **leading zeros** in each hextet: `0db8` → `db8`, `0010` → `10`, `0000` → `0`.
2. Replace the **longest run** of two or more all-zero hextets with `::`, **once**.
3. If two runs are the same length, compress the **leftmost** one.

`2001:0db8:0000:0000:00a0:0000:0000:0001`
→ rule 1: `2001:db8:0:0:a0:0:0:1`
→ rules 2–3, two runs of two, take the left one: **`2001:db8::a0:0:0:1`**

### Expanding

Count the hextets you can see. `::` stands for the missing ones (8 − visible).
`2001:db8:acad::10:1` shows 5 hextets → `::` = 3 zero hextets →
`2001:0db8:acad:0000:0000:0000:0010:0001`

### Planning: /48 → /64s

```
2001:db8:acad : 0010 : 0000:0000:0000:0001
└── /48 site ┘  └ID┘   └─ 64-bit interface ID ─┘
```
- 16 bits of subnet ID → 2¹⁶ = **65,536** LANs per site.
- Every LAN is a **/64**. SLAAC and EUI-64 need exactly 64 bits of interface ID.
- Reusing the VLAN number as the subnet ID (`VLAN 20 → :20::/64`) makes the plan readable.

### EUI-64 (MAC → interface ID)

MAC `00:1A:2B:3C:4D:5E`, prefix `2001:db8:acad:10::/64`:

| Step | Result |
|------|--------|
| 1. Split the MAC in half | `001A2B` \| `3C4D5E` |
| 2. Insert `FFFE` in the middle | `001A2B` **`FFFE`** `3C4D5E` |
| 3. Flip bit 7 of the first byte (U/L bit) | `00` = `0000 0000` → `0000 0010` = `02` |
| 4. Regroup into hextets | `021a:2bff:fe3c:4d5e` |
| 5. Add the prefix | **`2001:db8:acad:10:21a:2bff:fe3c:4d5e`** |

> Shortcut for step 3: if the second hex digit of the first byte is 0/1/4/5/8/9/C/D, **add 2**.
> If it's 2/3/6/7/A/B/E/F, **subtract 2**. Example: `0C` → `0E`.

### ✍️ Your turn

Solve problems **6–8** in `addressing-plan.md` on paper.

---

## Part 4 — Run the Calculator and Check Your Answers

For each problem, run the matching command and compare with your paper answer.

| Problem | Command |
|---------|---------|
| 1 | `python subnet_calc.py info 192.168.45.130/27` |
| 2 | `python subnet_calc.py info 10.20.37.200/21` |
| 3 | `python subnet_calc.py info 172.16.100.5 255.255.224.0` |
| 4 | `python subnet_calc.py vlsm 10.0.0.0/16 BIG=500` (look at the prefix it picks) |
| 5 | `python subnet_calc.py vlsm 192.168.50.0/24 A=60 B=28 C=12 WAN=2` |
| 6 | `python subnet_calc.py info 2001:0db8:0000:0000:00a0:0000:0000:0001/64` (see "Address") |
| 7 | `python subnet_calc.py info 2001:db8:acad::10:1/64` (see "Expanded") |
| 8 | `python subnet_calc.py eui64 2001:db8:acad:20::/64 0C9A.3E12.3456` |

Then explore:
```bash
python subnet_calc.py split 192.168.10.0/24 --prefix 27
python subnet_calc.py info 2001:db8:acad::/48
python subnet_calc.py info 169.254.10.5/16
python subnet_calc.py info 203.0.113.9/24
```

Finally, drill until it's automatic. Aim for 10/10 three times in a row:
```bash
python subnet_calc.py quiz --count 10
```

---

## Part 5 — Code Walkthrough

Open [`scripts/subnet_calc.py`](scripts/subnet_calc.py) beside this guide.

### 5.1 The big picture

```
main()                      <- reads the command line (argparse)
 ├─ info   → describe()     <- parse_interface, host_range, usable_hosts, block_size, address_type
 ├─ split  → split()
 ├─ vlsm   → parse_requirement() → vlsm() → prefix_for_hosts()
 ├─ eui64  → eui64()
 └─ quiz   → quiz()
print_pairs() / print_table()  <- the only functions that format output
```

**Design rule:** every command function *returns data* and only `main()` prints it. That
split is what makes the code easy to test (Part 6).

### 5.2 Python's `ipaddress` module does the heavy lifting

Try this in a Python shell (`python`, then type each line):
```python
>>> import ipaddress
>>> iface = ipaddress.ip_interface("192.168.10.77/26")
>>> iface.ip, iface.network
(IPv4Address('192.168.10.77'), IPv4Network('192.168.10.64/26'))
>>> n = iface.network
>>> n.netmask, n.hostmask, n.broadcast_address
(IPv4Address('255.255.255.192'), IPv4Address('0.0.0.63'), IPv4Address('192.168.10.127'))
>>> n.num_addresses
64
>>> n.network_address + 1          # addresses support math
IPv4Address('192.168.10.65')
>>> ipaddress.ip_network("192.168.10.77/26")
ValueError: 192.168.10.77/26 has host bits set
```

| Object | Meaning | Use it when |
|--------|---------|-------------|
| `ip_address("10.1.1.5")` | One address | Comparing or doing math on addresses |
| `ip_network("10.1.1.0/24")` | A subnet. Host bits must be 0 | You have a real network address |
| `ip_interface("10.1.1.5/24")` | Address + its subnet, like a router interface | The user typed a host address with a prefix |

That last error is why `describe()` uses **`ip_interface`**. Users type host addresses like
`192.168.10.77/26`, not network addresses.

### 5.3 Accepting both input styles: `parse_interface()`

```python
if " " in text:
    text = "/".join(text.split())
return ipaddress.ip_interface(text)
```
`"192.168.10.77 255.255.255.192"` becomes `"192.168.10.77/255.255.255.192"`, which
`ipaddress` accepts. So both CIDR and dotted-mask input work.

### 5.4 The CCNA rules in code: `usable_hosts()` and `host_range()`

```python
if net.version == 6:
    return net.num_addresses        # IPv6 has no broadcast
if net.prefixlen == 32:
    return 1                        # host route
if net.prefixlen == 31:
    return 2                        # point-to-point (RFC 3021)
return net.num_addresses - 2        # minus network + broadcast
```
This is the "2^h − 2" rule from Part 1, plus its two exceptions.

### 5.5 The block-size shortcut: `block_size()`

```python
octet = (p - 1) // 8              # which octet holds the last network bit (0-based)
bits_in_octet = p - 8 * octet     # how many network bits are in that octet
return 2 ** (8 - bits_in_octet), octet + 1
```
Trace it for **/26**: `octet = 25 // 8 = 3` (the 4th octet), `bits_in_octet = 26 − 24 = 2`,
`block = 2^(8−2) = 64`. This is the same as Part 1, step 3, done with bits instead of 256 − 192.

### 5.6 Sizing a subnet: `prefix_for_hosts()`

```python
for prefix in range(30, -1, -1):          # try /30, /29, /28 ... (smallest subnet first)
    if 2 ** (32 - prefix) - 2 >= hosts:
        return prefix
```
It walks from the smallest subnet upward and stops at the first one that fits, which is
exactly what you did on paper in Part 2, step 3.

### 5.7 VLSM: `vlsm()`

```python
ordered = sorted(requirements, key=lambda r: r[1], reverse=True)   # largest first
cursor = int(base.network_address)

for name, hosts in ordered:
    prefix = prefix_for_hosts(hosts)
    subnet = ipaddress.ip_network(f"{ipaddress.IPv4Address(cursor)}/{prefix}")
    if int(subnet.broadcast_address) > end:
        raise ValueError(...)                                         # ran out of space
    allocations.append((name, hosts, subnet))
    cursor = int(subnet.broadcast_address) + 1                        # next free address
```
- `sorted(..., key=lambda r: r[1], reverse=True)` sorts by the host count, biggest first.
- The **cursor** is an integer. IPv4 addresses are just 32-bit numbers, so "next address"
  is `+ 1`. This is the "Next cursor" column from the Part 2 table.
- Free space at the end uses `ipaddress.summarize_address_range()`, which turns a start–end
  range into the fewest CIDR blocks.

### 5.8 EUI-64 with bit operations: `eui64()`

```python
mac_bytes = bytearray.fromhex(digits)        # "001a2b3c4d5e" -> 6 bytes
mac_bytes[0] ^= 0x02                         # XOR flips bit 7 (0x02 = 0000 0010)
iid = bytes(mac_bytes[:3]) + b"\xff\xfe" + bytes(mac_bytes[3:])   # insert FFFE
address = ipaddress.IPv6Address(int(net.network_address) | int.from_bytes(iid, "big"))
```
- **`^` (XOR)** with `0x02` flips exactly one bit: 0→1 or 1→0. That's the U/L bit.
- **`|` (OR)** combines the prefix (top 64 bits) and the interface ID (bottom 64 bits),
  because the prefix's low bits are all 0.
- `re.sub(r"[^0-9a-fA-F]", "", mac)` strips `:`, `-` and `.`, so every MAC format works,
  including Cisco's `001a.2b3c.4d5e`.

### 5.9 The quiz, and why `ask=input`

```python
def quiz(count, rng=None, ask=input):
    ...
    reply = ask(f"   {label}: ")
```
Normally `ask` is Python's `input()`, which waits for you to type. A test can pass in a
fake function that returns the right answers instantly. This is called **dependency
injection**, and it's how you test interactive code. `random.Random(seed)` makes the
questions repeatable (`--seed 3` always gives the same quiz).

### 5.10 The command line: `build_parser()`

```python
sub = parser.add_subparsers(dest="command", required=True)
p = sub.add_parser("split", help="divide a network into equal subnets")
p.add_argument("network")
p.add_argument("--prefix", type=int, required=True)
```
Each `add_parser` creates a sub-command, like `git commit` or `git push`. `argparse` builds
`--help` for free and rejects bad input. `main()` catches `ValueError` and returns exit code
2, so a typo prints a clean error instead of a crash.

---

## Part 6 — The Tests

```bash
cd ..
python -m unittest discover -s scripts -v
```
Expected: `Ran 22 tests ... OK`.

| Test class | What it proves |
|------------|----------------|
| `TestIPv4Info` | Network, broadcast, masks, block size, /31 and /32, class and type |
| `TestIPv6` | Expansion, compression tie rule, link-local/ULA, EUI-64 in two MAC formats |
| `TestSplitAndVlsm` | Equal splits, host sizing, **the exact LabCorp plan**, out-of-space errors |
| `TestQuizAndCli` | The quiz scores right answers, and the CLI returns error code 2 on bad input |

The anatomy of a test:
```python
def test_host_in_slash26(self):
    info = sc.describe("192.168.10.77/26")              # 1. run the code
    self.assertEqual(info["Network"], "192.168.10.64/26")  # 2. check the result
```

**Try breaking it:** in `usable_hosts()`, change `- 2` to `- 1` and rerun the tests. Watch
which tests fail and why, then change it back. This is the fastest way to understand what a
test suite protects.

---

## Part 7 — Extend It Yourself

Each challenge is a real feature. Write the code, add a test, and commit it. This is where
the project becomes truly yours.

### Challenge 1 — `/31` point-to-point links ⭐
Add a `--p2p31` flag to `vlsm` so segments needing 2 hosts get a **/31** instead of a /30.
- Hint: add a parameter `allow_31: bool = False` to `prefix_for_hosts()`, and return 31 when `hosts == 2 and allow_31`.
- Pass the flag through `vlsm()` from `main()`.
- Test: `prefix_for_hosts(2, allow_31=True) == 31`.

### Challenge 2 — `wildcard` command ⭐
`python subnet_calc.py wildcard 192.168.10.64/26` should print:
```
Wildcard : 0.0.0.63
ACL      : access-list 10 permit 192.168.10.64 0.0.0.63
OSPF     : network 192.168.10.64 0.0.0.63 area 0
```
- Hint: `net.hostmask` is the wildcard. Add a sub-parser like `split`.

### Challenge 3 — `summarize` command (route summarization) ⭐⭐
`python subnet_calc.py summarize 192.168.0.0/24 192.168.1.0/24 192.168.2.0/24 192.168.3.0/24`
→ `192.168.0.0/22`
- Hint: `ipaddress.collapse_addresses()` merges contiguous networks.
- Bonus: if they don't collapse to one block, find the **smallest single supernet** that
  covers all of them (use `net.supernet()` in a loop until every network is inside it), and
  warn that it covers extra addresses.
- This is CCNP prep: EIGRP and OSPF summarization use the same math.

### Challenge 4 — IPv6 quiz mode ⭐⭐
Add `quiz --ipv6`, which shows a fully expanded address and asks for the compressed form
(and the reverse).
- Hint: build random addresses where some hextets are 0, so there's something to compress.
  `ipaddress.IPv6Address(...).compressed` and `.exploded` give you the answers.

---

## Part 8 — Push to GitHub

Fill in **📝 My Notes** in [`README.md`](README.md), especially which problems you got
wrong first and which shortcut finally clicked. Then, from the repo root:

```bash
.\tools\Check-Secrets.ps1
```
```bash
git add 002-ipv4-ipv6-subnetting/
```
```bash
git commit -m "Day 002: subnetting practice notes and calculator extensions"
```
```bash
git push origin main
```
