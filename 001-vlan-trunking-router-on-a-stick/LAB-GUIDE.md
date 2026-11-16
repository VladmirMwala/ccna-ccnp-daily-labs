# 001 — Step-by-Step Lab Guide (Cisco Packet Tracer)

Follow this from top to bottom. Every click and every command is here. After each part,
a ✅ **Checkpoint** tells you exactly what you should see before moving on.
If a checkpoint fails, stop and fix it first. Problems pile up quickly in networking.

**Time:** 90–120 minutes the first time · **You need:** Cisco Packet Tracer 8.x

| Part | What you'll do | Time |
|------|----------------|------|
| 0 | Prepare Packet Tracer | 5 min |
| 1 | Place the devices | 5 min |
| 2 | Cable everything | 5 min |
| 3 | Give the PCs IP addresses | 5 min |
| 4 | Basic setup on R1, SW1, SW2 | 10 min |
| 5 | Create the VLANs | 5 min |
| 6 | Assign access ports | 5 min |
| 7 | Build the 802.1Q trunks | 10 min |
| 8 | Configure router-on-a-stick | 10 min |
| 9 | Management VLAN on the switches | 5 min |
| 10 | Enable SSH | 10 min |
| 11 | Lock down unused ports | 5 min |
| 12 | Save + full verification | 10 min |
| 13 | Troubleshooting practice | 20 min |
| 14 | Push your work to GitHub | 5 min |

---

## Part 0 — Prepare Packet Tracer

1. Open Packet Tracer and check the version: **Help → About**. Any 8.x is fine.
2. Turn on port labels so you can see interface names on the cables:
   **Options → Preferences → Interface tab → tick "Always Show Port Labels in Logical Workspace"**.
3. Your lab file goes in this project's own `topology` folder (it already exists):
   `M:\LEARNING CENTER\VLADMIR_CCNA_CCNP PROJECTS\001-vlan-trunking-router-on-a-stick\topology\`
4. **File → Save As →** `001-vlan-roas.pkt` in that folder. Press **Ctrl+S** after every part.

### CLI survival kit

| Key / command | What it does |
|---------------|--------------|
| `?` | Lists what you can type next (e.g. `switchport ?`) |
| **Tab** | Completes a command (`conf` + Tab → `configure`) |
| **↑ arrow** | Recalls the previous command |
| `do show ...` | Runs a `show` command without leaving config mode |
| `end` | Jumps straight back to `#` (privileged EXEC) |
| `exit` | Goes up one level |

| Prompt | Mode | How you got there |
|--------|------|-------------------|
| `R1>` | User EXEC | Starting point |
| `R1#` | Privileged EXEC | `enable` |
| `R1(config)#` | Global config | `configure terminal` |
| `R1(config-if)#` | Interface config | `interface g0/0/0` |
| `R1(config-subif)#` | Subinterface config | `interface g0/0/0.10` |
| `R1(config-line)#` | Line config | `line vty 0 4` |

> **`% Invalid input detected at '^' marker`** means a typo or the wrong mode. The `^` points at the problem.

---

## Part 1 — Place the devices

The device picker is in the **bottom-left corner**. The top row holds categories and the bottom row holds the models.

1. **Router:** click **Network Devices** → **Routers** → drag a **4331** into the workspace.
2. **Switches:** **Network Devices** → **Switches** → drag a **2960** in, twice.
3. **PCs:** **End Devices** → drag a **PC** in, four times.
4. **Rename the labels:** click the text under each device (for example `Router0`) and type the new name:

   | Default label | Rename to |
   |---------------|-----------|
   | Router0 | **R1** |
   | Switch0 | **SW1** |
   | Switch1 | **SW2** |
   | PC0, PC1, PC2, PC3 | **PC1, PC2, PC3, PC4** |

5. Arrange them like this:
   ```
                    R1
                    |
          SW1 ------------- SW2
         /   \             /   \
       PC1   PC2         PC3   PC4
   ```

> Renaming the label only changes the picture. The device's **hostname** is set in the CLI in Part 4.

---

## Part 2 — Cable everything

1. Click **Connections** (the ⚡ lightning-bolt icon, bottom-left).
2. Pick **Copper Straight-Through** (the solid black line).
3. For each row: click the first device, choose its port from the pop-up, then click the second device and choose its port.

