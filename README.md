# Mini SD-WAN Lab

A functional 2-branch SD-WAN simulation built on VirtualBox VMs using pfSense, FRR, WireGuard, and a Python/Flask controller. Demonstrates real SD-WAN concepts: dual WAN links, dynamic routing, encrypted overlay tunnels, link quality monitoring, and centralized traffic steering decisions.


## Architecture

```
Client-A
    |
LAN-A (192.168.1.0/24)
    |
pfSense-A (192.168.1.10)
    |           |
  WAN1        WAN2
(10.1.1.1)  (10.2.2.1)
    |           |
----ISP1------ISP2----   ← VirtualBox Internal Networks
    |           |
(10.1.1.2)  (10.2.2.2)
  WAN1        WAN2
    |           |
pfSense-B (192.168.2.10)
    |
LAN-B (192.168.2.0/24)
    |
Client-B
```

### Overlay Tunnel (WireGuard)
```
pfSense-A (172.16.0.1) ←—WireGuard—→ pfSense-B (172.16.0.2)
```


## Stack

| Component | Technology |
|---|---|
| Virtualization | VirtualBox |
| Firewall / Router | pfSense CE |
| Dynamic Routing | FRR (OSPF) |
| Overlay Tunnel | WireGuard |
| Controller | Python / Flask |
| Database | SQLite |
| Branch Agent | Python |


## Features

- **Dual WAN links per branch** — two simulated ISP paths between branches
- **OSPF routing** — dynamic route discovery and equal-cost multipath across both WAN links
- **WireGuard overlay** — encrypted tunnel between branches over the WAN links
- **Gateway monitoring** — pfSense dpinger measures RTT and packet loss per WAN link in real time
- **Branch agent** — reports WAN link metrics to the central controller every 10 seconds
- **SD-WAN controller** — scores each WAN link and decides optimal path per branch


## IP Plan

| Device | Interface | IP |
|---|---|---|
| pfSense-A | LAN | 192.168.1.10 |
| pfSense-A | WAN1 | 10.1.1.1/30 |
| pfSense-A | WAN2 | 10.2.2.1/30 |
| pfSense-A | WireGuard | 172.16.0.1/30 |
| pfSense-B | LAN | 192.168.2.10 |
| pfSense-B | WAN1 | 10.1.1.2/30 |
| pfSense-B | WAN2 | 10.2.2.2/30 |
| pfSense-B | WireGuard | 172.16.0.2/30 |


## Controller API

### POST `/api/metrics`
Branch agent posts WAN link metrics.

**Request:**
```json
{
  "branch_id": "branch-A",
  "wan1": { "latency_ms": 30, "packet_loss_pct": 2 },
  "wan2": { "latency_ms": 80, "packet_loss_pct": 5 }
}
```

**Response:**
```json
{
  "active_wan": "WAN1",
  "reason": "WAN1 score=50.0"
}
```

### GET `/api/decisions/<branch_id>`
Returns last 20 routing decisions for a branch.

```json
[
  { "active_wan": "WAN1", "reason": "WAN1 score=1.4", "ts": "2026-03-09T12:58:36" },
  { "active_wan": "WAN2", "reason": "WAN2 score=1.3 better", "ts": "2026-03-09T12:57:11" }
]
```

---

## Decision Logic

Each WAN link is scored as:

```
score = latency_ms + (packet_loss_pct × 10)
```

WAN1 is preferred unless WAN2 score is more than 20% better:

```python
if score(WAN1) <= score(WAN2) * 1.2:
    use WAN1
else:
    use WAN2
```

---

## Setup

### 1. VirtualBox Network Config

| VM | Adapter 1 | Adapter 2 | Adapter 3 | Adapter 4 |
|---|---|---|---|---|
| pfSense-A | NAT | Internal `lan_a` | Internal `isp1` | Internal `isp2` |
| pfSense-B | NAT | Internal `lan_b` | Internal `isp1` | Internal `isp2` |
| Client-A | Internal `lan_a` | — | — | — |
| Client-B | Internal `lan_b` | — | — | — |

### 2. pfSense Interface Assignment

Assign and configure static IPs as per the IP plan above. Uncheck **Block private networks** on WAN1 and WAN2.

### 3. FRR / OSPF

Install FRR package via **System → Package Manager**. Enable OSPF and add networks:

- `192.168.1.0/24` area `0.0.0.0` (pfSense-A LAN)
- `10.1.1.0/30` area `0.0.0.0`
- `10.2.2.0/30` area `0.0.0.0`

Verify with: **Services → FRR → Status** — both branches should appear as OSPF neighbors.

### 4. WireGuard

Install WireGuard package. Create tunnel on each pfSense, generate key pairs, exchange public keys, set allowed IPs. Assign tunnel interface and add firewall pass rules on WAN1 and WAN2 for UDP port `51820`.

### 5. Controller

```bash
pip install flask
python controller.py
```

### 6. Branch Agent

```bash
pip install requests
python branch_agent.py
```


## Project Background

Built as part of a networking project to simulate real SD-WAN concepts learned during B.Tech. Prior work includes OSPF/BGP labs with pfSense,  MITM attack simulation with Wireshark/hping, and DNS server administration.

