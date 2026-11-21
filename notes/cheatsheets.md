# Cheat sheets (offline)

## Wireshark display filters
- `ip.addr == 10.0.0.5`, `ip.src == x && ip.dst == y`, `tcp.port == 443`, `udp.port == 53`
- `tcp.flags.syn == 1 && tcp.flags.ack == 0` (SYN scan), `tcp.analysis.retransmission`
- `dns.qry.name contains "evil"`, `dns.flags.response == 0`, long TXT/NULL queries = tunnelling
- `http.request.method == "POST"`, `http contains "password"`, `tls.handshake.type == 1`, `tls.handshake.extensions_server_name`
- `arp.duplicate-address-detected`, `arp.opcode == 2` (spoof checks), `dhcp`, `bootp.option.dhcp == 2` (offers: rogue DHCP)
- `smb2`, `mqtt`, `icmp.type == 8`
- Statistics: Protocol Hierarchy, Conversations, Endpoints, IO Graphs. File > Export Objects > HTTP.

## tshark / tcpdump
- `tshark -r f.pcap -q -z conv,tcp` | `-z io,phs` | `-Y 'http.request' -T fields -e ip.src -e http.host -e http.request.uri`
- `tshark -r f.pcap -Y dns -T fields -e dns.qry.name | sort | uniq -c | sort -rn | head`
- `tcpdump -i eth0 -nn -w out.pcap 'port 80'` | `tcpdump -nr out.pcap 'tcp[tcpflags] & tcp-syn != 0'`

## Zeek (docker)
`docker run --rm -v "$PWD:/p" -w /p zeek/zeek zeek -C -r f.pcap`
- conn.log: ts uid id.orig_h id.orig_p id.resp_h id.resp_p proto service duration orig_bytes resp_bytes conn_state
- dns.log: query qtype_name answers rcode_name | http.log: method host uri user_agent status_code | ssl.log: server_name version cipher | notice.log, weird.log
- Read: `cat conn.log | zeek-cut id.orig_h id.resp_h id.resp_p conn_state | sort | uniq -c | sort -rn | head`
- Port scan sign: one orig_h to many resp_p with conn_state S0/REJ.

## Suricata rules
`action proto src sport -> dst dport (msg:""; flow:to_server,established; content:"x"; nocase; http.uri; pcre:""; threshold:type both, track by_src, count 5, seconds 60; classtype:; sid:1000001; rev:1;)`
- Test on pcap: `docker run --rm -v "$PWD:/p" --entrypoint suricata jasonish/suricata -r /p/f.pcap -S /p/local.rules -l /p -k none` then see `fast.log`/`eve.json`
- SYN scan rule: `alert tcp any any -> $HOME_NET any (msg:"SYN scan"; flags:S; threshold:type both, track by_src, count 20, seconds 5; sid:1000002; rev:1;)`
- ssh brute: `alert tcp any any -> any 22 (msg:"SSH brute"; flow:to_server; flags:S; threshold:type threshold, track by_src, count 5, seconds 60; sid:1000003; rev:1;)`

## nftables (default-deny)
```
nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iif lo accept
nft add rule inet filter input tcp dport {22,80,443} accept
nft add rule inet filter input icmp type echo-request limit rate 5/second accept
nft add rule inet filter input log prefix \"DROP \" counter drop
nft list ruleset
# rate limit scans/brute: tcp dport 22 ct state new meter ssh { ip saddr limit rate 5/minute } accept
```
iptables equivalent: `iptables -P INPUT DROP; iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT; iptables -A INPUT -p tcp --dport 22 -j ACCEPT; iptables -A INPUT -j LOG`
Inside Docker containers add `--cap-add NET_ADMIN`.

## Attack/test tools
- nmap: `-sS -p- -T4`, `-sV -sC`, `-A`, `--script vuln`, `-sU --top-ports 50`, `-Pn`
- hydra: `hydra -l user -P pass.txt ssh://victim -t 4` | `http-post-form "/login:u=^USER^&p=^PASS^:F=incorrect"`
- ffuf/gobuster: `gobuster dir -u http://victim -w /usr/share/wordlists/dirb/common.txt`
- sqlmap: `sqlmap -u "http://victim/?id=1" --batch --dbs`
- scapy: `sniff(offline="f.pcap")`, `send(ARP(op=2,psrc=gw,pdst=victim))`, `rdpcap`, `wrpcap`
- Harden: ssh `PasswordAuthentication no`, `PermitRootLogin no`, fail2ban-style rate limits; nginx `server_tokens off`, TLS1.2+; mosquitto `allow_anonymous false` + password_file; postgres `pg_hba.conf` scram-sha-256 + restricted `listen_addresses`.
- TLS check: `docker run --rm drwetter/testssl.sh host:443`; `ssh-audit host`; `openssl s_client -connect host:443 -tls1_2`
- WireGuard: `wg genkey | tee priv | wg pubkey`, `wg-quick up wg0`

## Docker
`docker compose up -d` | `exec -it svc bash` | `logs -f svc` | `network ls/inspect` | `docker compose down -v` | `docker run --rm -it --network host ...` (limited on Docker Desktop)
Layer 2 tasks: use Ubuntu/Kali in WSL2 or a VM, not Docker Desktop bridges.

## ATT&CK quick map
Recon T1595 | Initial Access T1190 | Credential Access T1110 (brute force) | Discovery T1046 (port scan), T1018 | Lateral T1021 | C2 T1071.004 (DNS), T1572 (tunnel) | Exfil T1048 | Impact T1498 (DoS) | Adversary-in-the-middle T1557 (ARP spoof T1557.002, rogue DHCP T1557.003)
D3FEND: Network Traffic Analysis, Inbound Traffic Filtering, Network Isolation, DNS Denylisting, Certificate Analysis.
Offline matrices: D:\hackathon_prep\refs\enterprise-attack.json and d3fend.json