| # | From | Port | To | Port |
|---|------|------|----|------|
| 1 | R1 | GigabitEthernet0/0/0 | SW1 | GigabitEthernet0/1 |
| 2 | SW1 | GigabitEthernet0/2 | SW2 | GigabitEthernet0/2 |
| 3 | PC1 | FastEthernet0 | SW1 | FastEthernet0/1 |
| 4 | PC2 | FastEthernet0 | SW1 | FastEthernet0/2 |
| 5 | PC3 | FastEthernet0 | SW2 | FastEthernet0/1 |
| 6 | PC4 | FastEthernet0 | SW2 | FastEthernet0/2 |

> Wrong port? Click the cable, press **Delete**, and redo it.

✅ **Checkpoint: link lights**

| Light | Meaning | Expected now |
|-------|---------|--------------|
| 🔴 Red | Down | **Both ends of cable 1**: router ports start shut down, so the link stays down |
| 🟠 Orange | Spanning tree is still learning | Switch ports for the first ~30 s |
| 🟢 Green | Forwarding | All other links, after ~30 s |

Speed it up: click **Fast Forward Time** (bottom-right, next to the clock) two or three times.

---

## Part 3 — Give the PCs IP addresses

Click **PC1 → Desktop tab → IP Configuration → Static**, then type:

| PC | IPv4 Address | Subnet Mask | Default Gateway |
|----|--------------|-------------|-----------------|
| PC1 | 192.168.10.11 | 255.255.255.0 | 192.168.10.1 |
| PC2 | 192.168.20.12 | 255.255.255.0 | 192.168.20.1 |
| PC3 | 192.168.10.13 | 255.255.255.0 | 192.168.10.1 |
| PC4 | 192.168.20.14 | 255.255.255.0 | 192.168.20.1 |

Close the window (the values save automatically) and repeat for each PC.

✅ **Checkpoint:** PC1 → **Desktop → Command Prompt** → type `ipconfig`. You should see `192.168.10.11` and gateway `192.168.10.1`.

> The gateways don't exist yet. R1 provides them in Part 8.

---

## Part 4 — Basic setup on R1, SW1 and SW2

### 4a. R1

Click **R1 → CLI tab**. If you're asked:
```
Would you like to enter the initial configuration dialog? [yes/no]:
```
type `no` and press **Enter**, then press **Enter** again to get the `Router>` prompt.

Pick **one lab password** you'll remember. Type it everywhere you see `<REDACTED>` in this guide.
Never put your real password in GitHub. The repo files keep `<REDACTED>`.

```
enable
configure terminal
hostname R1
no ip domain-lookup
ip domain-name lab.local
enable secret <REDACTED>
username admin privilege 15 secret <REDACTED>
service password-encryption
banner motd # Authorized access only. All activity is monitored. #
line console 0
 exec-timeout 5 0
 logging synchronous
 login local
 exit
end
```

| Command | Why |
|---------|-----|
| `hostname R1` | Names the device, and the prompt changes to `R1` |
| `no ip domain-lookup` | A typo like `shwo` won't freeze the CLI for 30 s while it tries DNS |
| `ip domain-name lab.local` | Required later to create SSH keys |
| `enable secret` | Password for `enable`, stored as a hash |
| `username admin ... secret` | A local user account for console and SSH logins |
| `service password-encryption` | Hides any plain-text passwords in the config |
| `banner motd` | Legal warning shown at login |
| `exec-timeout 5 0` | Logs out after 5 idle minutes |
| `logging synchronous` | Log messages stop interrupting what you're typing |
| `login local` | Console now asks for the username and password |

> ⚠️ `login local` locks the console with the `admin` account. Make sure you remember the password.

### 4b. SW1 and SW2

Click **SW1 → CLI**, press **Enter**, and paste the same block with **`hostname SW1`**.
Then do **SW2** with **`hostname SW2`**.

✅ **Checkpoint:** On each device, type `exit` and press Enter. You should see the banner,
then `Username:`. Log in as `admin` with your password. The prompt is `R1#`, `SW1#` or `SW2#`.

---

## Part 5 — Create the VLANs (SW1 and SW2)

Run this on **both** switches:

```
configure terminal
vtp mode transparent
vlan 10
 name SALES
vlan 20
 name IT
vlan 99
 name MGMT
vlan 998
 name PARKING
vlan 999
 name NATIVE
end
```

