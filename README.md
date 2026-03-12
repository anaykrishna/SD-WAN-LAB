# Mini SD-WAN Lab

A functional 2-branch SD-WAN simulation built on VirtualBox VMs using pfSense, FRR, WireGuard, and a Python/Flask controller. Demonstrates real SD-WAN concepts: dual WAN links, dynamic routing, encrypted overlay tunnels, link quality monitoring, and centralized traffic steering decisions.


## Architecture

```
                        SD-WAN CONTROLLER
                        (Flask + SQLite)
                         /            \
                  metrics/              \metrics
                       /                \
Client-A  -----    pfSense-A          pfSense-B    -----  Client-B
   |                   |                   |                  |
192.168.1.x      192.168.1.10        192.168.2.10       192.168.2.x
   |                   |                   |                  |
LAN-A              WAN1  WAN2          WAN1  WAN2          LAN-B
192.168.1.0/24   10.1.1.1 10.2.2.1  10.1.1.2 10.2.2.2  192.168.2.0/24
                    |       |            |       |
                    +--ISP1-+            +-ISP1--+
                    |   10.1.1.0/30      |
                    +--ISP2-+            +-ISP2--+
                        10.2.2.0/30

WireGuard Tunnel: 172.16.0.1 (A) <=========> 172.16.0.2 (B)
OSPF: all subnets in area 0.0.0.0
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
- **OSPF routing** — dynamic route discovery and ECMP across both WAN links
- **WireGuard overlay** — encrypted tunnel between branches over the WAN links
- **Gateway monitoring** — pfSense dpinger measures RTT and packet loss per WAN link in real time
- **Branch agent** — reports WAN link metrics to the central controller every 10 seconds
- **SD-WAN controller** — scores each WAN link and decides optimal path per branch
- **Failover script** — pfSense polls controller and switches default route accordingly


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


## Repository Structure

```
sdwan-lab/
├── controller/
│   ├── controller.py       # Flask REST API + SQLite + decision logic
├── branch/
│   ├── branch_agent.py     # Measures WAN latency/loss, reports to controller
├── pfsense/
│   └── pfsense_switcher.sh # Polls controller, applies route switching on pfSense
└── README.md
```


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

### GET `/api/metrics/<branch_id>`
Returns last 40 raw metric readings for a branch.


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

## Route Switching (pfSense)

`pfsense/pfsense_switcher.sh` runs on each pfSense VM. It:

1. Calls `GET /api/decisions/<branch_id>` on the controller
2. Reads the current default route via `netstat -rn`
3. Switches the route only if the controller decision differs from current state
4. Logs every action to `/var/log/sdwan_switcher.log`

Deploy on pfSense via **Diagnostics → Edit File**, save to `/usr/local/bin/sdwan_switcher.sh`, then add to cron via **Services → Cron** (requires cron package) to run every minute.


## Project Background

Built as part of a networking lab to simulate real SD-WAN concepts learned during B.Tech — including OSPF/BGP with pfSense/FRR.
