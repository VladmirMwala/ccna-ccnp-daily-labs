# NNN — Project Title

| Date | Track | Exam Topic | Difficulty | Est. Time |
|------|-------|------------|------------|-----------|
| YYYY-MM-DD | CCNA / ENCOR / ENARSI | e.g. 3.4 OSPFv2 | ⭐⭐☆☆☆ | 45 min |

## 🎯 Objective

One or two sentences: what this lab builds and the skill it proves.

- [ ] Goal 1
- [ ] Goal 2
- [ ] Goal 3

## 🗺️ Topology

```
        [R1] G0/0 ------- G0/0 [R2]
         |                      |
       G0/1                   G0/1
         |                      |
       [SW1]                  [SW2]
         |                      |
       PC1                    PC2
```

Diagram file: [`topology/topology.png`](topology/topology.png)

### Addressing Table

| Device | Interface | IP Address | Subnet Mask | Gateway |
|--------|-----------|------------|-------------|---------|
| R1 | G0/0 | 10.0.12.1 | 255.255.255.252 | — |
| R2 | G0/0 | 10.0.12.2 | 255.255.255.252 | — |
| PC1 | NIC | 192.168.10.10 | 255.255.255.0 | 192.168.10.1 |

## 🧰 Tools & Platform

- **Simulator:** Packet Tracer 8.x / GNS3 / EVE-NG / CML
- **Images:** IOSv 15.9 / IOSvL2 / CSR1000v (images are not included in this repo)
- **Automation:** Python 3.x, Netmiko (if applicable)

## 📁 Files

| File | Description |
|------|-------------|
| `configs/R1.cfg` | Sanitized final config for R1 |
| `scripts/deploy.py` | Pushes configs with Netmiko |
| `topology/lab.pkt` | Packet Tracer file |

## 🚀 How to Run

1. Build the topology above (or open `topology/lab.pkt`).
2. Paste each file from `configs/` into the matching device, **or** run:
   ```bash
   cp ../.env.example .env      # fill in lab credentials
   python scripts/deploy.py
   ```
3. Run the verification steps below.

## ✅ Verification

| Command | Expected Result |
|---------|-----------------|
| `show ip interface brief` | All lab interfaces `up/up` |
| `show ip route` | Remote LANs learned via ... |
| `ping 192.168.20.10 source g0/1` | `!!!!!` (100% success) |

## 🧠 Key Takeaways

- What I learned / what surprised me
- Common mistake I hit and how I fixed it

## 🔗 References

- Cisco documentation link
- RFC / study guide chapter
