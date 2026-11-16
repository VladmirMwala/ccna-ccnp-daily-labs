# 🌐 CCNA / CCNP Daily Networking Labs

> One networking project a day — configurations, automation scripts, and lab guides
> documenting my path from **CCNA** to **CCNP Enterprise**.

![Projects](https://img.shields.io/badge/projects-0-blue)
![Track](https://img.shields.io/badge/track-CCNA%20%E2%86%92%20CCNP-0a7cbf)
![Started](https://img.shields.io/badge/started-2026--11--16-lightgrey)

**Author:** Vladmir Mwala · [GitHub](https://github.com/VladmirMwala)

---

## 📌 About This Repository

Each folder is a self-contained lab with:

- **Configs / scripts / lab guide** — clean, commented, and sanitized
- **`README.md`** — objective, topology, tools used, and how to run/verify it
- **Topology diagram** (when applicable) — in the project's `topology/` folder

## 🧭 Table of Contents

| #   | Date       | Project | Track | Topics | Tools |
|-----|------------|---------|-------|--------|-------|
<!-- NEW PROJECTS GO BELOW THIS LINE — newest at the bottom -->

## 📈 Progress by Exam Domain

### CCNA 200-301

| Domain | Weight | Projects |
|--------|--------|----------|
| 1.0 Network Fundamentals | 20% | — |
| 2.0 Network Access (VLANs, STP, EtherChannel, Wireless) | 20% | — |
| 3.0 IP Connectivity (Static, OSPF, FHRP) | 25% | — |
| 4.0 IP Services (NAT, DHCP, NTP, SNMP, QoS) | 10% | — |
| 5.0 Security Fundamentals (ACLs, Port Security, AAA) | 15% | — |
| 6.0 Automation & Programmability | 10% | — |

### CCNP Enterprise — ENCOR 350-401 / ENARSI 300-410

| Domain | Projects |
|--------|----------|
| Architecture (SD-WAN, SD-Access, QoS design) | — |
| Virtualization (VRF, GRE, IPsec, LISP/VXLAN) | — |
| Infrastructure (EIGRP, OSPF, BGP, redistribution, PBR) | — |
| Network Assurance (NetFlow, SPAN, IP SLA, Syslog) | — |
| Security (CoPP, uRPF, AAA/TACACS+, 802.1X) | — |
| Automation (Python, RESTCONF/NETCONF, Ansible, EEM) | — |

## 🗂️ Repository Structure

```
.
├── README.md                     # You are here — index of all projects
├── .gitignore                    # Blocks secrets, raw configs, IOS images, captures
├── .env.example                  # Template for automation credentials (copy to .env)
├── _templates/
│   └── PROJECT_README.md         # Copy into every new project folder
├── tools/
│   └── Check-Secrets.ps1         # Pre-push scan for passwords, keys & public IPs
└── NNN-project-name/             # One folder per daily project
    ├── README.md
    ├── configs/                  # Sanitized device configs (R1.cfg, SW1.cfg …)
    ├── scripts/                  # Python / Ansible automation
    └── topology/                 # Diagrams (.png/.drawio), .pkt / .unl / CML YAML
```

## 🔐 Security & Sanitization Policy

Everything here is safe to publish:

| Real value | Replaced with |
|------------|---------------|
| Passwords / secrets / PSKs / SNMP communities | `<REDACTED>` or `ChangeMe123!` (labs only) |
| Type 5/7/8/9 password hashes | `<REDACTED_HASH>` |
| API keys / tokens | Loaded from `.env` (never committed) |
| Public / work / ISP IP addresses | RFC 5737 documentation ranges: `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` |
| Public ASNs | Private ASNs `64512–65534` |
| Hostnames / domains of real orgs | `example.com`, `lab.local` |

Lab-internal RFC 1918 addresses (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) are kept as-is.

Run the scan before every push:

```powershell
.\tools\Check-Secrets.ps1
```

## 🛠️ Lab Environment

| Tool | Use |
|------|-----|
| Cisco Packet Tracer | CCNA fundamentals |
| GNS3 / EVE-NG / CML | CCNP routing, multi-vendor labs |
| Python 3 (Netmiko, NAPALM, Nornir) | Automation |
| Ansible | Config management |
| Wireshark | Protocol analysis |

## 📜 License

Lab content is shared for learning purposes under the [MIT License](LICENSE).
