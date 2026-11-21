# PS2 design: addressing plan, zones and flow matrix

_Generated from `policy.yaml` by `gen.py`. Edit the policy, not this file._

## Security zones and addressing plan

| Zone | Subnet | Router interface | Hosts |
|---|---|---|---|
| user | 10.10.10.0/24 | 10.10.10.254 | ws (10.10.10.10) |
| dmz | 10.10.20.0/24 | 10.10.20.254 | web (10.10.20.10) |
| server | 10.10.30.0/24 | 10.10.30.254 | app (10.10.30.10), db (10.10.30.11), files (10.10.30.12) |
| mgmt | 10.10.40.0/24 | 10.10.40.254 | jump (10.10.40.10) |

Flat (before) network: 10.10.0.0/24 with ws 10.10.0.10, web 10.10.0.20, app 10.10.0.30, db 10.10.0.31, files 10.10.0.32, jump 10.10.0.40

## Data-flow table (the only allowed traffic)

| ID | From | Zone | To | Zone | Port/proto | Rate limit | Purpose |
|---|---|---|---|---|---|---|---|
| F1 | ws | user | web | dmz | 443/tcp | - | Users reach the web portal over HTTPS |
| F2 | web | dmz | app | server | 8080/tcp | - | Web tier calls the app API |
| F3 | app | server | db | server | 5432/tcp | - | App reads and writes the database |
| F4 | app | server | files | server | 445/tcp | - | App stores documents on the file server |
| F5 | jump | mgmt | web | dmz | 22/tcp | 20/minute | Admin SSH to web |
| F6 | jump | mgmt | app | server | 22/tcp | 20/minute | Admin SSH to app |
| F7 | jump | mgmt | db | server | 22/tcp | 20/minute | Admin SSH to database |
| F8 | jump | mgmt | files | server | 22/tcp | 20/minute | Admin SSH to file server |

Everything else is dropped by default and logged (`PS2-DROP zone=...`).

## Controls

- Zones on separate Docker networks, joined only by the router container (no direct path).
- Router `forward` chain: default deny, stateful (established/related), one rule per flow.
- Management SSH rate limited at the router and on the database host.
- Host micro-segmentation on every host (second layer): each host only accepts the flows listed for it, so one wrong router rule cannot open a hole.
- Egress filtering: the database host may not start outbound connections; the router drops any server-to-user or server-to-DMZ start of a connection.
- Dropped traffic is logged per source zone and mapped to ATT&CK by `tools/droplog.py`.
