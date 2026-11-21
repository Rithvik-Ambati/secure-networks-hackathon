## Dropped traffic seen at the router (105 packets, 30 distinct src/dst/port)

- **ws** (user zone): 105 dropped packets to 30 host/port targets. Behaviour: T1046 service discovery, T1018 remote system discovery, T1021.004 SSH attempt, T1021.002 SMB attempt

| Source (zone) | Destination (zone) | Port | Dropped packets |
|---|---|---|---|
| ws (user) | db (server) | 22 | 7 |
| ws (user) | files (server) | 22 | 7 |
| ws (user) | files (server) | 445 | 7 |
| ws (user) | files (server) | 139 | 5 |
| ws (user) | app (server) | 443 | 4 |
| ws (user) | jump (mgmt) | 443 | 4 |
| ws (user) | db (server) | 443 | 4 |
| ws (user) | files (server) | 443 | 4 |
| ws (user) | app (server) | 22 | 4 |
| ws (user) | jump (mgmt) | 22 | 4 |
| ws (user) | web (dmz) | 22 | 4 |
| ws (user) | web (dmz) | 80 | 4 |
| ws (user) | db (server) | 445 | 4 |
| ws (user) | app (server) | 80 | 4 |
| ws (user) | files (server) | 80 | 4 |
