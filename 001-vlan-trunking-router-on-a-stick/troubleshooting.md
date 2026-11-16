# 001 — Troubleshooting Challenges

Build the working lab first and save a copy. Then break it with the **"Break it"**
commands, and fix it using only `show` commands before you open the solution.

---

## Ticket 1 — "Everything works, but the switch console keeps complaining"

**Break it (SW2):**
```
interface GigabitEthernet0/2
 switchport trunk native vlan 1
```

**Reported symptom:** Users can still reach each other, but SW1 and SW2 log a stream of
CDP messages.

<details>
<summary>💡 Hint</summary>

Compare the trunk settings on **both** ends of the SW1–SW2 link.
</details>

<details>
<summary>✅ Solution</summary>

**Diagnose:**
```
SW1# show interfaces trunk
SW2# show interfaces trunk
```
`Native vlan` is 999 on SW1 G0/2 and 1 on SW2 G0/2. CDP reports:
`%CDP-4-NATIVE_VLAN_MISMATCH: Native VLAN mismatch discovered on GigabitEthernet0/2 (1), with SW1 GigabitEthernet0/2 (999).`

**Fix (SW2):**
```
interface GigabitEthernet0/2
 switchport trunk native vlan 999
```

**Why it matters:** Tagged VLANs (10, 20, 99) keep working, which is why this fault is easy
to miss. Untagged frames sent in VLAN 999 on one side arrive in VLAN 1 on the other, so the
two VLANs leak into each other. On real switches, PVST+ also blocks the port for the
affected VLANs (`*PVID_Inc`).
</details>

---

## Ticket 2 — "PC4 can't reach anything, but PC3 is fine"

**Break it (SW1):**
```
interface GigabitEthernet0/2
 switchport trunk allowed vlan 10,99,999
```

**Reported symptom:** PC4 (VLAN 20, on SW2) can't ping its gateway `192.168.20.1`. PC3
(VLAN 10, on SW2) and PC2 (VLAN 20, on SW1) work normally.

<details>
<summary>💡 Hint</summary>

PC2 and PC4 are in the same VLAN but on different switches. What does PC4's traffic cross
that PC2's doesn't?
</details>

<details>
<summary>✅ Solution</summary>

**Diagnose:**
```
SW1# show interfaces trunk
```
`Vlans allowed on trunk` for Gig0/2 shows `10,99,999`. VLAN 20 is filtered, so PC4's frames
never reach SW1 or R1. SW2 still allows VLAN 20, which is why its own output looks fine.
Always check **both** ends.

**Fix (SW1):**
```
interface GigabitEthernet0/2
 switchport trunk allowed vlan add 20
```

**Exam tip:** `switchport trunk allowed vlan 20` *replaces* the whole list. Use
`allowed vlan add 20` to append to it. Getting this wrong takes VLANs down in production.
</details>

---

## Ticket 3 — "All of IT is down, Sales is fine"

**Break it (R1):**
```
interface GigabitEthernet0/0/0.20
 encapsulation dot1Q 21
```

**Reported symptom:** PC2 and PC4 can't ping `192.168.20.1` or anything outside VLAN 20.
They can still ping each other.

<details>
<summary>💡 Hint</summary>

The PCs can reach each other, so Layer 2 inside VLAN 20 works. The fault is where VLAN 20
meets the router.
</details>

<details>
<summary>✅ Solution</summary>

**Diagnose:**
```
R1# show running-config | begin 0/0/0.20
R1# show vlans
```
The subinterface is tagged for VLAN **21**, but the switch sends VLAN **20** frames. R1
drops frames for a VLAN it has no subinterface for. `show ip interface brief` still says
`up/up`, which is why that command alone doesn't catch this fault.

**Fix (R1):**
```
interface GigabitEthernet0/0/0.20
 encapsulation dot1Q 20
```
On some IOS versions, changing the encapsulation removes the IP address. Re-check with
`show ip interface brief` and re-apply `ip address 192.168.20.1 255.255.255.0` if needed.
</details>

---

### Troubleshooting method used in every ticket

1. **Define the scope:** who is affected and who isn't? (one PC, one VLAN, one switch)
2. **Work up the layers:** physical → access port VLAN → trunk (native/allowed) → gateway subinterface → IP.
3. **Compare both ends** of every link. Most trunk faults are mismatches.
4. **Fix, verify, document.**