| VLAN | Purpose |
|------|---------|
| 10 SALES / 20 IT | User networks |
| 99 MGMT | Switch management addresses |
| 998 PARKING | A dead-end home for unused ports |
| 999 NATIVE | Untagged traffic on trunks. Nothing lives here |

> **`vtp mode transparent`** keeps each switch's VLAN list local. A misconfigured switch
> elsewhere can't push changes in and wipe your VLANs.

✅ **Checkpoint:** `show vlan brief` lists VLANs 10, 20, 99, 998 and 999. They have no ports yet.

---

## Part 6 — Assign access ports

**SW1:**
```
configure terminal
interface FastEthernet0/1
 description PC1 - SALES
 switchport mode access
 switchport access vlan 10
interface FastEthernet0/2
 description PC2 - IT
 switchport mode access
 switchport access vlan 20
end
```

**SW2:** paste the same block, changing the descriptions to `PC3 - SALES` and `PC4 - IT`.

✅ **Checkpoint:** `show vlan brief` on SW1:
```
VLAN Name                             Status    Ports
---- -------------------------------- --------- -------------------------------
1    default                          active    Fa0/3, Fa0/4, ... Gig0/1, Gig0/2
10   SALES                            active    Fa0/1
20   IT                               active    Fa0/2
...
```

🧪 **Try this, it should fail:** from PC1's Command Prompt, `ping 192.168.10.13` (PC3).
PC1 and PC3 are both in VLAN 10, so why does it fail? The SW1–SW2 link is still a plain access
link in VLAN 1, so VLAN 10 frames can't cross it. Part 7 fixes this.

---

## Part 7 — Build the 802.1Q trunks

**SW1** (two trunks: to R1 and to SW2):
```
configure terminal
interface GigabitEthernet0/1
 description TRUNK to R1 G0/0/0
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,99,999
interface GigabitEthernet0/2
 description TRUNK to SW2 G0/2
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,99,999
end
```

**SW2** (one trunk to SW1):
```
configure terminal
interface GigabitEthernet0/2
 description TRUNK to SW1 G0/2
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,99,999
end
```

| Command | Why |
|---------|-----|
| `switchport mode trunk` | Carries many VLANs, each frame tagged with its VLAN ID (802.1Q) |
| `switchport nonegotiate` | Turns off DTP, so nothing can negotiate a trunk with this port |
| `native vlan 999` | Untagged frames go to an unused VLAN instead of VLAN 1 (blocks VLAN hopping) |
| `allowed vlan 10,20,99,999` | Only the VLANs we need cross the link |

> 💬 Between configuring SW1 and SW2 you'll see
> `%CDP-4-NATIVE_VLAN_MISMATCH ... (999), with SW2 ... (1)`. That's expected. The two ends
> disagree until SW2 is done, and then the messages stop.

✅ **Checkpoint:** on SW1, `show interfaces trunk`:
```
Port        Mode         Encapsulation  Status        Native vlan
Gig0/2      on           802.1q         trunking      999
```
Gig0/1 (toward R1) is missing because R1's port is still shut down. It appears in Part 8.

🧪 **Now test:**
- PC1 → `ping 192.168.10.13` (PC3) → ✅ **works.** Same VLAN, crossing the trunk.
- PC1 → `ping 192.168.20.12` (PC2) → ❌ **fails.** A different VLAN needs a router.

> The first ping often shows one `Request timed out` while ARP resolves. That's normal.

---

## Part 8 — Configure router-on-a-stick (R1)

```
configure terminal
interface GigabitEthernet0/0/0
 description TRUNK to SW1 G0/1 (802.1Q)
 no ip address
 no shutdown
interface GigabitEthernet0/0/0.10
 description GATEWAY - VLAN 10 SALES
 encapsulation dot1Q 10
 ip address 192.168.10.1 255.255.255.0
interface GigabitEthernet0/0/0.20
 description GATEWAY - VLAN 20 IT
 encapsulation dot1Q 20
 ip address 192.168.20.1 255.255.255.0
interface GigabitEthernet0/0/0.99
 description GATEWAY - VLAN 99 MGMT
 encapsulation dot1Q 99
 ip address 192.168.99.1 255.255.255.0
interface GigabitEthernet0/0/0.999
 description NATIVE VLAN 999 - no IP by design
 encapsulation dot1Q 999 native
end
```

| Command | Why |
|---------|-----|
| `no shutdown` on the physical port | Router ports start disabled. The subinterfaces inherit this state |
| `interface g0/0/0.10` | A logical slice of one physical port. The `.10` is just a label |
| `encapsulation dot1Q 10` | **This** is what binds the subinterface to VLAN 10. It must come before the IP |
| `ip address 192.168.10.1 ...` | The default gateway for every host in VLAN 10 |
| `dot1Q 999 native` | Untagged frames from the switch land here and go nowhere |

> If Packet Tracer rejects `encapsulation dot1Q 999 native`, skip that subinterface. It's
> best practice, not required for the lab to work.

✅ **Checkpoint:** on R1, `show ip interface brief`:
```
Interface                IP-Address      OK? Method Status                Protocol
GigabitEthernet0/0/0     unassigned      YES unset  up                    up
GigabitEthernet0/0/0.10  192.168.10.1    YES manual up                    up
GigabitEthernet0/0/0.20  192.168.20.1    YES manual up                    up
GigabitEthernet0/0/0.99  192.168.99.1    YES manual up                    up
```
On SW1, `show interfaces trunk` now lists **Gig0/1** and **Gig0/2**.

🧪 **Test inter-VLAN routing** from PC1's Command Prompt:
```
ping 192.168.10.1
ping 192.168.20.12
ping 192.168.20.14
tracert 192.168.20.14
```
Expected `tracert` result: hop 1 = `192.168.10.1` (R1), hop 2 = `192.168.20.14` (PC4).
**🎉 Inter-VLAN routing works.**

---

## Part 9 — Management VLAN on the switches

Every switch gets a management IP in VLAN 99, so you can reach it over the network.

**SW1:**
```
configure terminal
interface Vlan1
 no ip address
 shutdown
interface Vlan99
 description MGMT SVI
 ip address 192.168.99.11 255.255.255.0
 no shutdown
exit
ip default-gateway 192.168.99.1
end
```

**SW2:** the same, but with **`ip address 192.168.99.12 255.255.255.0`**.

| Command | Why |
|---------|-----|
| `interface Vlan99` | An SVI: a virtual interface the switch uses to talk IP itself |
| `shutdown` on Vlan1 | Nothing should be managed through the default VLAN |
| `ip default-gateway` | A Layer 2 switch doesn't route, so this is how it answers PCs in other subnets |

✅ **Checkpoint:**
- On SW1, `show ip interface brief` → `Vlan99  192.168.99.11 ... up  up`
  - `down/down` means VLAN 99 doesn't exist or isn't allowed on the trunk.
- PC1 → `ping 192.168.99.11` and `ping 192.168.99.12` → both reply.

---

## Part 10 — Enable SSH (R1, SW1, SW2)

**R1:**
```
configure terminal
crypto key generate rsa general-keys modulus 2048
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3
line vty 0 4
 exec-timeout 5 0
 logging synchronous
 login local
 transport input ssh
end
```

**SW1 and SW2:** the same block, but use **`line vty 0 15`**, because switches have 16 VTY lines.

> If `crypto key generate rsa general-keys modulus 2048` errors, type
> `crypto key generate rsa`, then enter `2048` when it asks
> `How many bits in the modulus [512]:`.
> SSH version 2 needs a key of at least 768 bits.

| Command | Why |
|---------|-----|
| `crypto key generate rsa` | Creates the key pair SSH encrypts with (needs hostname + domain-name) |
| `ip ssh version 2` | v1 has known weaknesses |
| `login local` on VTY | Remote logins use the `admin` account |
| `transport input ssh` | Only SSH is accepted. Telnet sends passwords in clear text |

✅ **Checkpoint:** from PC1 → **Desktop → Command Prompt**:
```
ssh -l admin 192.168.99.11
```
Enter your password and you should land on `SW1#`. Type `exit`. Then try:
```
telnet 192.168.99.11
```
→ the connection is **refused**. That's the goal.

Also try `ssh -l admin 192.168.10.1` to reach R1.

---

## Part 11 — Lock down unused ports

**SW1:**
```
configure terminal
interface range FastEthernet0/3 - 24
 description UNUSED - parked
 switchport mode access
 switchport access vlan 998
 shutdown
end
```

**SW2** (G0/1 isn't used on this switch either):
```
configure terminal
interface range FastEthernet0/3 - 24, GigabitEthernet0/1
 description UNUSED - parked
 switchport mode access
 switchport access vlan 998
 shutdown
end
```

**R1:**
```
configure terminal
interface GigabitEthernet0/0/1
 description UNUSED
 shutdown
interface GigabitEthernet0/0/2
 description UNUSED
 shutdown
end
```

**Why:** if someone plugs a laptop into a spare port, it's disabled. Even if it's turned
back on, the port is in a VLAN with no gateway and nothing else in it.

✅ **Checkpoint:** `show vlan brief` → Fa0/3–24 are in VLAN 998. `show interfaces status` → those ports show `disabled`.

---

## Part 12 — Save and run the full verification

On **each device**:
```
write memory
```
Then save the Packet Tracer file: **Ctrl+S**.

> The running-config lives in RAM and is lost on reboot. `write memory` copies it to the
> startup-config in NVRAM. `copy running-config startup-config` does the same thing.

### Final test sheet: tick each one

| # | Where | Command | Expected | ✔ |
|---|-------|---------|----------|---|
| 1 | SW1, SW2 | `show vlan brief` | Fa0/1 → 10, Fa0/2 → 20, spare ports → 998 | ☐ |
| 2 | SW1, SW2 | `show interfaces trunk` | Mode `on`, native `999`, allowed `10,20,99,999` | ☐ |
| 3 | SW1 | `show interfaces g0/1 switchport` | `Negotiation of Trunking: Off` | ☐ |
| 4 | R1 | `show ip interface brief` | G0/0/0 and .10/.20/.99 up/up, G0/0/1-2 admin down | ☐ |
| 5 | PC1 | `ping 192.168.10.13` | Replies (same VLAN) | ☐ |
| 6 | PC1 | `ping 192.168.20.14` | Replies (routed) | ☐ |
| 7 | PC1 | `tracert 192.168.20.14` | Hop 1 = 192.168.10.1 | ☐ |
| 8 | PC1 | `ssh -l admin 192.168.99.11` | Logs into SW1 | ☐ |
| 9 | PC1 | `telnet 192.168.99.11` | Refused | ☐ |
| 10 | All | `show running-config` | Matches the files in [`configs/`](configs/) | ☐ |

**All ten ticked? The lab is complete.** Save the file one more time.

---

## Part 13 — Troubleshooting practice

1. Make sure the working lab is saved (**Ctrl+S**).
2. Open [`troubleshooting.md`](troubleshooting.md) and do the three tickets one at a time:
   break it → diagnose with `show` commands only → fix → confirm.
3. When you're done, **close Packet Tracer without saving**, or reopen `001-vlan-roas.pkt`,
   to get back to the clean version.

> Write down how long each ticket took you in "My Notes". It's a good way to track progress.

---

## Part 14 — Push your work to GitHub

1. Check the `.pkt` file is in `001-vlan-trunking-router-on-a-stick\topology\`.
2. Open [`README.md`](README.md) and fill in **📝 My Notes**: what broke, what surprised you, and what clicked.
3. In a terminal at the repo root:

```bash
.\tools\Check-Secrets.ps1
```
```bash
git add 001-vlan-trunking-router-on-a-stick/
```
```bash
git commit -m "Day 001: add Packet Tracer topology and lab notes"
```
```bash
git push origin main
```

---

## Appendix — Common errors and fixes

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `% Invalid input detected at '^'` | Typo, or the wrong mode | Check the prompt. Use `?` |
| `% Incomplete command` | Missing a value | Add the rest, e.g. `vlan 10` not `vlan` |
| R1 end of cable stays red | Port is shut down | `interface g0/0/0` → `no shutdown` |
| Same-VLAN ping fails across switches | Not a trunk, or VLAN not allowed | `show interfaces trunk` on **both** switches |
| PC can't ping its gateway | Wrong PC gateway, access VLAN, allowed list or subinterface tag | Work from the PC toward R1 |
| `Vlan99` is down/down | VLAN 99 not created, or not on the trunk | `show vlan brief` and `show interfaces trunk` |
| `% Please define a domain-name first` | Missing `ip domain-name` | `ip domain-name lab.local`, then generate keys |
| SSH `Connection refused` | No RSA keys, or VTY not set up | `show ip ssh` → should say `SSH Enabled - version 2.0` |
| Locked out of the console | Forgot the password | Reopen your last saved `.pkt` file |
| CDP native VLAN mismatch spam | Native VLAN differs on the two ends | `switchport trunk native vlan 999` on both ends |
